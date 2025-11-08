"""
This module handles incoming webhook events from the Mux Video API.

Mux sends notifications (webhooks) for important video lifecycle events such as:
    - video.asset.ready     → asset successfully processed
    - video.asset.errored   → processing failed
    - video.upload.created  → upload initialized

These webhooks allow the application to automatically update its MongoDB
lesson records without manual admin intervention, ensuring that video metadata
(e.g. asset_id, playback_id, duration, and status) is always in sync with Mux.

Security:
    - HMAC-SHA256 signature verification ensures that only genuine requests
      from Mux are accepted.
    - Signature is validated using the shared secret `MUX_WEBHOOK_SECRET`.
"""

from datetime import datetime
from fastapi import APIRouter, Request, Header, HTTPException, status
from app.models.no_sql.lesson import lessons_collection
from app.core.config import settings  # centralized environment management
import logging
from webhooks.mux_webhook import verify_mux_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

# Secret from .env
MUX_WEBHOOK_SECRET = settings.MUX_WEBHOOK_SECRET

# Webhook endpoint
@router.post("/mux")
async def mux_webhook(
    request: Request,
    x_mux_signature: str = Header(None)
):
    """
    Receive webhook events from Mux and update the lessons collection accordingly.

    Supported event types:
        - video.asset.ready
        - video.asset.errored

    The event payload is verified for authenticity before processing.
    """
    raw_body = await request.body()

    # Verify authenticity
    if not verify_mux_signature(raw_body, x_mux_signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Mux webhook signature.")

    payload = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})

    logger.info(f" Received Mux webhook: {event_type}")

    # Common fields
    now = datetime.now()

    # Handle event types
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
            "payload": payload,
        })
        logger.info(f" Ignored Mux event: {event_type}")
        return {"status": "ignored", "event": event_type}