import asyncio
import random

from app.config import DOWNSTREAM_LATENCY_MS, FAILURE_RATE
from app.metrics import metrics


class DownstreamError(Exception):
    pass


_runtime_failure_rate = FAILURE_RATE


def get_failure_rate() -> float:
    return _runtime_failure_rate


def set_failure_rate(rate: float) -> None:
    global _runtime_failure_rate
    _runtime_failure_rate = max(0.0, min(1.0, rate))


async def call_downstream() -> dict:
    await metrics.record_downstream_call()
    await asyncio.sleep(DOWNSTREAM_LATENCY_MS / 1000)

    if random.random() < _runtime_failure_rate:
        await metrics.record_downstream_failure()
        raise DownstreamError("downstream service unavailable")

    await metrics.record_downstream_success()
    return {"user_id": "u-123", "name": "Alice", "status": "ok"}
