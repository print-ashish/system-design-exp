import asyncpg
from app.config import DATABASE_URL, POOL_MIN_SIZE, POOL_MAX_SIZE

pool: asyncpg.Pool | None = None


async def init_pool():
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=POOL_MIN_SIZE,
        max_size=POOL_MAX_SIZE,
    )


async def close_pool():
    global pool
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    return pool
