from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.circuit_breaker import circuit_breaker
from app.config import (
    BACKOFF_MAX_RETRIES,
    CIRCUIT_FAILURE_THRESHOLD,
    CIRCUIT_OPEN_SECONDS,
    FAILURE_RATE,
    NAIVE_MAX_RETRIES,
)
from app.downstream import get_failure_rate, set_failure_rate
from app.metrics import metrics
from app.strategies import STRATEGIES

app = FastAPI(
    title="Resilience Demo",
    description="Retry storms, exponential backoff, and circuit breakers",
)


class ConfigUpdate(BaseModel):
    failure_rate: float = Field(ge=0.0, le=1.0)


@app.get("/profile")
async def get_profile(
    strategy: str = Query(
        "direct",
        description="direct | naive | backoff | circuit",
    ),
):
    handler = STRATEGIES.get(strategy)
    if handler is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{strategy}'. Use: direct, naive, backoff, circuit",
        )

    await metrics.record_api_request()
    return await handler()


@app.get("/metrics")
async def get_metrics():
    return await metrics.snapshot(circuit_breaker.state, get_failure_rate())


@app.post("/config")
async def update_config(body: ConfigUpdate):
    set_failure_rate(body.failure_rate)
    return {"failure_rate": get_failure_rate()}


@app.post("/reset")
async def reset():
    await metrics.reset()
    circuit_breaker.reset()
    return {"status": "reset", "failure_rate": get_failure_rate()}


@app.get("/")
async def root():
    return {
        "demo": "resilience-demo",
        "strategies": list(STRATEGIES.keys()),
        "defaults": {
            "failure_rate": FAILURE_RATE,
            "naive_max_retries": NAIVE_MAX_RETRIES,
            "backoff_max_retries": BACKOFF_MAX_RETRIES,
            "circuit_failure_threshold": CIRCUIT_FAILURE_THRESHOLD,
            "circuit_open_seconds": CIRCUIT_OPEN_SECONDS,
        },
        "endpoints": {
            "profile": "/profile?strategy=naive",
            "metrics": "/metrics",
            "reset": "POST /reset",
            "config": "POST /config",
        },
    }
