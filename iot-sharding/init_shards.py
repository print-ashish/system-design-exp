import asyncio
import asyncpg
from database import SHARDS

async def init():
    for i, url in SHARDS.items():
        print(f"🔧 Initializing Shard {i+1}...")
        conn = await asyncpg.connect(url)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                device_id INTEGER NOT NULL,
                temperature FLOAT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.close()
    print("✅ All Shards Initialized.")

if __name__ == "__main__":
    asyncio.run(init())
