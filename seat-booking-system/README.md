# High-Concurrency Seat Booking System

This project demonstrates a distributed locking mechanism using Redis to prevent race conditions in a seat booking scenario.

## Requirements
- Docker and Docker Compose
- Python 3.8+

## Setup
1. **Infrastructure**: Start PostgreSQL and Redis using Docker.
   ```bash
   docker-compose up -d
   ```

2. **Backend**: Install dependencies and run the FastAPI server.
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Performance Testing**: Run Locust to simulate concurrent users.
   ```bash
   locust -f locustfile.py --host http://localhost:8000
   ```

## Experiments

### Experiment 1: With Redis Lock (Default)
In `locustfile.py`, ensure `use_lock = True`. Run the test.
**Expected**: Only one user successfully books the seat. Others get "Seat is being booked" (Redis lock) or "Seat is already booked" (DB validation).

### Experiment 2: Without Redis Lock
In `locustfile.py`, set `use_lock = False`. Reset the seats using `POST /reset-seats`. Run the test.
**Expected**: Multiple users might pass the initial check before the transaction commits, potentially causing issues (though Postgres transactions help, the 2s delay makes the race condition visible).

## API Endpoints
- `POST /book-seat/{seat_id}?use_lock=true`: Book a seat with optional locking.
- `GET /seats`: List all seats.
- `POST /reset-seats`: Reset all seats to available.
