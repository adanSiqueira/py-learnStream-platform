import pytest
from unittest.mock import patch, AsyncMock
from app.models.no_sql import database


@pytest.mark.asyncio
async def test_get_db_returns_db_instance():
    """Ensure get_db returns the shared MongoDB database instance."""
    with patch.object(database, "db", AsyncMock(name="db_mock")) as mock_db:
        result = await database.get_db()
        assert result == mock_db