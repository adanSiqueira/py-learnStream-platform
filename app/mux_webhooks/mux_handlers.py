"""
Mux Webhook Handlers — Receives, interprets and persists Mux video lifecycle events.

This module processes webhook events originating from Mux, updating the `lessons`
MongoDB collection with the state of an asset or its upload. It keeps lesson records
synchronized with the full lifecycle:

    upload_created ➝ asset_created ➝ asset_ready ➝ playback available
    upload_cancelled / upload_errored / asset_errored / asset_deleted

Each handler receives a parsed JSON `event` payload and applies the appropriate
database update. Playback IDs, duration, metadata and status flags are persisted
for consumption by the application’s frontend and backend video services.
"""

from app.models.no_sql.lesson import lessons_collection
from app.services.mux_service import get_asset
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_title(data: dict):
    """
    Extracts the most likely title from an asset or upload payload.

    Priority order:
        1. Direct upload metadata: data["new_asset_settings"]["meta"]["title"]
        2. Asset metadata:         data["metadata"]["title"]
        3. Track names:            first track with a non-null `name`

    Parameters
    ----------
    data : dict
        Mux event `data` field.

    Returns
    -------
    str | None
        A resolved title string if available, otherwise None.
    """
    return (
        data.get("new_asset_settings", {}).get("meta", {}).get("title")
        or data.get("metadata", {}).get("title")
        or next((t.get("name") for t in data.get("tracks", []) if t.get("name")), None)
    )

# -------------------------------------------------------------
# video.asset.ready
# -------------------------------------------------------------
async def handle_asset_ready(event: dict):
    """
    Final stage in the Mux pipeline — asset is fully processed and playable.

    Actions performed:
        • Fetch remote asset details via `get_asset(asset_id)`  
        • Resolve playback ID, duration and tracks
        • Update the associated lesson entry using upload_id or asset_id
        • Write canonical mux.* fields used by the platform

    Parameters
    ----------
    event : dict
        Webhook payload containing `data.id`, `data.upload_id`, metadata, etc.

    Returns
    -------
    dict
        Standard API response: update summary + match count.
    """
    logger.info("🔥 ENTERED handle_asset_ready()")
    data = event.get("data", {}) or {}

    asset_id = data.get("id")
    if not asset_id:
        print ({"error": "missing asset id"})

    title = extract_title(data)
    if not title:
        title = "No title found"

    asset_details = await get_asset(asset_id)

    playback_id = (
        asset_details.get("playback_ids", [{}])[0].get("id")
        if asset_details.get("playback_ids")
        else None
    )

    duration = asset_details.get("duration")
    tracks = asset_details.get("tracks", [])

    logger.info(
        "Asset ready — asset_id=%s playback=%s duration=%s",
        asset_id, playback_id, duration
    )

    update_doc = {
        "$set": {
            "title": title,
            "mux.asset_id": asset_id,
            "mux.playback_id": playback_id,
            "mux.duration": duration,
            "mux.status": "ready",
            "mux.tracks": tracks,
            "mux.updated_at": datetime.now(),
        }
    }

    upload_id = data.get("upload_id") or asset_details.get("upload_id")
    query = {
    "$or": [
        {"mux.upload_id": upload_id},
        {"mux.asset_id": asset_id},
        {"video.upload_id": upload_id},
        {"video.asset_id": asset_id}
        ]
    }


    result = await lessons_collection.update_one(query, update_doc, upsert=False)

    logger.info(
        "Asset-ready DB update result: matched=%s modified=%s",
        getattr(result, "matched_count", None),
        getattr(result, "modified_count", None)
    )

    return {
        "message": "Lesson updated with ready video.",
        "matched": getattr(result, "matched_count", None),
    }

# -------------------------------------------------------------
# video.upload.created
# -------------------------------------------------------------
async def handle_upload_created(event: dict):
    """
    Triggered when a direct upload URL is generated on Mux.

    Creates a placeholder lesson record *if none exists* so that subsequent
    asset events may populate it. This allows upload → processed asset
    synchronization without requiring manual linking.

    Parameters
    ----------
    event : dict
        Webhook JSON with `data.id/upload_id`.

    Returns
    -------
    dict
        Status message indicating insert or noop.
    """
    data = event.get("data", {}) or {}

    upload_id = data.get("id") or data.get("upload_id")
    if not upload_id:
        return {"error": "missing upload id"}

    title = extract_title(data) or "Untitled Video"

    doc = {
        "title": title,
        "mux": {
            "upload_id": upload_id,
            "status": "upload_created",
        },
        "video": {
            "upload_id": upload_id,
            "status": "upload_created",
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await lessons_collection.update_one(
        {"mux.upload_id": upload_id},
        {"$setOnInsert": doc},
        upsert=True
    )

    return {"message": "Upload placeholder created."}

# -------------------------------------------------------------
# video.asset.created
# -------------------------------------------------------------
async def handle_asset_created(event: dict):
    """
    Fired shortly after upload is received, when the asset is created but
    not yet processed. Useful for tracking progress and linking asset_id.

    Persists:
        • asset_id
        • resolved title fallback
        • status: asset_created

    Parameters
    ----------
    event : dict
        Payload including `data.id` (asset) and optionally `upload_id`.

    Returns
    -------
    dict
        Update summary for diagnostic logging or webhook replay.
    """
    data = event.get("data", {}) or {}

    asset_id = data.get("id")
    upload_id = data.get("upload_id")

    if not asset_id:
        print ({"error": "missing asset id"})
    
    title = extract_title(data)
    if not title:
        title = "No title found"
    
    asset_details = await get_asset(asset_id)

    playback_id = (
        asset_details.get("playback_ids", [{}])[0].get("id")
        if asset_details.get("playback_ids")
        else None
    )

    duration = asset_details.get("duration")
    tracks = asset_details.get("tracks", [])

    logger.info(
        "Asset ready — asset_id=%s playback=%s duration=%s",
        asset_id, playback_id, duration
    )

    query = {
    "$or": [
        {"mux.upload_id": upload_id},
        {"mux.asset_id": asset_id},
        {"video.upload_id": upload_id},   # extra segurança
        {"video.asset_id": asset_id}
        ]
    }

    update_doc = {
    "$set": {
        "title": title,
        "mux.asset_id": asset_id,
        "video.asset_id": asset_id,
        "mux.status": "asset_created",
        "video.status": "asset_created",
        "updated_at": datetime.now()
        }
    }


    result = await lessons_collection.update_one(query, update_doc)

    return {
        "message": "Asset ID attached to lesson.",
        "matched": result.matched_count
    }


# -------------------------------------------------------------
# video.asset.deleted
# -------------------------------------------------------------
async def handle_asset_deleted(event: dict):
    """
    Marks the corresponding lesson entry as deleted when the asset is
    permanently removed from Mux.

    Parameters
    ----------
    event : dict
        Payload with `data.id` representing asset_id.

    Returns
    -------
    dict
        Confirmation message + matched record count.
    """
    data = event.get("data", {}) or {}
    asset_id = data.get("id")

    if not asset_id:
        return {"error": "missing asset id"}

    update_doc = {
        "$set": {
            "mux.status": "deleted",
            "video.status": "deleted",
            "updated_at": datetime.now()
        }
    }

    result = await lessons_collection.update_one({"mux.asset_id": asset_id}, update_doc)

    return {
        "message": "Asset marked as deleted.",
        "matched": result.matched_count
    }


# -------------------------------------------------------------
# video.asset.errored
# -------------------------------------------------------------
async def handle_asset_errored(event: dict):
    """
    Fired if Mux fails to process an asset.

    Marks lesson so UI and backend can respond appropriately — retries, user
    alerts, or manual re-upload.

    Returns standard diagnostic response.
    """
    data = event.get("data", {}) or {}
    asset_id = data.get("id")

    if not asset_id:
        return {"error": "missing asset id"}

    update_doc = {
        "$set": {
            "mux.status": "errored",
            "video.status": "errored",
            "updated_at": datetime.now()
        }
    }

    result = await lessons_collection.update_one(
        {"mux.asset_id": asset_id},
        update_doc,
        upsert=False
    )

    logger.info("Asset errored DB update: matched=%s", getattr(result, "matched_count", None))

    return {"message": "Asset marked as errored."}


# -------------------------------------------------------------
# video.upload.cancelled
# -------------------------------------------------------------
async def handle_upload_cancelled(event: dict):
    """
    Upload was abandoned — invalidates pending lessons.

    Used when client terminates upload or URL expires without completion.
    """
    data = event.get("data", {}) or {}

    upload_id = data.get("id") or data.get("upload_id")
    if not upload_id:
        return {"error": "missing upload id"}

    update_doc = {
        "$set": {
            "mux.status": "upload_cancelled",
            "video.status": "upload_cancelled",
            "updated_at": datetime.now()
        }
    }

    result = await lessons_collection.update_one({"mux.upload_id": upload_id}, update_doc)

    return {"message": "Upload cancelled."}


# -------------------------------------------------------------
# video.upload.errored
# -------------------------------------------------------------
async def handle_upload_errored(event: dict):
    """
    Upload failed before reaching processing stage.

    Keeps DB synchronized with failure state — helpful for UI recovery,
    retries or logging metrics.
    """
    data = event.get("data", {}) or {}

    upload_id = data.get("id") or data.get("upload_id")
    if not upload_id:
        return {"error": "missing upload id"}

    update_doc = {
        "$set": {
            "mux.status": "upload_error",
            "video.status": "upload_error",
            "updated_at": datetime.now()
        }
    }

    result = await lessons_collection.update_one({"mux.upload_id": upload_id}, update_doc)

    return {"message": "Upload errored."}

# -------------------------------------------------------------
# HANDLER MAP
# -------------------------------------------------------------
MUX_EVENT_HANDLERS = {
    "video.upload.created": handle_upload_created,
    "video.asset.created": handle_asset_created,
    "video.asset.ready": handle_asset_ready,
    "video.asset.errored": handle_asset_errored,
    "video.upload.errored": handle_upload_errored,
    "video.upload.cancelled": handle_upload_cancelled,
    "video.asset.deleted": handle_asset_deleted,
}