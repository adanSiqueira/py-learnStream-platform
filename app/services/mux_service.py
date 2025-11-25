"""
This module encapsulates all logic related to the Mux API,
including playback URL generation, signing, and webhook handling.

It ensures caching is used to minimize redundant requests and
keeps all Mux-specific operations centralized and testable.
"""
import hmac
import base64
import hashlib
import logging
import httpx
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Dict
from datetime import datetime, timedelta
from app.services.cache_service import get_cache, set_cache
from app.core.config import settings

MUX_API_BASE = "https://api.mux.com"
MUX_TOKEN_SECRET = settings.MUX_TOKEN_SECRET
MUX_TOKEN_ID = settings.MUX_TOKEN_ID
MUX_WEBHOOK_SECRET = settings.MUX_WEBHOOK_SECRET

auth = (MUX_TOKEN_ID, MUX_TOKEN_SECRET)
logger = logging.getLogger(__name__)

async def create_direct_upload():
    """
    Create a direct upload object in Mux for client-side upload.
    Returns the upload object payload which includes upload_url, id, etc.
    """
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        # Create an upload object (Mux Uploads API)
        # docs: POST /video/v1/uploads
        try:
            resp = await client.post(f"{MUX_API_BASE}/video/v1/uploads", json={
                "new_asset_settings": {"playback_policy": ["public"]} 
            })
            resp.raise_for_status()
            return resp.json()["data"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to create Mux direct upload: {e}")
            raise
    
async def get_asset(asset_id: str) -> Dict:
    """
    Fetch asset details from Mux.
    """
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        try:    
            resp = await client.get(f"{MUX_API_BASE}/video/v1/assets/{asset_id}")
            resp.raise_for_status()
            return resp.json()["data"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Mux asset {asset_id}: {e}")
            raise

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
    try:
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
    except Exception as e:
        logger.error(f"Error generating signed Mux URL: {e}")
        raise


async def handle_mux_webhook(event: dict, lessons_collection: AsyncIOMotorCollection):
    """
    Handle webhook events from Mux (e.g., asset.ready, asset.errored).
    Updates your lesson collection accordingly.
    """
    event_type = event.get("type")
    data = event.get("data", {})

    logger.info(f" Received Mux webhook: {event_type}")

    now = datetime.now()

    # Handle event types
    try: 
        if event_type == "video.asset.ready":
            asset_id = data.get("id")
            upload_id = data.get("upload_id")
            playback_id = None
            if isinstance(data.get("playback_ids"), list) and data["playback_ids"]:
                playback_id = data["playback_ids"][0].get("id")

            updates = {
                "mux.asset_id": asset_id,
                "mux.playback_id": playback_id,
                "mux.duration": data.get("duration"),
                "mux.status": "ready",
                "mux.updated_at": now,
            }

            # Prefer match by upload_id, fallback to asset_id
            query = {"mux.upload_id": upload_id} if upload_id else {"mux.asset_id": asset_id}

            result = await lessons_collection.update_one(query, {"$set": updates}, upsert=True)
            logger.info(f" Asset ready updated (matched={result.matched_count}, upserted={result.upserted_id})")
            return {"status": "ok", "event": event_type}

        elif event_type == "video.asset.errored":
            asset_id = data.get("id")
            error_msg = data.get("errors", [{}])[0].get("message", "Unknown error")
            await lessons_collection.update_one(
                {"mux.asset_id": asset_id},
                {"$set": {
                    "mux.status": "errored",
                    "mux.error_message": error_msg,
                    "mux.updated_at": now,
                }}
            )
            logger.error(f" Asset errored: {asset_id} - {error_msg}")
            return {"status": "errored-handled"}

        else:
            # Log but ignore other event types
            await lessons_collection.database["webhook_logs"].insert_one({
                "received_at": now,
                "event_type": event_type,
                "payload": event,
            })
            logger.info(f" Ignored Mux event: {event_type}")
            return {"status": "ignored", "event": event_type}
    except Exception as e:
        logger.error(f"Error handling Mux webhook event {event_type}: {e}")
        raise
    
# Signature verification helper
def verify_mux_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verify Mux webhook signature.

    Correct Mux algorithm:
        signed_message = f"{timestamp}.{raw_body}"
        signature = HMAC_SHA256(secret, signed_message)
    """
    logger.info("─── Verifying Mux Signature ─────────────────────")

    if not signature_header:
        logger.error("Missing signature header.")
        return False

    # Example header:
    # t=1700000000,v1=abcd1234...
    parts = signature_header.split(",")
    timestamp = None
    signatures = []

    for part in parts:
        part = part.strip()
        if part.startswith("t="):
            timestamp = part.split("=", 1)[1]
        elif part.startswith("v1="):
            signatures.append(part.split("=", 1)[1])

    if not timestamp:
        logger.error("Missing timestamp in signature header.")
        return False

    if not signatures:
        logger.error("No v1 signatures found.")
        return False

    # Build signed message EXACTLY as Mux expects
    signed_message = f"{timestamp}.".encode() + raw_body

    # Compute expected signature
    expected = hmac.new(
        MUX_WEBHOOK_SECRET.encode(),
        signed_message,
        hashlib.sha256
    ).hexdigest()

    # Debug logs
    logger.info(f"Header timestamp: {timestamp}")
    logger.info(f"Incoming signatures: {signatures}")
    logger.info(f"Computed HMAC: {expected}")
    logger.info(f"Signed message (first 300 bytes): {signed_message[:300]}")

    # Compare against all v1 signatures
    for sig in signatures:
        if hmac.compare_digest(expected, sig):
            logger.info("Mux webhook signature OK.")
            return True

    logger.error("Computed signature did not match any provided signature.")
    return False