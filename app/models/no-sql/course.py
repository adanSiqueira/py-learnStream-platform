from datetime import datetime
from bson import ObjectId, errors
from .database import db

courses_collection = db["courses"]

async def create_course(title: str, description: str):
    course = {
        "title": title,
        "description": description,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = await courses_collection.insert_one(course)
    return str(result.inserted_id)

async def get_course(course_id: str):
    try:
        return await courses_collection.find_one({"_id": ObjectId(course_id)})
    except errors.InvalidId:
        return None
    

async def update_course(course_id: str, updates: dict):
    updates["updated_at"] = datetime.now()
    await courses_collection.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": updates}
    )

async def list_courses():
    cursor = courses_collection.find()
    return [course async for course in cursor]

async def delete_course(course_id: str):
    await courses_collection.delete_one({"_id": ObjectId(course_id)})
