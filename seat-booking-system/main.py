from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import asyncio
import random
from database import get_db, init_db, Seat
from redis_client import acquire_lock, release_lock, redis_client
import time

app = FastAPI(title="High-Concurrency Seat Booking System (Async)")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/book-seat/{seat_id}")
async def book_seat(
    seat_id: int, 
    use_lock: bool = Query(True, description="Toggle distributed lock"),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    
    # 1. READ CACHE (Fail-Fast)
    is_booked_cache_key = f"seat_status:{seat_id}:booked"
    if await redis_client.get(is_booked_cache_key):
        await redis_client.incr("stats:cache_hits")
        raise HTTPException(status_code=400, detail="Seat is already booked (Cached)")

    lock_key = f"seat_lock:{seat_id}"
    
    if use_lock:
        if not await acquire_lock(lock_key):
            await redis_client.incr("stats:locks_prevented")
            raise HTTPException(status_code=409, detail="Seat is being booked by another user")

    try:
        # Fetch the seat
        result = await db.execute(select(Seat).filter(Seat.id == seat_id))
        seat = result.scalars().first()
        
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        
        if seat.is_booked:
            await redis_client.incr("stats:db_prevented")
            raise HTTPException(status_code=400, detail="Seat is already booked")
        
        # Simulate delay (1-2 seconds)
        delay = random.uniform(1, 2)
        await asyncio.sleep(delay)
        
        # Update seat as booked
        seat.is_booked = True
        await db.commit()
        
        # 2. UPDATE CACHE
        await redis_client.set(is_booked_cache_key, "1")
        await redis_client.incr("stats:success")
        
        # Track response time
        rt = time.time() - start_time
        await redis_client.incr("stats:total_rt", int(rt * 1000)) 
        await redis_client.incr("stats:total_requests")
        
        return {"status": "success", "message": f"Seat {seat_id} booked successfully", "delay": delay}
        
    except Exception as e:
        await db.rollback()
        raise e
    finally:
        if use_lock:
            await release_lock(lock_key)

@app.get("/seats")
async def get_seats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seat))
    return result.scalars().all()

@app.post("/reset-seats")
async def reset_seats(db: AsyncSession = Depends(get_db)):
    await db.execute(update(Seat).values(is_booked=False))
    await db.commit()
    # Reset stats and caches
    keys_to_delete = await redis_client.keys("stats:*")
    keys_to_delete += await redis_client.keys("seat_status:*")
    if keys_to_delete:
        await redis_client.delete(*keys_to_delete)
    return {"status": "success", "message": "All seats reset to available and caches cleared"}

@app.get("/stats")
async def get_stats():
    success = await redis_client.get("stats:success") or 0
    locks = await redis_client.get("stats:locks_prevented") or 0
    db_blocked = await redis_client.get("stats:db_prevented") or 0
    cache_hits = await redis_client.get("stats:cache_hits") or 0
    total_rt = await redis_client.get("stats:total_rt") or 0
    count = await redis_client.get("stats:total_requests") or 0
    
    avg_rt = int(total_rt) / int(count) if int(count) > 0 else 0
    
    return {
        "success": int(success),
        "locks_prevented": int(locks),
        "db_prevented": int(db_blocked),
        "cache_hits": int(cache_hits),
        "avg_response_time_ms": round(avg_rt, 2)
    }
