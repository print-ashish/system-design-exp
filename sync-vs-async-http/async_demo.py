import asyncio
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/async-task")
async def async_task():
    # This is a non-blocking call. The event loop can handle thousands
    # of concurrent connections while this waits.
    await asyncio.sleep(1)
    return {"message": "Async task finished after 1s"}

if __name__ == "__main__":
    # Running uvicorn for the async version
    uvicorn.run(app, host="127.0.0.1", port=8002)
