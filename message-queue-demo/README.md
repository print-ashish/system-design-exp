# Message Queue Demo

Hands-on lab comparing **sync** vs **async job processing** with **in-memory Redis Streams** (no Docker). Submit image "processing" jobs via FastAPI, load-test with Locust, and observe backpressure when the queue is full.

## The problem

When every HTTP request waits 3 seconds for "processing" inline, concurrency collapses under load. Async handoff enqueues work and returns `202 Accepted` immediately; background workers drain the queue at a fixed rate.

## Architecture

```
Client (Locust)
    │
    ├─ POST /jobs/sync  ──► await 3s processing ──► 200
    │
    └─ POST /jobs/async ──► XADD Redis Stream ──► 202
                                    │
                            Background worker (4 slots)
                                    │
                            status hash: queued → processing → done
```

**Stack:** FastAPI, fakeredis (in-memory Redis), Redis Streams, Locust.

**No Docker.** One process runs the API + broker + worker.

## Quick start

```bash
cd message-queue-demo
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Try it manually:

```bash
curl -X POST http://localhost:8000/jobs/async -H "Content-Type: application/json" -d "{\"image_name\":\"photo.jpg\"}"
curl http://localhost:8000/metrics
curl http://localhost:8000/jobs/<job_id>
curl -X POST http://localhost:8000/reset
```

## Load tests (Locust)

In a second terminal:

```bash
pip install locust
locust -f locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 — use **100 users**, spawn rate **10**, run **2 minutes**.

Between experiments: `curl -X POST http://localhost:8000/reset`

| Experiment | Locust command | What to watch |
|------------|----------------|---------------|
| **1 — Sync** | `--mode sync` | p95 latency in seconds, low RPS |
| **2 — Async** | `--mode async` | p95 ~ms, all 202; `/metrics` queue_depth spikes |
| **3 — Backpressure** | Set `MAX_QUEUE_SIZE=50`, restart server, `--mode async-backpressure` | mix of 202 + 503; queue_depth capped |

### Experiment 3 setup (Windows PowerShell)

```powershell
$env:MAX_QUEUE_SIZE="50"
uvicorn app.main:app --port 8000
```

```bash
locust -f locustfile.py --host http://localhost:8000 --mode async-backpressure
```

## Config (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCESSING_SECONDS` | `3` | Simulated image processing time |
| `MAX_QUEUE_SIZE` | `100` | Max stream length before 503 |
| `WORKER_CONCURRENCY` | `4` | Parallel background jobs |

## API

| Endpoint | Description |
|----------|-------------|
| `POST /jobs/sync` | Process inline, return when done |
| `POST /jobs/async` | Enqueue, return `202` |
| `GET /jobs/{id}` | Poll job status |
| `GET /metrics` | Queue depth, accepted, rejected, completed |
| `POST /reset` | Clear queue and counters |

## Key takeaways

1. **Queues decouple, they don't add capacity** — total work is the same; users stop waiting on the HTTP thread.
2. **Fixed workers = fixed drain rate** — 4 workers × 3s ≈ 1.3 jobs/s max throughput.
3. **Backpressure** — return `503` when full instead of accepting unbounded work.

## Interview talking points

- Sync vs async job handoff
- Redis Streams (`XADD`, consumer groups, `XACK`) vs RabbitMQ vs Kafka
- Backpressure and explicit rejection vs silent degradation
- At-least-once delivery → need idempotency in production

## LinkedIn post draft

```
I built a hands-on system design lab: sync vs async job processing with Redis Streams.

Setup: FastAPI + in-memory Redis (no Docker) + Locust — 100 concurrent users

Experiment 1 — Sync API
→ p95 latency: ___s | throughput: ___ RPS
→ Every user waits 3s inline

Experiment 2 — Async + 4 background workers
→ API p95: ___ms (202 Accepted)
→ Queue absorbed the spike; workers drained at ~1.3 jobs/s

Experiment 3 — Backpressure (max queue = 50)
→ API returned 503 when full
→ System stayed responsive under overload

Takeaway: Message queues don't add capacity — they decouple producers from consumers. Backpressure tells clients when to retry.

Code: [your repo link]
#SystemDesign #Backend #Redis #FastAPI #SoftwareEngineering
```
