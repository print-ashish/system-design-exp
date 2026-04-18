from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Boolean
import os

# Use postgresql+asyncpg for async support
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/seat_booking")

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=20,          # Base pool of connections
    max_overflow=30,       # Extra connections allowed during peak load
    pool_timeout=30,       # Seconds to wait for a connection from the pool
    pool_recycle=1800,     # Reset connections every 30 minutes
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    is_booked = Column(Boolean, default=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed data
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Seat))
        if len(result.scalars().all()) == 0:
            for i in range(1, 11):
                session.add(Seat(id=i, is_booked=False))
            await session.commit()
