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
    if not ObjectId.is_valid(course_id):
        raise ValueError("Invalid course_id")
    
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

def serialize_lesson(lesson: dict) -> dict:
    return {
        "id": str(lesson["_id"]),
        "course_id": str(lesson["course_id"]),
        "title": lesson.get("title"),
        "description": lesson.get("description"),
        "mux": lesson.get("mux", {}),
        "created_at": lesson.get("created_at"),
        "updated_at": lesson.get("updated_at"),
    }

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
    oid = ObjectId(course_id)
    cursor = lessons_collection.find({"course_id": oid})
    lessons = [lesson async for lesson in cursor]
    return [serialize_lesson(lesson) for lesson in lessons]

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

async def create_draft_lesson(
    course_id: str = None,
    title: str = "Untitled Lesson",
    description: str = "",
    upload_id: str = None,
    asset_id: str = None,
    playback_id: str = None,
    status: str = "uploading",
    upload_method: str = None
):
    """
    Create a draft lesson document in the database.

    This helper function is used by admin endpoints to create a lesson entry
    before the video is fully processed or available. It stores metadata about
    the Mux upload/asset and returns the newly created lesson ID.

    Parameters
    ----------
    course_id : str, optional
        The ID of the course this lesson belongs to. Converted to ObjectId if provided.
    title : str, optional
        The lesson title. Defaults to "Untitled Lesson".
    description : str, optional
        A text description of the lesson.
    upload_id : str, optional
        The Mux direct-upload ID (used when file is uploaded via Mux Upload API).
    asset_id : str, optional
        The Mux asset ID (used when video already exists or is created from URL).
    playback_id : str, optional
        The Mux playback ID, if available.
    status : str, optional
        Current processing status. Usually "uploading" or "processing".
        Defaults to "uploading".
    upload_method : str, optional
        Indicates how the lesson video was provided:
        - "direct_upload"
        - "from_url"
        - "existing_asset"
        or None.

    Returns
    -------
    str
        The ID of the newly created lesson document (as a string).

    Notes
    -----
    - The function inserts a minimal draft structure; additional fields like
      duration, thumbnail, manifest, etc. will be filled later once Mux processes the asset.
    - The returned lesson ID is used by the frontend/admin panel to track progress
      and eventually update the lesson when processing completes.
    """
    lesson = {
        "course_id": ObjectId(course_id) if ObjectId.is_valid(course_id) else course_id,
        "title": title,
        "description": description,
        "mux": {
            "asset_id": asset_id,
            "upload_id": upload_id,
            "playback_id": playback_id,
            "status": status,
            "duration": None,
            "thumbnail_url": None,
            "poster_url": None,
            "manifest_url": None,
            "watch_page_url": None,
            "visibility": "private",
            "upload_method": upload_method,
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    res = await lessons_collection.insert_one(lesson)
    return str(res.inserted_id)
