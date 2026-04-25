import asyncio
import asyncpg

async def init():
    # Connect to default postgres to create the DB
    conn = await asyncpg.connect("postgresql://admin:password@localhost:5432/postgres")
    await conn.execute("DROP DATABASE IF EXISTS iot_single")
    await conn.execute("CREATE DATABASE iot_single")
    await conn.close()

    # Create table in the new DB
    conn = await asyncpg.connect("postgresql://admin:password@localhost:5432/iot_single")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id SERIAL PRIMARY KEY,
            device_id INTEGER NOT NULL,
            temperature FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Single IoT Database Initialized.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init())
