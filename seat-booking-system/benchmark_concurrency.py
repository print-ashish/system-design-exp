import asyncio
import httpx
import time
from collections import Counter
try:
    from plot_results import create_linkedin_visual
except ImportError:
    create_linkedin_visual = None

BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 1000
SEAT_ID = 1

async def book_seat(client, use_lock):
    url = f"{BASE_URL}/book-seat/{SEAT_ID}?use_lock={str(use_lock).lower()}"
    try:
        response = await client.post(url, timeout=30)
        return response.status_code
    except Exception as e:
        return f"Error: {str(e)}"

async def run_experiment(use_lock):
    print(f"\n--- Running Experiment: use_lock={use_lock} ---")
    
    # Reset seats before experiment
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/reset-seats")
        
        start_time = time.time()
        tasks = [book_seat(client, use_lock) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
    
    counts = Counter(results)
    duration = end_time - start_time
    
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Total Duration: {duration:.2f} seconds")
    print(f"Requests per Second: {NUM_REQUESTS/duration:.2f}")
    print("\nResults Distribution:")
    # Fetch detailed stats from the server
    async with httpx.AsyncClient() as client:
        stats_resp = await client.get(f"{BASE_URL}/stats")
        stats = stats_resp.json()
    
    total_400s = counts.get(400, 0)
    cache_hits = stats.get('cache_hits', 0)
    db_hits_booked = stats.get('db_prevented', 0)
    
    print(f"  200 OK (Success):       {counts.get(200, 0)}")
    print(f"  409 Conflict (Locked):  {counts.get(409, 0)}")
    print(f"  400 (Stopped by Cache): {cache_hits}")
    print(f"  400 (Stopped by DB):    {db_hits_booked}")
    
    if counts.get(200, 0) > 1 and not use_lock:
        print("\n[!] RACE CONDITION OBSERVED: Multiple users successfully booked the same seat!")
    elif counts.get(200, 0) == 1:
        print("\n[✓] CONSISTENCY MAINTAINED: Only one user successfully booked the seat.")
    
    return {
        "use_lock": use_lock,
        "duration": duration,
        "success": counts.get(200, 0),
        "lock_blocked": counts.get(409, 0),
        "db_blocked": db_hits_booked,
        "cache_hits": cache_hits
    }

async def main():
    print("Starting Concurrency Benchmark...")
    
    # Run with locking
    lock_stats = await run_experiment(use_lock=True)
    
    # Run without locking
    no_lock_stats = await run_experiment(use_lock=False)
    
    print("\n" + "="*55)
    print("FINAL CONCURRENCY COMPARISON")
    print("="*55)
    print(f"{'Metric':<30} | {'With Lock':<10} | {'Without Lock':<10}")
    print("-" * 55)
    print(f"{'Seats Sold (Goal: 1)':<30} | {lock_stats['success']:<10} | {no_lock_stats['success']:<10}")
    print(f"{'Blocked by Redis (Bouncer)':<30} | {lock_stats['lock_blocked']:<10} | {no_lock_stats['lock_blocked']:<10}")
    print(f"{'Blocked by READ-CACHE':<30} | {lock_stats['cache_hits']:<10} | {no_lock_stats['cache_hits']:<10}")
    print(f"{'Blocked by DB (Judge)':<30} | {lock_stats['db_blocked']:<10} | {no_lock_stats['db_blocked']:<10}")
    print(f"{'Total Time (Lower is better)':<30} | {lock_stats['duration']:<10.2f} | {no_lock_stats['duration']:<10.2f}")
    print("="*55)

    if create_linkedin_visual:
        create_linkedin_visual(lock_stats, no_lock_stats)
    else:
        print("\n[!] Matplotlib not found. Install it to generate infographics.")

if __name__ == "__main__":
    asyncio.run(main())
