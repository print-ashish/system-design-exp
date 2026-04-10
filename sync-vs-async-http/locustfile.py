from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Frequent requests to simulate load
    
    @task
    def test_sync(self):
        # This will hit either port 8001 (sync) or 8002 (async) 
        # based on the host provided to locust.
        self.client.get("/sync-task" if self.host.endswith("8001") else "/async-task")
