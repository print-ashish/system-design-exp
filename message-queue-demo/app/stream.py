from redis.exceptions import ResponseError

from app import jobs
from app.config import CONSUMER_GROUP, MAX_QUEUE_SIZE, STREAM_KEY
from app.redis_client import redis


async def ensure_consumer_group() -> None:
    try:
        await redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def get_queue_depth() -> int:
    return await redis.xlen(STREAM_KEY)


async def enqueue(job_id: str, image_name: str) -> tuple[bool, int]:
    depth = await get_queue_depth()
    if depth >= MAX_QUEUE_SIZE:
        await jobs.incr_metric("rejected_503")
        return False, depth

    await jobs.create_job(job_id, image_name, "queued")
    await redis.xadd(STREAM_KEY, {"job_id": job_id, "image_name": image_name})
    await jobs.incr_metric("accepted")
    return True, depth + 1


async def reset_queue() -> None:
    keys = [key async for key in redis.scan_iter("job:*")]
    if keys:
        await redis.delete(*keys)
    await redis.delete("metrics")
    await redis.delete(STREAM_KEY)
    try:
        await redis.xgroup_destroy(STREAM_KEY, CONSUMER_GROUP)
    except ResponseError:
        pass
    await ensure_consumer_group()
