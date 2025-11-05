"""
This module defines asynchronous CRUD operations for the "courses" collection 
in the MongoDB database.

Collections:
    - courses: Stores course information, including title, description, 
      and timestamps for creation and updates.
"""

from datetime import datetime
from bson import ObjectId, errors
from .database import db
import uuid

courses_collection = db["courses"]

async def create_course(title: str, description: str):
    """
    Create a new course document in the database.

    Args:
        title (str): The title of the course.
        description (str): A short description of the course content.

    Returns:
        str: The string representation of the inserted course's ObjectId.
    """
    course = {
        "course_id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = await courses_collection.insert_one(course)
    return str(result.inserted_id)

async def get_course(course_id: str):
    """
    Retrieve a single course document by its ID.

    Args:
        course_id (str): The ObjectId of the course as a string.

    Returns:
        dict | None: The course document if found, otherwise None.
    """
    try:
        return await courses_collection.find_one({"_id": ObjectId(course_id)})
    except errors.InvalidId:
        return None
    

async def update_course(course_id: str, updates: dict):
    """
    Update fields of an existing course document.

    Args:
        course_id (str): The ObjectId of the course as a string.
        updates (dict): A dictionary of fields to update.

    Returns:
        None
    """
    updates["updated_at"] = datetime.now()
    await courses_collection.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": updates}
    )

async def list_courses():
    """
    Retrieve all courses from the collection.

    Returns:
        list[dict]: A list of all course documents.
    """
    cursor = courses_collection.find()
    return [course async for course in cursor]

async def delete_course(course_id: str):
    """
    Delete a course document by its ID.

    Args:
        course_id (str): The ObjectId of the course as a string.

    Returns:
        None
    """
    await courses_collection.delete_one({"_id": ObjectId(course_id)})
