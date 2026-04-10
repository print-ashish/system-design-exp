import asyncio
import time
import asyncpg
from fastapi import APIRouter, HTTPException, status
from app.config import DATABASE_URL
from app.db import get_pool

router = APIRouter()

SIMULATED_LATENCY = 0.075  # 75 ms — mimics a real DB query


@router.get("/no-pool")
async def no_pool():
    """
    Opens a brand-new DB connection per request.
    Under high concurrency this exhausts PostgreSQL's max_connections
    and causes 'too many clients' errors.
    """
    start = time.perf_counter()
    conn = None
    try:
        # 2-second timeout so it fails fast when saturated, instead of hanging
        conn = await asyncpg.connect(DATABASE_URL, timeout=2.0)
        await asyncio.sleep(SIMULATED_LATENCY)
        result = await conn.fetchval("SELECT 1")
        return {
            "endpoint": "no-pool",
            "status": "ok",
            "result": result,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "endpoint": "no-pool",
                "status": "error",
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
    finally:
        if conn and not conn.is_closed():
            await conn.close()


@router.get("/with-pool")
async def with_pool():
    """
    Borrows a connection from the shared pool.
    Pool caps DB connections at max_size=10 regardless of HTTP concurrency.
    """
    start = time.perf_counter()
    try:
        async with get_pool().acquire() as conn:
            await asyncio.sleep(SIMULATED_LATENCY)
            result = await conn.fetchval("SELECT 1")
        return {
            "endpoint": "with-pool",
            "status": "ok",
            "result": result,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "endpoint": "with-pool",
                "status": "error",
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
