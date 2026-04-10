# Sync vs Async HTTP Benchmark with FastAPI

This project demonstrates the performance difference between synchronous (`def`) and asynchronous (`async def`) endpoints in FastAPI using [Locust](https://locust.io/) for load testing.

## Files
- `sync_demo.py`: FastAPI server with a synchronous endpoint (`time.sleep(1)`).
- `async_demo.py`: FastAPI server with an asynchronous endpoint (`await asyncio.sleep(1)`).
- `locustfile.py`: Locust configuration to benchmark the endpoints.

## Setup
Ensure you have the required dependencies installed:
```bash
pip install fastapi uvicorn locust httpx requests
```

## Running the Benchmark

### 1. Synchronous Test
1. Start the sync server:
   ```bash
   python sync_demo.py
   ```
2. Start Locust pointing to the sync server:
   ```bash
   python -m locust -f locustfile.py --host http://127.0.0.1:8001
   ```
3. Open `http://localhost:8089` in your browser.
4. Set **Number of users** to 100 and **Spawn rate** to 10.
5. Click **Start swarming** and observe the RPS in the "Charts" tab.

### 2. Asynchronous Test
1. Stop the sync server and locust.
2. Start the async server:
   ```bash
   python async_demo.py
   ```
3. Start Locust pointing to the async server:
   ```bash
   python -m locust -f locustfile.py --host http://127.0.0.1:8002
   ```
4. Repeat the test steps in the browser.

## The Difference

| Metric | Synchronous (`def`) | Asynchronous (`async def`) |
| :--- | :--- | :--- |
| **Execution** | Runs in a threadpool. | Runs on the Event Loop. |
| **Blocking** | `time.sleep` blocks the thread. | `await asyncio.sleep` yields the loop. |
| **Throughput** | Limited by the threadpool size (~40-100 RPS). | High concurrency (thousands of RPS). |
| **Latency** | Spikes when threads are exhausted. | Stays flat even under load. |
