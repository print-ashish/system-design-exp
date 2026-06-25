import asyncio
import random

from fastapi import HTTPException

from app.circuit_breaker import CircuitOpenError, circuit_breaker
from app.config import BACKOFF_BASE_SECONDS, BACKOFF_MAX_RETRIES, NAIVE_MAX_RETRIES
from app.downstream import DownstreamError, call_downstream
from app.metrics import metrics


async def fetch_profile_direct() -> dict:
    try:
        data = await call_downstream()
        await metrics.record_api_success()
        return {"strategy": "direct", "profile": data}
    except DownstreamError:
        await metrics.record_api_failure()
        raise HTTPException(
            status_code=503,
            detail={"message": "downstream failed", "strategy": "direct"},
        )


async def fetch_profile_naive() -> dict:
    last_error: DownstreamError | None = None
    for attempt in range(NAIVE_MAX_RETRIES + 1):
        try:
            data = await call_downstream()
            await metrics.record_api_success()
            return {"strategy": "naive", "profile": data, "attempts": attempt + 1}
        except DownstreamError as exc:
            last_error = exc
            if attempt < NAIVE_MAX_RETRIES:
                await metrics.record_retry()

    await metrics.record_api_failure()
    raise HTTPException(
        status_code=503,
        detail={
            "message": str(last_error),
            "strategy": "naive",
            "attempts": NAIVE_MAX_RETRIES + 1,
        },
    )


async def fetch_profile_backoff() -> dict:
    last_error: DownstreamError | None = None
    for attempt in range(BACKOFF_MAX_RETRIES + 1):
        try:
            data = await call_downstream()
            await metrics.record_api_success()
            return {"strategy": "backoff", "profile": data, "attempts": attempt + 1}
        except DownstreamError as exc:
            last_error = exc
            if attempt < BACKOFF_MAX_RETRIES:
                await metrics.record_retry()
                delay = BACKOFF_BASE_SECONDS * (2**attempt) + random.uniform(0, 0.05)
                await asyncio.sleep(delay)

    await metrics.record_api_failure()
    raise HTTPException(
        status_code=503,
        detail={
            "message": str(last_error),
            "strategy": "backoff",
            "attempts": BACKOFF_MAX_RETRIES + 1,
        },
    )


async def fetch_profile_circuit() -> dict:
    try:
        data = await circuit_breaker.call(call_downstream)
        await metrics.record_api_success()
        return {"strategy": "circuit", "profile": data}
    except CircuitOpenError:
        await metrics.record_api_failure()
        raise HTTPException(
            status_code=503,
            detail={
                "message": "circuit open — failing fast without calling downstream",
                "strategy": "circuit",
                "circuit_state": circuit_breaker.state,
            },
        )
    except DownstreamError:
        await metrics.record_api_failure()
        raise HTTPException(
            status_code=503,
            detail={
                "message": "downstream failed",
                "strategy": "circuit",
                "circuit_state": circuit_breaker.state,
            },
        )


STRATEGIES = {
    "direct": fetch_profile_direct,
    "naive": fetch_profile_naive,
    "backoff": fetch_profile_backoff,
    "circuit": fetch_profile_circuit,
}
