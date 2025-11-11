import pytest
from unittest.mock import AsyncMock, patch
from app.models.no_sql import progress


@pytest.mark.asyncio
async def test_save_progress_upserts_progress_record():
    """Ensure save_progress updates or inserts a progress record correctly."""
    with patch.object(progress, "progress_collection", AsyncMock()) as mock_collection:
        await progress.save_progress("user123", "lesson456", 0.7)
        mock_collection.update_one.assert_awaited_once()

        args, kwargs = mock_collection.update_one.await_args
        assert kwargs["upsert"] is True
        assert "user_id" in args[0]
        assert "lesson_id" in args[0]
