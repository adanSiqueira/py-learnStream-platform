import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from main import create_app
from app.auth.deps import get_current_user
from app.models.sql.database import get_db

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.lessons.router.get_lesson", new_callable=AsyncMock)
async def test_get_playback_lesson_not_found(mock_get):
    """Should raise 404 when lesson not found."""
    mock_user = MagicMock()
    mock_user.id = "user1"
    
    mock_get.return_value = None

    async def fake_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = fake_get_current_user

    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 404
    assert "Lesson not found" in resp.text or "not foud" in resp.text
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.lessons.router.get_lesson", new_callable=AsyncMock)
async def test_get_playback_missing_mux_metadata(mock_get):
    """Should raise 404 when lesson missing playback info."""
    mock_user = MagicMock()
    mock_user.id = "user1"
    
    mock_get.return_value = {"mux": {}}

    async def fake_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = fake_get_current_user

    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 404
    assert "Playback not available" in resp.text
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.lessons.router.create_signed_manifest_url", new_callable=AsyncMock)
@patch("app.lessons.router.user_ops.is_enrolled", new_callable=AsyncMock)
@patch("app.lessons.router.get_lesson", new_callable=AsyncMock)
async def test_get_playback_success(mock_get, mock_enroll, mock_signed):
    """Should return playback info if user enrolled and metadata valid."""
    mock_user = MagicMock()
    mock_user.id = "user1"
    
    mock_get.return_value = {
        "course_id": "course123",
        "mux": {
            "playback_id": "mux_123",
            "thumbnail_url": "thumb.jpg",
            "status": "ready"
        }
    }
    mock_enroll.return_value = True
    mock_signed.return_value = "https://mux.com/signed123"

    async def fake_get_current_user():
        return mock_user
    
    async def fake_get_db():
        return AsyncMock()

    app.dependency_overrides[get_current_user] = fake_get_current_user
    # Override get_db which is aliased as get_sql_db in the router
    app.dependency_overrides[get_db] = fake_get_db

    resp = client.get("/lessons/xyz/playback")
    data = resp.json()

    assert resp.status_code == 200
    assert data["playback_id"] == "mux_123"
    assert "iframe" in data["embed_iframe"]
    assert data["manifest_url"].startswith("https://mux.com/")
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.lessons.router.user_ops.is_enrolled", new_callable=AsyncMock)
@patch("app.lessons.router.get_lesson", new_callable=AsyncMock)
async def test_get_playback_user_not_enrolled(mock_get, mock_enroll):
    """Should raise 403 if user not enrolled in the course."""
    mock_user = MagicMock()
    mock_user.id = "user1"
    
    mock_get.return_value = {
        "course_id": "course123",
        "mux": {"playback_id": "mux_123"}
    }
    mock_enroll.return_value = False

    async def fake_get_current_user():
        return mock_user
    
    async def fake_get_db():
        return AsyncMock()

    app.dependency_overrides[get_current_user] = fake_get_current_user
    # Override get_db which is aliased as get_sql_db in the router
    app.dependency_overrides[get_db] = fake_get_db

    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 403
    assert "User not enrolled" in resp.text or "not enrolled" in resp.text
    
    app.dependency_overrides.clear()
