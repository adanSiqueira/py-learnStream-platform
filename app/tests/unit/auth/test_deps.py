import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from app.auth import deps


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """ Should return a user when a valid token is decoded and user exists."""
    fake_user = AsyncMock()
    fake_user.id = 1

    # Mock decode_token and user_ops.get_by_id
    with patch("app.auth.deps.decode_token", return_value={"sub": "1"}), \
         patch("app.auth.deps.user_ops.get_by_id", return_value=fake_user):

        result = await deps.get_current_user(token="valid.jwt.token", db=AsyncMock())
        assert result == fake_user


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """ Should raise 401 if JWT is expired."""
    with patch("app.auth.deps.decode_token", side_effect=deps.jwt.ExpiredSignatureError):
        with pytest.raises(HTTPException) as exc:
            await deps.get_current_user(token="expired.jwt", db=AsyncMock())
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """ Should raise 401 if JWT is invalid."""
    with patch("app.auth.deps.decode_token", side_effect=deps.jwt.InvalidTokenError):
        with pytest.raises(HTTPException) as exc:
            await deps.get_current_user(token="invalid.jwt", db=AsyncMock())
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    """ Should raise 401 if token valid but user not found in DB."""
    with patch("app.auth.deps.decode_token", return_value={"sub": "42"}), \
         patch("app.auth.deps.user_ops.get_by_id", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await deps.get_current_user(token="jwt.ok", db=AsyncMock())
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_require_role_allows_valid_role():
    """ Should allow access if user has required role."""
    mock_user = AsyncMock()
    mock_user.role.value = "admin"

    dependency = deps.require_role(["admin"])
    result = await dependency(user=mock_user)
    assert result == mock_user


@pytest.mark.asyncio
async def test_require_role_denies_invalid_role():
    """ Should deny access if user role not in allowed list."""
    mock_user = AsyncMock()
    mock_user.role.value = "student"

    dependency = deps.require_role(["admin"])
    with pytest.raises(HTTPException) as exc:
        await dependency(user=mock_user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
