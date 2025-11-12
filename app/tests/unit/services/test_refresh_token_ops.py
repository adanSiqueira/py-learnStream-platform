import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from app.models.sql.refresh_token import RefreshToken
from app.tests.conftest import FakeResult
from app.services import refresh_token_ops

@pytest.mark.asyncio
async def test_save_refresh_token_commits_and_refreshes():
    # Arrange
    db = AsyncMock()

    # Act
    await refresh_token_ops.save_refresh_token(
        db=db,
        user_id=1,
        hashed_token="abc123",
        expires_at=datetime.now()
    )

    # Assert
    # Check that add() was called with a RefreshToken instance
    db.add.assert_awaited()
    db.commit.assert_awaited()
    added_obj = db.add.await_args.args[0]
    assert isinstance(added_obj, RefreshToken)
    assert added_obj.user_id == 1
    assert added_obj.token_hash == "abc123"

    # Check that commit() was awaited
    db.commit.assert_awaited()

@pytest.mark.asyncio
async def test_get_refresh_token_queries_db():
    # Arrange
    db = AsyncMock()
    fake_row = Mock()

    # FakeResult should mimic the result of db.execute(...).scalar_one_or_none()
    fake_result = FakeResult(fake_row)
    db.execute.return_value = fake_result

    # Act
    result = await refresh_token_ops.get_refresh_token(db, user_id=10, hashed_token="h")

    # Assert
    db.execute.assert_awaited()  # ensures query was executed
    assert result is fake_row  # the function should return the fake_row
