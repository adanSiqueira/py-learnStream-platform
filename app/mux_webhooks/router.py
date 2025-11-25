"""
Mux webhook receiver router.
"""
from fastapi import APIRouter, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.config import settings
import logging
from app.services.mux_service import verify_mux_signature
from app.mux_webhooks.mux_handlers import MUX_EVENT_HANDLERS

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)

MUX_WEBHOOK_SECRET = settings.MUX_WEBHOOK_SECRET

@router.post("/mux")
async def mux_webhook(request: Request, mux_signature: str | None = Header(None, alias="mux-signature")):
    """
    Receive webhook events from Mux and dispatch to handlers.
    Robust: initializes event_type/event_id so logging/exception handlers won't crash.
    Accepts mux-signature header alias and verifies signature using verify_mux_signature.
    """
    # Read raw body first (used for signature verification)
    raw_body = await request.body()

    # Initialize for safe logging even when parsing fails
    event_type: str | None = None
    event_id: str | None = None

    # Debug logs (keeps raw body truncated)
    try:
        headers = dict(request.headers)
    except Exception:
        headers = {}
    logger.info("─── Incoming Mux Webhook ─────────────────────")
    logger.info("Headers: %s", headers)
    logger.info("RAW BODY (first 500 bytes): %s", raw_body[:500])

    # Accept different header spellings (ngrok / proxies may lowercase)
    signature_header = mux_signature or headers.get("x-mux-signature") or headers.get("Mux-Signature")

    if not signature_header:
        logger.warning("Missing Mux signature header. Headers present: %s", list(headers.keys()))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Mux signature header.")

    # Verify signature
    try:
        if not verify_mux_signature(raw_body, signature_header):
            logger.error("Invalid Mux webhook signature.")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Mux webhook signature.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Exception while verifying Mux signature: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Signature verification error.")

    # Safe JSON parsing and handler dispatch
    try:
        event = await request.json()
        event_type = event.get("type")
        event_id = event.get("id")
        logger.info("Handling event %s (id=%s)", event_type, event_id)

        # Resolve handler (fallback to)
        handler = MUX_EVENT_HANDLERS.get(event_type)

        if not handler:
            logger.warning("No handler for event type: %s", event_type)
            return JSONResponse( content={"message": f"Ignored unsupported event type: {event_type}"}, status_code=status.HTTP_200_OK)

        # Call the handler. Handlers should be async and accept the event dict.
        response = await handler(event)

        # Optionally: log success
        logger.info("Handled event %s (id=%s) -> %s", event_type, event_id, response)

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)

    except HTTPException:
        # Re-raise to allow FastAPI to handle HTTPExceptions
        raise
    except Exception as e:
        logger.exception(
            "Error processing webhook. event_type=%s event_id=%s error=%s raw_body_head=%s",
            event_type, event_id, e, (raw_body[:300] if isinstance(raw_body, (bytes, bytearray)) else str(raw_body)) 
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error processing webhook.")
