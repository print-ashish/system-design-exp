import asyncio, asyncpg, time, random

DB_URL = "postgresql://admin:password@localhost:5432/iot_single"

async def run_test():
    # 60 connections working for 1 database
    pool = await asyncpg.create_pool(DB_URL, min_size=60, max_size=60)
    print("🚀 Running Single-DB with Pool (Size 60)...")
    
    start = time.time()
    async def report(i):
        async with pool.acquire() as conn:
            # await conn.execute("SELECT pg_sleep(0.1)") # Simulate work
            await conn.execute("INSERT INTO metrics (device_id, temperature) VALUES ($1,$2)", i, 25.0)

    await asyncio.gather(*[report(i) for i in range(100000)])
    duration = time.time() - start
    print(f"✅ Single-DB Finished in: {duration:.2f} seconds")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(run_test())
