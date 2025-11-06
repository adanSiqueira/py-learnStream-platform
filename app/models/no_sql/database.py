"""
This module initializes and provides access to the MongoDB NoSQL database using Motor,
an asynchronous Python driver for MongoDB.

It establishes a single shared connection client for the application and exposes
a dependency-compatible functio for use in FastAPI routes and services.

Environment Variables:
    - MONGO_URL: The MongoDB connection URI
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

MONGO_URL = settings.MONGO_URL
client = AsyncIOMotorClient(MONGO_URL)
db = client["py-learnstream"]

async def get_db():
    return db