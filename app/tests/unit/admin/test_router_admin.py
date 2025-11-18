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

# ============================================================
# NEW TESTS FOR NEW ENDPOINTS (FIXED)
# ============================================================
@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
@patch("app.admin.router.create_draft_lesson", new_callable=AsyncMock)
async def test_create_asset_from_url_success(mock_draft, mock_http_post):
    """Should create Mux asset from URL and create draft lesson."""
    mock_draft.return_value = "lesson_imported_1"

    # Mock Mux response
    mock_http_post.return_value.json = MagicMock(return_value={
        "data": {
            "id": "asset_123",
            "playback_ids": [{"id": "pb1"}],
        }
    })
    mock_http_post.return_value.raise_for_status = MagicMock()

    resp = client.post(
        "/admin/uploads/from-url",
        data={"video_url": "http://example.com/video.mp4", "title": "Imported"}
    )

    data = resp.json()
    assert resp.status_code == 200

    # asset fields
    assert data["asset"]["id"] == "asset_123"
    assert data["asset"]["playback_id"] == "pb1"

    # lesson fields
    assert data["lesson"]["id"] == "lesson_imported_1"
    # the endpoint **does not** return lesson.status anymore


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
@patch("app.admin.router.create_draft_lesson", new_callable=AsyncMock)
async def test_import_existing_mux_asset_success(mock_draft, mock_http_get):
    """Should import existing Mux asset successfully."""
    mock_draft.return_value = "lesson_existing_1"

    mock_http_get.return_value.json = MagicMock(return_value={
        "data": {"id": "asset_existing", "status": "ready"}
    })
    mock_http_get.return_value.raise_for_status = MagicMock()

    resp = client.post(
        "/admin/uploads/import-existing",
        data={"asset_id": "asset_existing", "course_id": "123"}
    )
    data = resp.json()

    assert resp.status_code == 200

    # asset fields
    assert data["asset"]["id"] == "asset_existing"
    assert data["asset"]["status"] == "ready"

    # lesson fields
    assert data["lesson"]["id"] == "lesson_existing_1"
    # the endpoint does NOT return lesson.status anymore


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_import_existing_mux_asset_not_found(mock_http_get):
    """Should return 404 when Mux asset does not exist."""
    mock_http_get.return_value.json = MagicMock(return_value={"data": {}})
    mock_http_get.return_value.raise_for_status.side_effect = Exception("404 Not Found")

    resp = client.post(
        "/admin/uploads/import-existing",
        data={"asset_id": "wrong_id", "course_id": "123"}
    )

    # router raises HTTPException(404)
    assert resp.status_code == 404
    assert "Not Found" in resp.text