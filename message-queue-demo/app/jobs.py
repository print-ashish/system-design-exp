import uuid
from datetime import datetime, timezone

from app.redis_client import redis


def new_job_id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_job(job_id: str, image_name: str, status: str) -> None:
    await redis.hset(
        f"job:{job_id}",
        mapping={
            "job_id": job_id,
            "image_name": image_name,
            "status": status,
            "created_at": _now(),
        },
    )


async def update_job_status(job_id: str, status: str) -> None:
    mapping: dict[str, str] = {"status": status}
    if status in ("done", "failed"):
        mapping["completed_at"] = _now()
    await redis.hset(f"job:{job_id}", mapping=mapping)


async def get_job(job_id: str) -> dict | None:
    data = await redis.hgetall(f"job:{job_id}")
    return data or None


async def incr_metric(key: str, amount: int = 1) -> None:
    await redis.hincrby("metrics", key, amount)


async def get_metric_counters() -> dict[str, str]:
    return await redis.hgetall("metrics")
