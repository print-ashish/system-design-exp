import asyncio

from app.config import PROCESSING_SECONDS


async def simulate(image_name: str = "") -> None:
    await asyncio.sleep(PROCESSING_SECONDS)
