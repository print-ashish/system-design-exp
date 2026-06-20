import asyncio
import logging

from app import jobs, processor
from app.config import CONSUMER_GROUP, CONSUMER_NAME, STREAM_KEY, WORKER_CONCURRENCY
from app.redis_client import redis
from app.stream import ensure_consumer_group

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._semaphore = asyncio.Semaphore(WORKER_CONCURRENCY)

    async def start(self) -> None:
        await ensure_consumer_group()
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Background worker started (concurrency=%s)", WORKER_CONCURRENCY)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while self._running:
            try:
                messages = await redis.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_KEY: ">"},
                    count=1,
                    block=0,
                )
            except Exception:
                logger.exception("Worker read failed")
                await asyncio.sleep(0.1)
                continue

            if not messages:
                await asyncio.sleep(0.1)
                continue

            for _, entries in messages:
                for msg_id, fields in entries:
                    asyncio.create_task(self._process(msg_id, fields))

    async def _process(self, msg_id: str, fields: dict) -> None:
        async with self._semaphore:
            job_id = fields["job_id"]
            image_name = fields.get("image_name", "")
            await jobs.incr_metric("in_flight")
            try:
                await jobs.update_job_status(job_id, "processing")
                await processor.simulate(image_name)
                await jobs.update_job_status(job_id, "done")
                await jobs.incr_metric("completed")
            except Exception:
                await jobs.update_job_status(job_id, "failed")
                logger.exception("Job %s failed", job_id)
            finally:
                await jobs.incr_metric("in_flight", -1)
                await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                await redis.xdel(STREAM_KEY, msg_id)


worker = Worker()
