"""
This module provides a shared asynchronous Redis client
for caching and temporary data storage across services.

It's used to store short-lived signed URLs, tokens, and other
frequently accessed items to reduce database or API calls.
"""
from redis import asyncio as aioredis
from typing import Optional
from app.core.config import settings

REDIS_URL = settings.REDIS_URL

#Global Redis connection
redis: Optional[aioredis.Redis] = None

async def init_redis():
    """
    Initialize the global Redis connection. This should be called once at application startup.
    """
    global redis
    redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis

async def close_redis():
    """Close the Redis connection on app shutdown."""
    global redis
    if redis:
        await redis.close()

#Convenience wrappers
async def set_cache(key: str, value: str, ttl: int = 300):
    """Store a key/value pair in Redis with expiration time."""
    await redis.set(key, value, ex=ttl)

async def get_cache(key: str) -> Optional[str]:
    """Retrieve a value from Redis by key."""
    return await redis.get(key)
