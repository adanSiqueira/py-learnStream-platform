import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId, errors
from app.models.no_sql import course


@pytest.mark.asyncio
async def test_create_course_inserts_and_returns_id():
    """Verify create_course inserts a document and returns its ID."""
    mock_insert_result = MagicMock(inserted_id=ObjectId())
    with patch.object(course, "courses_collection", AsyncMock()) as mock_collection:
        mock_collection.insert_one.return_value = mock_insert_result

        inserted_id = await course.create_course("Test Course", "A test description")

        mock_collection.insert_one.assert_awaited_once()
        assert inserted_id == str(mock_insert_result.inserted_id)


@pytest.mark.asyncio
async def test_get_course_returns_document():
    """Verify get_course fetches a document correctly."""
    fake_course = {"_id": ObjectId(), "title": "Math"}
    with patch.object(course, "courses_collection", AsyncMock()) as mock_collection:
        mock_collection.find_one.return_value = fake_course
        result = await course.get_course(str(fake_course["_id"]))
        assert result == fake_course
        mock_collection.find_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_course_invalid_id_returns_none():
    """Verify get_course handles invalid ObjectId properly."""
    with patch("app.models.no_sql.course.ObjectId", side_effect=errors.InvalidId):
        result = await course.get_course("invalid_id")
        assert result is None


@pytest.mark.asyncio
async def test_update_course_updates_fields():
    """Ensure update_course calls update_one with updated fields."""
    with patch.object(course, "courses_collection", AsyncMock()) as mock_collection:
        await course.update_course("507f1f77bcf86cd799439011", {"title": "Updated"})
        mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_courses_returns_all_courses():
    """Ensure list_courses retrieves all documents from collection."""
    fake_courses = [{"title": "C1"}, {"title": "C2"}]
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = fake_courses
    with patch.object(course, "courses_collection", AsyncMock(find=MagicMock(return_value=mock_cursor))):
        result = await course.list_courses()
        assert result == fake_courses


@pytest.mark.asyncio
async def test_delete_course_removes_document():
    """Ensure delete_course calls delete_one correctly."""
    with patch.object(course, "courses_collection", AsyncMock()) as mock_collection:
        await course.delete_course("507f1f77bcf86cd799439011")
        mock_collection.delete_one.assert_awaited_once()
