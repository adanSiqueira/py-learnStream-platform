import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import create_app

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.admin.router.require_role")
async def test_admin_action_allows_admin(mock_require):
    """ Should return success when user has admin role."""
    mock_user = AsyncMock(email="admin@example.com")
    mock_require.return_value = lambda: mock_user

    resp = client.post("/admin/admin-only")
    assert resp.status_code == 200
    assert "admin@example.com" in resp.json()["detail"]


@pytest.mark.asyncio
@patch("app.admin.router.create_direct_upload")
@patch("app.admin.router.create_draft_lesson")
@patch("app.admin.router.get_current_user")
async def test_create_upload_success(mock_user, mock_draft, mock_mux):
    """ Should create upload and draft successfully."""
    mock_user.return_value = AsyncMock(id=1)
    mock_mux.return_value = {"id": "mux_upload_123"}
    mock_draft.return_value = "lesson_abc"

    resp = client.post(
        "/admin/uploads",
        data={"course_id": "course123", "title": "Test Lesson", "description": "Desc"},
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["upload"]["id"] == "mux_upload_123"
    assert data["lesson"]["id"] == "lesson_abc"
    assert data["lesson"]["status"] == "uploading"


@pytest.mark.asyncio
@patch("app.admin.router.create_direct_upload", return_value=None)
async def test_create_upload_mux_failure(mock_mux):
    """ Should raise 500 if Mux upload creation fails."""
    resp = client.post("/admin/uploads", data={"title": "Fail"})
    assert resp.status_code == 500
    assert "Failed to create Mux upload" in resp.text
