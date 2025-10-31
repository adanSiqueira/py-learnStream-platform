import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["py-learnstream"]

async def get_db():
    return db