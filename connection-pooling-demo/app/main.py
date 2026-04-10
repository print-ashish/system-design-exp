from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_pool, close_pool
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Connection Pooling Demo", lifespan=lifespan)
app.include_router(router)
