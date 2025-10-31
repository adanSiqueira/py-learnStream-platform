from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/py-learnstream"

engine = create_async_engine (DATABASE_URL, echo = True)

AsyncSessionLocal = sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session