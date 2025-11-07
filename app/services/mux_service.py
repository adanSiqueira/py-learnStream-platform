"""
This module encapsulates all logic related to the Mux API,
including playback URL generation, signing, and webhook handling.

It ensures caching is used to minimize redundant requests and
keeps all Mux-specific operations centralized and testable.
"""
import hmac
import base64
import hashlib
import os
import httpx
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.services.cache_service import get_cache, set_cache
from app.core.config import settings

MUX_API_BASE = "https://api.mux.com"
MUX_TOKEN_SECRET = settings.MUX_TOKEN_SECRET
MUX_TOKEN_ID = settings.MUX_TOKEN_ID

auth = (MUX_TOKEN_ID, MUX_TOKEN_SECRET)

async def create_direct_upload():
    """
    Create a direct upload object in Mux for client-side upload.
    Returns the upload object payload which includes upload_url, id, etc.
    """
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        # Create an upload object (Mux Uploads API)
        # docs: POST /video/v1/uploads
        resp = await client.post(f"{MUX_API_BASE}/video/v1/uploads", json={
            "new_asset_settings": {"playback_policy": ["public"]} 
        })
        resp.raise_for_status()
        return resp.json()["data"]
    
async def get_asset(asset_id: str) -> Dict:
    """
    Fetch asset details from Mux.
    """
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        resp = await client.get(f"{MUX_API_BASE}/video/v1/assets/{asset_id}")
        resp.raise_for_status()
        return resp.json()["data"]

async def create_signed_manifest_url(playback_id: str, user_id: str) -> str:
    """
    Generate (and cache) a signed Mux manifest URL for a playback ID.

    Args:
        playback_id (str): The Mux playback ID.
        user_id (str): The user requesting access (used in cache key).

    Returns:
        str: The signed playback manifest (.m3u8) URL.
    """
    cache_key = f"signed:{user_id}:{playback_id}"

    # Try to retrieve from cache
    cached = await get_cache(cache_key)
    if cached:
        return cached
    
    # Generate signed URL
    expires = int((datetime.now() + timedelta(minutes=5)).timestamp())
    message = f"{playback_id}:{expires}".encode()
    signature = hmac.new(MUX_TOKEN_SECRET.encode(), message, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    signed_url = f"https://stream.mux.com/{playback_id}.m3u8?token={token}&expires={expires}"

    # Cache the signed URL for 5 minutes
    await set_cache(cache_key, signed_url, ttl=300)

    return signed_url


async def handle_mux_webhook(event: dict):
    """
    Handle webhook events from Mux (e.g., asset.ready, asset.errored).
    Updates your lesson collection accordingly.
    """
    event_type = event.get("type")

    if event_type == "video.asset.ready":
        asset_id = event["data"]["id"]
        # TODO: Update MongoDB lesson.mux.status to "ready".
        pass

    elif event_type == "video.asset.errored":
        asset_id = event["data"]["id"]
        # TODO: Mark this asset as failed in MongoDB.
        pass

    return {"status": "ok", "event": event_type}
