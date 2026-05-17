# PostgreSQL Database Connection
# This file is entirely separate from database/connection.py (MongoDB)
# Never import one into the other

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import os

# Read PostgreSQL URL from environment variable
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://hireiq:hireiq_password@localhost:5432/hireiq_saas")

# Create async SQLAlchemy engine
engine = create_async_engine(
    POSTGRES_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Async session dependency function for FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session generator for FastAPI dependency injection.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for backwards compatibility
get_async_session = get_db


# Function to create all tables (for testing/migrations)
async def init_db():
    """Create all tables defined in pg_models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Function to drop all tables (for testing)
async def drop_db():
    """Drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
