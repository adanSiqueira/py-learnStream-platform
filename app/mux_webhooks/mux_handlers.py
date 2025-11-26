from app.models.no_sql.lesson import lessons_collection
from app.services.mux_service import get_asset
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_title(data: dict):
    return (
        data.get("new_asset_settings", {}).get("meta", {}).get("title")
        or data.get("metadata", {}).get("title")
        or next((t.get("name") for t in data.get("tracks", []) if t.get("name")), None)
    )

# -------------------------------------------------------------
# video.asset.ready
# -------------------------------------------------------------
async def handle_asset_ready(event: dict):
    logger.info("🔥 ENTERED handle_asset_ready()")
    data = event.get("data", {}) or {}

    asset_id = data.get("id")
    if not asset_id:
        print ({"error": "missing asset id"})

    title = extract_title(data)
    if not title:
        title = "No title found"

    #----------------------------------------------------------------------#
    #---fetch asset details from Mux (playback_ids, duration, tracks)------#
    #----------------------------------------------------------------------#
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
    #----------------------------------------------------------------------#
    #----------------------------------------------------------------------#

    update_doc = {
        "$set": {
            "title": title,
            # canonical
            "mux.asset_id": asset_id,
            "mux.playback_id": playback_id,
            "mux.duration": duration,
            "mux.status": "ready",
            "mux.tracks": tracks,
            "mux.updated_at": datetime.now(),

            # backwards compatibility
            "video.asset_id": asset_id,
            "video.playback_id": playback_id,
            "video.duration": duration,
            "video.status": "ready",
            "video.tracks": tracks,
            "video.updated_at": datetime.now(),
        }
    }

    # try matching by upload_id first
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
    data = event.get("data", {}) or {}

    asset_id = data.get("id")
    upload_id = data.get("upload_id")

    if not asset_id:
        print ({"error": "missing asset id"})
    
    title = extract_title(data)
    if not title:
        title = "No title found"
    
    #----------------------------------------------------------------------#
    #---fetch asset details from Mux (playback_ids, duration, tracks)------#
    #----------------------------------------------------------------------#
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

    #----------------------------------------------------------------------#
    #----------------------------------------------------------------------#

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