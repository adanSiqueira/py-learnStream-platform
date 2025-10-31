from datetime import datetime
from bson import ObjectId, errors
from .database import db


lessons_collection = db["lessons"]

async def create_lesson(course_id: str, title: str, description: str):
    lesson = {
        "course_id": ObjectId(course_id),
        "title": title,
        "description": description,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = await lessons_collection.insert_one(lesson)
    return str(result.inserted_id)

async def get_lesson(lesson_id: str):
    try:
        return await lessons_collection.find_one({"_id": ObjectId(lesson_id)})
    except errors.InvalidId:
        return None
    

async def list_lessons_by_course(course_id: str):
    cursor = lessons_collection.find({"course_id": ObjectId(course_id)})
    return [lesson async for lesson in cursor]

async def update_lesson(lesson_id: str, updates: dict):
    updates["updated_at"] = datetime.now()
    await lessons_collection.update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": updates}
    )

async def delete_lesson(lesson_id: str):
    await lessons_collection.delete_one({"_id": ObjectId(lesson_id)})
