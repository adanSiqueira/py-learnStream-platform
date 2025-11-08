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
from fastapi.responses import JSONResponse
from app.models.no_sql.lesson import lessons_collection
from app.core.config import settings  # centralized environment management
import logging
from app.services.mux_service import verify_mux_signature, handle_mux_webhook

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

    event = await request.json()
    try:
        return JSONResponse(content=await handle_mux_webhook(event, lessons_collection), status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error processing Mux webhook: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error processing webhook.")