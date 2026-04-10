import time
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/sync-task")
def sync_task():
    # This is a blocking call. FastAPI handles 'def' functions in a 
    # separate threadpool to prevent blocking the main event loop.
    # However, it is still limited by the number of threads in that pool.
    time.sleep(1)
    return {"message": "Sync task finished after 1s"}

if __name__ == "__main__":
    # Running uvicorn for the sync version
    uvicorn.run(app, host="127.0.0.1", port=8001)
