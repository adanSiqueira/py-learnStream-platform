import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.database import engine, Base, AsyncSessionLocal
from app.models.sql.user import User

@pytest.mark.asyncio
async def test_sqlalchemy_integration(tmp_path):
    """Create tables in a temporary in-memory DB and insert one record."""
    # Use in-memory SQLite for a quick test
    from sqlalchemy.ext.asyncio import create_async_engine
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = AsyncSession(bind=test_engine)
    async with async_session as session:
        user = User(name="Test", email="test@test.com", password_hash="123")
        session.add(user)
        await session.commit()

        result = await session.get(User, 1)
        assert result.email == "test@test.com"
