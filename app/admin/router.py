"""
Admin routes module.

This module exposes administrative-only API endpoints, protected by role-based
access control (RBAC). It provides functionality such as creating direct Mux
uploads and managing platform-level operations that require elevated privileges.

Endpoints:
    - POST /admin/admin-only: Simple RBAC demonstration route.
    - POST /admin/uploads: Initiate a new video upload flow for lessons.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from app.auth.deps import require_role, get_current_user
from app.services.mux_service import create_direct_upload
from app.models.no_sql.lesson import create_draft_lesson

router = APIRouter(prefix="/admin")

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