# Connection Pooling Demo

A practical, production-style experiment demonstrating why backend systems fail under high concurrency without database connection pooling, and how a connection pool elegantly solves the problem.

## 🧠 The Core Problem

When handling web requests, opening a new PostgreSQL connection per request is incredibly expensive. At scale, this anti-pattern causes three immediate issues:
1. **Connection Overhead**: TCP handshakes and Auth add roughly 10–30ms per request.
2. **Resource Exhaustion**: PostgreSQL has a hard limit on concurrent connections (default `max_connections = 100`). Sending 200 concurrent HTTP requests will spawn 200 raw DB connections, causing immediate failures or OS-level queuing blocks.
3. **Cascading Failure**: As the database blocks incoming connections, the backend requests hang until the client load-tester times out, resulting in massive 500 API errors and disconnected clients.

With a connection pool (`max_size=10`), a fixed number of connections are kept warm. Requests borrow a connection, do work, and return it. Peak latency drops, and the DB never exceeds its connection limit.

## 🛠️ Tech Stack
- **Python / FastAPI** 
- **PostgreSQL** (running locally via Docker)
- **asyncpg** (fast Python PostgreSQL driver)
- **Locust** (for load testing)

---

## 🚀 Quick Start

### 1. Start PostgreSQL (Docker)
We use port `5436` to ensure it doesn't conflict with any local DBs you might have running.

```bash
docker run -d \
  --name postgres-pool-demo \
  -e POSTGRES_PASSWORD=pass \
  -p 5436:5432 \
  postgres:16-alpine
```

### 2. Install Dependencies
Ensure you have Python installed, then install the packages:

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI Server
Start Uvicorn to serve the API on port 8000:

```bash
python -m uvicorn app.main:app
```
*Leave this terminal running so you can observe the logs!*

### 4. Run the Load Test (Locust)
In a **new terminal window**, start Locust:

```bash
python -m locust -f locustfile.py --host http://localhost:8000
```

1. Open your browser and go to: **[http://localhost:8089](http://localhost:8089)**
2. Click **Advanced options** below the Host field.
3. In the **Endpoint** input box, enter the endpoint you want to test:
    - `/no-pool`
    - `/with-pool`
4. Enter **500** for users, **10** for ramp-up, and click **START**.

---

## 📊 What You Will Observe

### Test 1: Testing `/no-pool` (The Anti-Pattern)
* **In Locust:** As the user count climbs past ~100, the Response Time graph (especially the 95th percentile) will skyrocket. The failure rate will quickly spike as requests time out waiting for PostgreSQL.
* **In your FastAPI Terminal:** You will initially see some `200 OK`s, but very quickly you will see a massive flood of `500 Internal Server Error`s. This is because we placed a strict 2-second timeout on raw database connections—once Postgres reaches its limit, the queue stalls out and our code aggressively catches the exhaustion and fails.

### Test 2: Testing `/with-pool` (Production Ready)
* **In Locust:** Stop the previous test, hit "New Test", change the endpoint to `/with-pool`, and start again. You will see rock-solid, flat latency lines. Zero failures.
* **In your FastAPI Terminal:** A calm, steady stream of `200 OK`s. By recycling a maximum of 10 connections, your FastAPI system happily queues incoming HTTP requests momentarily in memory instead of forcing raw TCP connections onto the Database.

---

## 📂 Project Structure

- `app/config.py`: Environment setup and hardcoded database connection details.
- `app/db.py`: Establishes the reusable asyncpg connection pool logic.
- `app/routes.py`: Houses our two API endpoints (`/with-pool` and `/no-pool`). Notice the artificial 75ms sleep to mimic network/disk query latency.
- `locustfile.py`: The load-test script that creates concurrent users hammering the server.
