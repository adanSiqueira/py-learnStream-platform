import pytest
from unittest.mock import AsyncMock, Mock
from app.tests.conftest import FakeResult
from app.services import refresh_token_ops as refresh_token_service
from datetime import datetime

@pytest.mark.asyncio
async def test_save_refresh_token_commits_and_refreshes():
    db = AsyncMock()
    db.commit = AsyncMock()
    async def _fake_refresh(obj): obj.id = 123; return obj
    db.refresh = AsyncMock(side_effect=_fake_refresh)

    token = await refresh_token_service.save_refresh_token(db, 10, "h", expires_at=datetime.now())
    assert token.id == 123
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()

@pytest.mark.asyncio
async def test_get_refresh_token_queries_db():
    db = AsyncMock()
    fake_row = Mock()
    db.execute.return_value = FakeResult(fake_row)
    res = await refresh_token_service.get_refresh_token(db, 10, "h")
    assert res is fake_row
