# Resilience Demo

Compare **direct calls**, **naive retries**, **exponential backoff**, and a **circuit breaker** when calling a flaky downstream service.

**No Docker.** One command: `uvicorn app.main:app --port 8001`

Pairs with [message-queue-demo](../message-queue-demo/):
- Queue demo → fail fast when **you're full** (backpressure)
- This demo → fail fast when **dependency is sick** (circuit breaker)

## Diagrams (LinkedIn / docs)

Mermaid diagrams for the circuit breaker experiment: [diagrams/circuit-breaker.md](diagrams/circuit-breaker.md)

Export as PNG via [mermaid.live](https://mermaid.live) — use the **side by side** diagram as your single LinkedIn image.

## Quick start

```bash
cd resilience-demo
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Try manually:

```bash
curl "http://localhost:8001/profile?strategy=direct"
curl "http://localhost:8001/profile?strategy=naive"
curl http://localhost:8001/metrics
curl -X POST http://localhost:8001/reset
```

## Strategies

| Strategy | Behavior |
|----------|----------|
| `direct` | 1 downstream call, no retry |
| `naive` | Up to 6 attempts back-to-back (retry storm) |
| `backoff` | Up to 4 attempts with exponential backoff + jitter |
| `circuit` | Opens after 5 consecutive failures; fail fast while open |

## Key metric

**Amplification factor** = `downstream_calls / api_requests`

Naive retry under 50% failure rate can push this above **2×** — you multiply traffic to a sick service.

## Load tests (Locust)

```bash
locust -f locustfile.py --host http://localhost:8001
```

Use **100 users**, spawn **10**, run **2 minutes**. `POST /reset` between runs.

| Experiment | Command | What to watch |
|------------|---------|---------------|
| **1 — Retry storm** | `--strategy naive` | High `amplification_factor`, high `retries_total` |
| **2 — Backoff** | `--strategy backoff` | Lower amplification vs naive |
| **3 — Circuit breaker** | `--strategy circuit` | `circuit_state: open`, `circuit_short_circuits` climbs, downstream calls plateau |

Poll metrics during a run:

```bash
curl http://localhost:8001/metrics
```

## Config (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `FAILURE_RATE` | `0.5` | Simulated downstream failure rate |
| `DOWNSTREAM_LATENCY_MS` | `200` | Simulated downstream latency |
| `NAIVE_MAX_RETRIES` | `5` | Immediate retries after first failure |
| `BACKOFF_MAX_RETRIES` | `3` | Backoff retry count |
| `CIRCUIT_FAILURE_THRESHOLD` | `5` | Consecutive failures before circuit opens |
| `CIRCUIT_OPEN_SECONDS` | `10` | Cooldown before half-open probe |

Or tune at runtime: `POST /config` with `{"failure_rate": 0.5}`

## Interview talking points

- **Retry storm:** retries amplify load on a failing dependency
- **Backoff + jitter:** spread retries in time
- **Circuit breaker:** stop calling downstream when it's unhealthy
- **vs backpressure:** backpressure = your queue is full; circuit = their service is sick

## LinkedIn post draft

**Title:** Retry fast or amplify the crash — your service gets to choose.

I built a resilience lab: FastAPI calling a flaky downstream service (50% failure rate).

Experiment 1 — Naive retry (5 instant retries):
→ Amplification factor: ___×
→ You don't just fail — you hammer a sick dependency harder

Experiment 2 — Exponential backoff:
→ Amplification dropped to ___×
→ Better, but users still wait

Experiment 3 — Circuit breaker:
→ Circuit opened after 5 failures
→ API returned 503 instantly — zero new downstream calls
→ Fail fast when the dependency is broken, not when you're lazy

Same lesson as backpressure, different layer.

Code: [your repo link]
#SystemDesign #Backend #CircuitBreaker #Resilience #FastAPI
