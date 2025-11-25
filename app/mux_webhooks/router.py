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
from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.no_sql.lesson import lessons_collection
from app.core.config import settings 
import logging
from app.services.mux_service import verify_mux_signature, handle_mux_webhook

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)

# Secret from .env
MUX_WEBHOOK_SECRET = settings.MUX_WEBHOOK_SECRET

# Webhook endpoint
@router.post("/mux")
async def mux_webhook(request: Request):
    """
    Receive webhook events from Mux and update the lessons collection accordingly.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    print("─── Incoming Mux Webhook ─────────────────────")
    print("Headers:", headers)
    print("RAW BODY (first 500 bytes):", raw_body[:500])
    print("MUX_WEBHOOK_SECRET (last 4 chars):", MUX_WEBHOOK_SECRET[-4:])
    print("──────────────────────────────────────────────")

    signature_header = (
        headers.get("mux-signature")
        or headers.get("Mux-Signature")
        or headers.get("x-mux-signature")
    )

    if not signature_header:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Mux signature header.")

    # Validate signature
    if not verify_mux_signature(raw_body, signature_header):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Mux webhook signature.")

    # Now safe to parse JSON
    event = await request.json()

    try:
        return JSONResponse(
            content=await handle_mux_webhook(event, lessons_collection),
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error processing Mux webhook: {e}")
        raise HTTPException(500, "Error processing webhook.")