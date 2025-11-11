import pytest
from unittest.mock import AsyncMock, Mock
from app.tests.conftest import FakeResult
from app.services import user_ops

@pytest.mark.asyncio
async def test_get_by_email_uses_execute_and_returns_user():
    fake_user = Mock(id=1, email="x@example.com")
    db = AsyncMock()
    db.execute.return_value = FakeResult(fake_user)

    res = await user_ops.get_by_email(db, "x@example.com")
    assert res is fake_user
    db.execute.assert_awaited()

@pytest.mark.asyncio
async def test_get_by_id_uses_execute_and_returns_user():
    fake_user = Mock(id=2, email="y@example.com")
    db = AsyncMock()
    db.execute.return_value = FakeResult(fake_user)

    res = await user_ops.get_by_id(db, 2)
    assert res is fake_user
    db.execute.assert_awaited()

@pytest.mark.asyncio
@pytest.mark.parametrize("exec_return, expected", [
    (Mock(), True),
    (None, False),
])
async def test_is_enrolled_various(exec_return, expected):
    db = AsyncMock()
    db.execute.return_value = FakeResult(exec_return)
    assert await user_ops.is_enrolled(db, 1, "course-1") is expected
