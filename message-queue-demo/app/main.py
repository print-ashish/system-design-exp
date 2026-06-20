import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import jobs, processor, stream
from app.config import MAX_QUEUE_SIZE, PROCESSING_SECONDS, WORKER_CONCURRENCY
from app.worker import worker

logging.basicConfig(level=logging.INFO)


class JobRequest(BaseModel):
    image_name: str = "photo.jpg"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await worker.start()
    yield
    await worker.stop()


app = FastAPI(
    title="Message Queue Demo",
    description="Sync vs async job processing with in-memory Redis Streams",
    lifespan=lifespan,
)


@app.post("/jobs/sync")
async def submit_sync(body: JobRequest):
    job_id = jobs.new_job_id()
    await jobs.create_job(job_id, body.image_name, "processing")
    await processor.simulate(body.image_name)
    await jobs.update_job_status(job_id, "done")
    return {"job_id": job_id, "status": "done", "mode": "sync"}


@app.post("/jobs/async", status_code=202)
async def submit_async(body: JobRequest):
    job_id = jobs.new_job_id()
    accepted, depth = await stream.enqueue(job_id, body.image_name)
    if not accepted:
        raise HTTPException(
            status_code=503,
            detail={"message": "Queue full, try again later", "queue_depth": depth},
        )
    return {"job_id": job_id, "status": "queued", "mode": "async"}


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = await jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/metrics")
async def get_metrics():
    counters = await jobs.get_metric_counters()
    queue_depth = await stream.get_queue_depth()
    return {
        "queue_depth": queue_depth,
        "max_queue_size": MAX_QUEUE_SIZE,
        "worker_concurrency": WORKER_CONCURRENCY,
        "processing_seconds": PROCESSING_SECONDS,
        "accepted": int(counters.get("accepted", 0)),
        "rejected_503": int(counters.get("rejected_503", 0)),
        "completed": int(counters.get("completed", 0)),
        "in_flight": max(0, int(counters.get("in_flight", 0))),
    }


@app.post("/reset")
async def reset():
    await stream.reset_queue()
    return {"status": "reset"}
