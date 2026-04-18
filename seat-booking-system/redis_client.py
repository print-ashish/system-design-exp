import redis.asyncio as redis
import time
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

# Async Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def acquire_lock(lock_key: str, timeout: int = 5):
    """
    Acquire a distributed lock using Redis (Async).
    """
    lock_value = str(time.time())
    result = await redis_client.set(lock_key, lock_value, nx=True, ex=timeout)
    return result if result else None

async def release_lock(lock_key: str):
    """
    Release a distributed lock (Async).
    """
    await redis_client.delete(lock_key)
