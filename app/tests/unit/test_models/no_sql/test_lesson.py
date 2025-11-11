import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId, errors
from app.models.no_sql import lesson


@pytest.mark.asyncio
async def test_create_lesson_inserts_and_returns_id():
    """Verify create_lesson inserts a document and returns its ObjectId as str."""
    mock_result = MagicMock(inserted_id=ObjectId())
    with patch.object(lesson, "lessons_collection", AsyncMock()) as mock_collection:
        mock_collection.insert_one.return_value = mock_result
        result = await lesson.create_lesson("507f1f77bcf86cd799439011", "Title", "Desc", {})
        assert result == str(mock_result.inserted_id)
        mock_collection.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_lesson_returns_document():
    """Verify get_lesson returns a document if found."""
    fake_lesson = {"_id": ObjectId(), "title": "Lesson 1"}
    with patch.object(lesson, "lessons_collection", AsyncMock()) as mock_collection:
        mock_collection.find_one.return_value = fake_lesson
        result = await lesson.get_lesson(str(fake_lesson["_id"]))
        assert result == fake_lesson


@pytest.mark.asyncio
async def test_get_lesson_invalid_id_returns_none():
    """Verify get_lesson returns None when ObjectId is invalid."""
    with patch("app.models.no_sql.lesson.ObjectId", side_effect=errors.InvalidId):
        result = await lesson.get_lesson("invalid_id")
        assert result is None


@pytest.mark.asyncio
async def test_list_lessons_by_course_returns_list():
    """Ensure list_lessons_by_course returns lessons for given course."""
    fake_lessons = [{"title": "L1"}, {"title": "L2"}]
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = fake_lessons
    with patch.object(lesson, "lessons_collection", AsyncMock(find=MagicMock(return_value=mock_cursor))):
        result = await lesson.list_lessons_by_course("507f1f77bcf86cd799439011")
        assert result == fake_lessons


@pytest.mark.asyncio
async def test_update_lesson_calls_update_one():
    """Ensure update_lesson updates a document properly."""
    with patch.object(lesson, "lessons_collection", AsyncMock()) as mock_collection:
        await lesson.update_lesson("507f1f77bcf86cd799439011", {"title": "Updated"})
        mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_lesson_calls_delete_one():
    """Ensure delete_lesson removes document properly."""
    with patch.object(lesson, "lessons_collection", AsyncMock()) as mock_collection:
        await lesson.delete_lesson("507f1f77bcf86cd799439011")
        mock_collection.delete_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_draft_lesson_inserts_and_returns_id():
    """Ensure create_draft_lesson inserts and returns ID."""
    mock_result = MagicMock(inserted_id=ObjectId())
    with patch.object(lesson, "lessons_collection", AsyncMock()) as mock_collection:
        mock_collection.insert_one.return_value = mock_result
        result = await lesson.create_draft_lesson("507f1f77bcf86cd799439011", "T", "D", "upload123")
        assert result == str(mock_result.inserted_id)
        mock_collection.insert_one.assert_awaited_once()
