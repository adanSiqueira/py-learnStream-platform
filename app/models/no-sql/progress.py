from .database import db
from datetime import datetime

progress_collection = db["progress"]

async def save_progress(user_id: str, lesson_id: str, progress: float):
    now = datetime.now()
    await progress_collection.update_one(
        {"user_id": user_id, "lesson_id": lesson_id},
        {"$set": {"progress": progress, "updated_at": now},
         "$setOnInsert": {"created_at": now}},
        upsert=True
    )