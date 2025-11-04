"""
This module defines the asynchronous database configuration and session management layer 
for the SQL-based models of the application.

It sets up:
- The SQLAlchemy Declarative Base for ORM model definitions.
- The asynchronous database engine using 'create_async_engine'.
- The session factory ('AsyncSessionLocal') for managing database sessions.
- The dependency 'get_db()' for providing scoped sessions to FastAPI routes and services.

Database Engine:
    PostgreSQL with AsyncPG driver ('postgresql+asyncpg')
"""

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/py-learnstream"

# Asynchronous database engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Factory for async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """
    Provides an asynchronous database session for request-scoped operations.

    This function is used as a dependency in FastAPI routes or services.
    It ensures proper session lifecycle management by automatically closing
    the session after the request is complete.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous session instance.
    """
    async with AsyncSessionLocal() as session:
        yield session
