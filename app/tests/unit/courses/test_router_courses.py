import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import create_app

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.courses.router.list_courses")
async def test_get_all_courses_returns_list(mock_list):
    """ Should return formatted list of courses."""
    mock_list.return_value = [
        {"_id": "1", "title": "Course 1", "description": "Desc", "created_at": "now", "updated_at": "now"}
    ]
    resp = client.get("/courses/")
    data = resp.json()

    assert resp.status_code == 200
    assert isinstance(data, list)
    assert data[0]["title"] == "Course 1"


@pytest.mark.asyncio
@patch("app.courses.router.get_course")
async def test_get_course_by_id_found(mock_get):
    """ Should return details if course exists."""
    mock_get.return_value = {"_id": "1", "title": "Course A", "description": "Desc"}
    resp = client.get("/courses/1")
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] == "1"
    assert "Course A" in data["title"]


@pytest.mark.asyncio
@patch("app.courses.router.get_course", return_value=None)
async def test_get_course_by_id_not_found(mock_get):
    """ Should return 404 if course not found."""
    resp = client.get("/courses/nonexistent")
    assert resp.status_code == 404
    assert "Course not found" in resp.text
