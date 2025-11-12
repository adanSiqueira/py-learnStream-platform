import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from main import create_app
from app.auth.deps import get_current_user
from app.models.sql.user import UserRole

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
async def test_admin_action_allows_admin():
    """Should return success when user has admin role."""
    mock_user = MagicMock()
    mock_user.email = "admin@example.com"
    mock_role = MagicMock()
    mock_role.value = "admin"
    mock_user.role = mock_role
    
    async def fake_get_current_user():
        return mock_user
    
    # Override get_current_user which is used by require_role
    app.dependency_overrides[get_current_user] = fake_get_current_user

    resp = client.post("/admin/admin-only")
    assert resp.status_code == 200
    assert "admin@example.com" in resp.json()["detail"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.admin.router.create_draft_lesson", new_callable=AsyncMock)
@patch("app.admin.router.create_direct_upload", new_callable=AsyncMock)
async def test_create_upload_success(mock_mux, mock_draft):
    """Should create upload and draft successfully."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_role = MagicMock()
    mock_role.value = "admin"
    mock_user.role = mock_role
    
    mock_mux.return_value = {"id": "mux_upload_123"}
    mock_draft.return_value = "lesson_abc"

    async def fake_get_current_user():
        return mock_user

    # Override get_current_user which is used by require_role
    app.dependency_overrides[get_current_user] = fake_get_current_user

    resp = client.post(
        "/admin/uploads",
        data={"course_id": "course123", "title": "Test Lesson", "description": "Desc"},
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["upload"]["id"] == "mux_upload_123"
    assert data["lesson"]["id"] == "lesson_abc"
    assert data["lesson"]["status"] == "uploading"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.admin.router.create_direct_upload", new_callable=AsyncMock)
async def test_create_upload_mux_failure(mock_mux):
    """Should raise 500 if Mux upload creation fails."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_role = MagicMock()
    mock_role.value = "admin"
    mock_user.role = mock_role
    
    mock_mux.return_value = None  # simulate failure

    async def fake_get_current_user():
        return mock_user

    # Override get_current_user which is used by require_role
    app.dependency_overrides[get_current_user] = fake_get_current_user

    resp = client.post("/admin/uploads", data={"title": "Fail"})
    assert resp.status_code == 500
    assert "Failed to create Mux upload" in resp.text
    
    app.dependency_overrides.clear()
