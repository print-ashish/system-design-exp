import asyncio, asyncpg, time, random
from database import SHARDS

async def run_test():
    # Create 3 pools (20 connections each = 60 total)
    pools = {i: await asyncpg.create_pool(url, min_size=20, max_size=20) for i, url in SHARDS.items()}
    print("🚀 Running 3-Shard System (Total Pool Size 60)...")

    start = time.time()
    async def report(device_id):
        shard_idx = device_id % 3
        async with pools[shard_idx].acquire() as conn:
            # await conn.execute("SELECT pg_sleep(0.1)")
            await conn.execute("INSERT INTO metrics (device_id, temperature) VALUES ($1,$2)", device_id, 25.0)

    await asyncio.gather(*[report(i) for i in range(100000)])
    duration = time.time() - start
    print(f"✅ 3-Shard System Finished in: {duration:.2f} seconds")
    
    for p in pools.values(): await p.close()

if __name__ == "__main__":
    asyncio.run(run_test())
