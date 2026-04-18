from locust import HttpUser, task, between
import random

class SeatBookingUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def book_seat(self):
        # Experiment 1: With lock
        use_lock = True 
        url = f"/book-seat/1?use_lock={str(use_lock).lower()}"
        
        with self.client.post(url, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 409:
                # Expected: Seat is being booked by someone else
                response.success()
            elif response.status_code == 400:
                # Expected: Seat is already booked
                response.success()
            else:
                # Actual failures (e.g., 500 Internal Server Error)
                response.failure(f"Unexpected status code: {response.status_code}")

    def on_start(self):
        # Optional: reset seats before starting
        pass
