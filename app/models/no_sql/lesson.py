"""
This module defines asynchronous CRUD operations for the "lessons" collection 
in the MongoDB database.

Collections:
    - lessons: Stores lessons associated with specific courses, 
      including title, description, and timestamps.

Dependencies:
    - Requires an active MongoDB connection via the `db` instance from `database.py`.
    - Each lesson references a `course_id` linking it to the parent course.
"""

from datetime import datetime
from bson import ObjectId, errors
from .database import db

# Reference to the "lessons" collection in MongoDB.
lessons_collection = db["lessons"]

async def create_lesson(course_id: str, title: str, description: str, mux: dict) -> str:
    """
    Create a new lesson document linked to a specific course.

    Args:
        course_id (str): The ObjectId of the associated course as a string.
        title (str): The title of the lesson.
        description (str): A short description of the lesson content.

    Returns:
        str: The string representation of the inserted lesson's ObjectId.
    """
    lesson = {
        "course_id": ObjectId(course_id),
        "title": title,
        "description": description,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "mux": {
            "asset_id": str,
            "playback_id": str,
            "status": str,
            "duration": float | None,
            "thumbnail_url": str | None,
            "poster_url": str | None,
            "manifest_url": str | None,
            "watch_page_url": str | None,
            "visibility": str,        
            "upload_method": str | None
            }
        }
    result = await lessons_collection.insert_one(lesson)
    return str(result.inserted_id)

async def get_lesson(lesson_id: str) -> dict | None:
    """
    Retrieve a single lesson document by its ID.

    Args:
        lesson_id (str): The ObjectId of the lesson as a string.

    Returns:
        dict | None: The lesson document if found, otherwise None.
    """
    try:
        return await lessons_collection.find_one({"_id": ObjectId(lesson_id)})
    except errors.InvalidId:
        return None

async def list_lessons_by_course(course_id: str) -> list[dict]:
    """
    List all lessons associated with a specific course.

    Args:
        course_id (str): The ObjectId of the course as a string.

    Returns:
        list[dict]: A list of lesson documents related to the given course.
    """
    cursor = lessons_collection.find({"course_id": ObjectId(course_id)})
    return [lesson async for lesson in cursor]

async def update_lesson(lesson_id: str, updates: dict) -> None:
    """
    Update fields of an existing lesson document.

    Args:
        lesson_id (str): The ObjectId of the lesson as a string.
        updates (dict): A dictionary of fields to update.

    Returns:
        None
    """
    updates["updated_at"] = datetime.now()
    await lessons_collection.update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": updates},
    )

async def delete_lesson(lesson_id: str) -> None:
    """
    Delete a lesson document by its ID.

    Args:
        lesson_id (str): The ObjectId of the lesson as a string.

    Returns:
        None
    """
    await lessons_collection.delete_one({"_id": ObjectId(lesson_id)})

async def create_draft_lesson(course_id: str, title: str, description: str, upload_id: str = None):
    lesson = {
        "course_id": ObjectId(course_id) if course_id else None,
        "title": title,
        "description": description,
        "mux": {
            "upload_id": upload_id,
            "status": "uploading"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    res = await lessons_collection.insert_one(lesson)
    return str(res.inserted_id)