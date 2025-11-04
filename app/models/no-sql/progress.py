"""
This module defines operations for tracking and updating user lesson progress 
in the MongoDB "progress" collection.

Each record links a user to a lesson, storing the percentage of completion 
and timestamps for creation and updates.

Collections:
    - progress: Stores users' learning progress for individual lessons.
"""

from .database import db
from datetime import datetime

# Reference to the "progress" collection in MongoDB.
progress_collection = db["progress"]

async def save_progress(user_id: str, lesson_id: str, progress: float) -> None:
    """
    Insert or update a user's progress for a specific lesson.

    Args:
        user_id (str): The unique identifier of the user.
        lesson_id (str): The unique identifier of the lesson.
        progress (float): The completion percentage (0.0 to 1.0).

    Returns:
        None

    Notes:
        - If a progress record for the (user_id, lesson_id) pair exists, 
          it updates the 'progress' and 'updated_at' fields.
        - If it does not exist, a new document is inserted with 'created_at'.
        - The 'upsert=True' flag ensures idempotent behavior.
    """
    now = datetime.now()
    await progress_collection.update_one(
        {"user_id": user_id, "lesson_id": lesson_id},
        {
            "$set": {"progress": progress, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
