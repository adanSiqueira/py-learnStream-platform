"""
Admin routes module.

This module exposes administrative-only API endpoints, protected by role-based
access control (RBAC). It provides functionality such as creating direct Mux
uploads and managing platform-level operations that require elevated privileges.

Endpoints:
    - POST /admin/admin-only: Simple RBAC demonstration route.
    - POST /admin/uploads: Initiate a new video upload flow for lessons.
    - POST /admin/uploads/from-url
    - POST /admin/uploads/import-existing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel
import httpx
from app.auth.deps import require_role, get_current_user
from app.services.mux_service import create_direct_upload
from app.models.no_sql.lesson import create_draft_lesson
from app.models.no_sql.course import get_course_by_id, update_course
from app.models.no_sql.course import create_course, get_course_by_title
from app.models.no_sql.lesson import get_lesson, update_lesson
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin Actions"])
MUX_API_BASE = "https://api.mux.com"
MUX_TOKEN_SECRET = settings.MUX_TOKEN_SECRET
MUX_TOKEN_ID = settings.MUX_TOKEN_ID
MUX_WEBHOOK_SECRET = settings.MUX_WEBHOOK_SECRET

auth = (MUX_TOKEN_ID, MUX_TOKEN_SECRET)

# ===============================================================
# Admin checking endpoint
# ===============================================================

@router.post("/admin-only")
async def admin_action(user=Depends(require_role(["admin"]))):
    """
    Protected endpoint accessible only by users with the 'admin' role.

    This route demonstrates the use of the `require_role` dependency to enforce
    role-based access control (RBAC). Any user without the "admin" role will
    receive a 403 Forbidden response.

    Args:
        user (User): The authenticated admin user (injected automatically via dependency).

    Returns:
        dict: A confirmation message or result from the admin operation.
    """
    return {"detail": f"Admin access granted for user {user.email}"}

# ===============================================================
# Creating/Updating courses endpoints
# ===============================================================
class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

@router.post("/create_course")
async def new_course(title: str , description: str):
    """
    Create a new course if the title does not already exist.

    Behavior:
        - Checks whether a course with the same title already exists.
        - If it does, returns HTTP 400.
        - If not, creates a new course document and returns metadata.

    Args:
        title (str): The course name.
        description (str): A short summary of what the course contains.

    Returns:
        dict: Success message, created course ID and its initial fields.
    """
    existing = await get_course_by_title(title=title)
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Course already exists")
    
    new_course = await create_course(title = title, description = description)

    return {'Status': 'Created', 
            'course_id': new_course,
            'title': title,
            'description': description}

@router.patch("/update_course/{course_id}", summary="Update an existing course")
async def update_course_endpoint(
    course_id: str,
    payload: CourseUpdate,
    current_user = Depends(get_current_user),
):
    # Optional: Only admins can edit courses
    if current_user.role.value != "admin":
        raise HTTPException(403, "Only admins can update courses")

    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}

    if not updates:
        return {"message": "No fields to update"}

    await update_course(course_id, updates)

    return {"message": "Course updated successfully", "updated_fields": updates}

# ===============================================================
# Creating (Uploads) lessons endpoints:
#  -- Upload by session in MUX 
#  -- Upload from a pre-existing URL 
#  -- Upload by Import-for-existing-in-MUX
# ===============================================================

@router.post("/uploads", dependencies=[Depends(require_role(["admin"]))])
async def create_upload(
    current_user = Depends(get_current_user),
    course_id: str | None = Form(None),
    title: str = Form("Untitled Lesson"),
    description: str = Form("Pending upload")
):
    """
    Create a direct upload session in Mux and store a draft lesson in MongoDB.

    Steps:
        1. Calls Mux's API to create a direct upload (returns upload URL & ID).
        2. Creates a draft lesson document linked to that upload ID.
        3. Returns both Mux upload info and draft lesson metadata.

    This allows the platform to later match Mux webhooks (e.g. `asset.ready`)
    with the corresponding lesson draft, ensuring a seamless ingestion flow.

    Args:
        current_user (User): The authenticated admin user (injected).
        course_id (str, optional): The ID of the course this lesson belongs to.
        title (str, optional): Preliminary title for the lesson.
        description (str, optional): Short description for the draft lesson.

    Returns:
        dict: Contains both Mux upload info and draft lesson data.
    """
    # 1. Create a Mux direct upload session
    upload = await create_direct_upload()

    if not upload or "id" not in upload:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Mux upload."
        )

    upload_id = upload["id"]

    # 2. Create a draft lesson in Mongo linked to the Mux upload
    lesson_id = await create_draft_lesson(
        course_id=course_id,
        title=title,
        description=description,
        upload_id=upload_id
    )

    # 3. Return upload and draft info together
    return {
        "upload": upload,
        "lesson": {
            "id": lesson_id,
            "title": title,
            "description": description,
            "status": "uploading",
            "created_by": str(current_user.id),
        },
    }

@router.post("/uploads/from-url")
async def create_asset_from_url(
    video_url: str,
    title: str,
    description: str):
    """
    Create a Mux asset directly from an external URL and register it as a draft lesson.

    This does **not** use the Mux Direct Upload flow. Instead, it:
        1. Sends a POST request to Mux's `/assets` endpoint with a public video URL.
        2. Mux pulls the video from the specified URL.
        3. Stores the returned asset ID + playback IDs into your local database.

    Useful when:
        - The video already exists on a public bucket/server.
        - Admins want to import remote videos without uploading files.

    Args:
        video_url (str): Publicly accessible URL containing the MP4 file.
        title (str): Title of the draft lesson.
        description (str): Description of the draft lesson.

    Returns:
        dict: Mux asset details + created lesson metadata.
    """
    async with httpx.AsyncClient(auth=auth) as client:
        response = await client.post(
            "https://api.mux.com/video/v1/assets",
            json={
                "inputs": [{'url' : str(video_url), 'name' : str(title)}],
                "playback_policy": ["public"],
                "encoding_tier": "baseline"
            }
        )
        response.raise_for_status()
        data = response.json()["data"]

    # You should store the mux asset ID in your lessons database
    asset_id = data["id"]
    playback_ids = data["playback_ids"]

    lesson_id = await create_draft_lesson(
    title=title,
    description=description,
    asset_id=asset_id,
    playback_id=playback_ids[0]["id"] if playback_ids else None,
    status=data.get("status", "processing"),
    upload_method="url-import"
    )

    return {
    "status": "success",
    "lesson": {
        "id": lesson_id,
        "status": data.get("status", "processing")
    },
    "asset": {
        "id": asset_id,
        "playback_id": playback_ids[0]["id"] if playback_ids else None
    }
    }

@router.post("/uploads/import-existing")
async def import_existing_mux_asset(asset_id: str = Form(...), course_id: str = Form(...), lesson_title: str = None):
    """
    Import a video already stored in Mux and register it as a lesson in the platform.

    This endpoint retrieves metadata for an existing Mux asset using its ID, then
    stores a new lesson entry referencing that asset.

    Typical use cases:
        - Migrating content from an older system.
        - Registering assets uploaded manually through the Mux dashboard.
        - Recovering orphaned assets.

    Args:
        asset_id (str): ID of an already existing Mux asset.

    Returns:
        dict: Asset metadata + created lesson metadata.
    """
    # get asset details from Mux to validate it
    async with httpx.AsyncClient() as client:
        url = f"https://api.mux.com/video/v1/assets/{asset_id}"

        try:
            resp = await client.get(url, auth=(MUX_TOKEN_ID, MUX_TOKEN_SECRET))
            resp.raise_for_status()
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail="Mux asset Not Found"
            )

        data = resp.json().get("data", {})

        if not data or data.get("id") is None:
            raise HTTPException(
                status_code=404,
                detail="Mux asset Not Found"
            )

        lesson_id = await create_draft_lesson(
            course_id=course_id,
            title=lesson_title,
            description=f"Imported existing Mux asset {asset_id}",
            asset_id=data["id"],
            playback_id=data.get("playback_ids", [{}])[0].get("id"),
            status=data.get("status", "ready"),
            upload_method="import-existing"
        )

        return {
            "status": "success",
            "lesson": {
                "id": lesson_id,
                "status": data.get("status")
            },
            "asset": {
                "id": data["id"],
                "status": data.get("status")
                }
            }

# ===============================================================
# Updating lesson endpoint
# ===============================================================
class LessonUpdate(BaseModel):
    title: str | None = None
    course_id: str | None = None
    description: str | None = None
    mux: dict | None = None

@router.patch("/update_lesson/{lesson_id}", summary="Update an existing lesson (admin only)")
async def update_lesson_endpoint(
    lesson_id: str,
    payload: LessonUpdate,
    current_user = Depends(get_current_user)
):
    """
    Update details about a lesson (title, course, description or mux fields).

    This endpoint is restricted to admin users only. It retrieves the lesson,
    applies only the modified fields from the payload, and saves the update.

    Args:
        lesson_id (str): Target lesson document ID.
        payload (LessonUpdate): Fields to update.
        current_user (User): Injected authenticated admin user.

    Returns:
        dict: Status of the update + which fields were applied.
    """
    if current_user.role.value != "admin":
        raise HTTPException(403, "Only admins can edit lessons")

    lesson = await get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    updates = {}

    if payload.title is not None:
        updates["title"] = payload.title

    if payload.course_id is not None:
        updates["course_id"] = payload.course_id

    if payload.description is not None:
        updates["description"] = payload.description

    if payload.mux is not None:
        updates["mux"] = {**lesson.get("mux", {}), **payload.mux}

    if not updates:
        return {"message": "No fields to update"}

    await update_lesson(lesson_id, updates)

    return {"message": "Lesson updated successfully", "updated_fields": updates}