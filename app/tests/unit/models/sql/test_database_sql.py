import pytest
from unittest.mock import patch, AsyncMock
from app.models.sql import database

@pytest.mark.asyncio
async def test_get_db_yields_session():
    """Ensure get_db yields an AsyncSession and closes it properly."""
    fake_session = AsyncMock()
    
    with patch.object(database, "AsyncSessionLocal", return_value=fake_session):
        async for db in database.get_db():
            assert db == fake_session.__aenter__.return_value
        fake_session.__aexit__.assert_called_once()

def test_engine_and_base_configuration():
    """Verify engine and declarative base are configured correctly."""
    assert str(database.engine.url).startswith("postgresql+asyncpg")
    assert hasattr(database.Base, "metadata")
