import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient
import main

app = main.create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.auth.router.user_ops.get_by_email", return_value=None)
@patch("app.auth.router.user_ops.create_user")
@patch("app.auth.router.hash_password", return_value="hashed_pwd")
async def test_register_creates_user(mock_hash, mock_create, mock_get_email):
    """ Should register a new user when email is not registered."""
    fake_user = AsyncMock(id=1, email="test@example.com")
    mock_create.return_value = fake_user

    resp = client.post("/auth/register", json={
        "name": "Tester",
        "email": "test@example.com",
        "password": "123"
    })

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
@patch("app.auth.router.user_ops.get_by_email")
async def test_register_email_already_exists(mock_get_email):
    """ Should raise 400 if email already registered."""
    mock_get_email.return_value = AsyncMock()
    resp = client.post("/auth/register", json={
        "name": "User",
        "email": "exists@example.com",
        "password": "123"
    })
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
@patch("app.auth.router.user_ops.get_by_email")
@patch("app.auth.router.verify_password", return_value=True)
@patch("app.auth.router.create_access_token", return_value="access123")
@patch("app.auth.router.create_refresh_token", return_value="refresh123")
@patch("app.auth.router.hash_token", return_value="hashed_refresh")
@patch("app.auth.router.refresh_token_ops.save_refresh_token")
async def test_login_valid_credentials(
    mock_save, mock_hash, mock_refresh, mock_access, mock_verify, mock_get_email
):
    """ Should return tokens when login credentials are valid."""
    user = AsyncMock(id=10, email="login@example.com", password_hash="hash")
    mock_get_email.return_value = user

    resp = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "123"
    })
    data = resp.json()

    assert resp.status_code == 200
    assert "access_token" in data
    assert "refresh_token" in data
    mock_save.assert_called_once()


@pytest.mark.asyncio
@patch("app.auth.router.user_ops.get_by_email", return_value=None)
async def test_login_invalid_credentials(mock_get_email):
    """ Should return 401 for invalid login."""
    resp = client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "123"
    })
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
