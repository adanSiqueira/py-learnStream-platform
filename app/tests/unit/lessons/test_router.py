import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import create_app

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.lessons.router.get_lesson")
async def test_get_playback_lesson_not_found(mock_get):
    """ Should raise 404 when lesson not found."""
    mock_get.return_value = None
    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 404
    assert "Lesson not foud" in resp.text


@pytest.mark.asyncio
@patch("app.lessons.router.get_lesson")
async def test_get_playback_missing_mux_metadata(mock_get):
    """ Should raise 404 when lesson missing playback info."""
    mock_get.return_value = {"mux": {}}
    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 404
    assert "Playback not available" in resp.text


@pytest.mark.asyncio
@patch("app.lessons.router.create_signed_manifest_url", return_value="https://mux.com/signed123")
@patch("app.lessons.router.user_ops.is_enrolled", return_value=True)
@patch("app.lessons.router.get_lesson")
@patch("app.lessons.router.get_current_user")
@patch("app.lessons.router.get_sql_db")
async def test_get_playback_success(mock_db, mock_user, mock_get, mock_enroll, mock_signed):
    """ Should return playback info if user enrolled and metadata valid."""
    mock_user.return_value = AsyncMock(id="user1")
    mock_get.return_value = {
        "course_id": "course123",
        "mux": {
            "playback_id": "mux_123",
            "thumbnail_url": "thumb.jpg",
            "status": "ready"
        }
    }

    resp = client.get("/lessons/xyz/playback")
    data = resp.json()

    assert resp.status_code == 200
    assert data["playback_id"] == "mux_123"
    assert "iframe" in data["embed_iframe"]
    assert data["manifest_url"].startswith("https://mux.com/")


@pytest.mark.asyncio
@patch("app.lessons.router.user_ops.is_enrolled", return_value=False)
@patch("app.lessons.router.get_lesson")
async def test_get_playback_user_not_enrolled(mock_get, mock_enroll):
    """ Should raise 403 if user not enrolled in the course."""
    mock_get.return_value = {
        "course_id": "course123",
        "mux": {"playback_id": "mux_123"}
    }
    resp = client.get("/lessons/abc/playback")
    assert resp.status_code == 403
    assert "User not enrolled" in resp.text
