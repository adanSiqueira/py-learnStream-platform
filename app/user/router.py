from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.models.no_sql.course import get_course_by_id
from app.auth.deps import get_current_user
from app.models.sql.database import get_db as get_sql_db
from app.services.user_ops import get_enrollments_for_user, update_user
from datetime import datetime
from app.services.security import hash_password

router = APIRouter(prefix="/user", tags = ["User"])

class EnrollmentOut(BaseModel):
    """
    Response model representing a user's enrollment entry with combined SQL + NoSQL data.

    Returned by: `GET /user/enrollments`
    """
    enrollment_id: int
    course_id: str
    course_title: str | None
    course_description: str | None
    enrolled_at: datetime

class UserUpdate(BaseModel):
    """
    Allowed fields for user profile updates.

    None fields are ignored, enabling partial updates without affecting
    unchanged values in the user's record.
    """
    name: str | None = None
    email: str | None = None
    password: str | None = None

@router.patch("/update", summary="Update current user profile")
async def update_my_user(
    payload: UserUpdate,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    """
    Update the profile information of the currently authenticated user.

    This endpoint performs partial updates — only the provided fields
    (non-None) are applied. If a new password is sent, it is securely
    re-hashed before storage.

    Args:
        payload (UserUpdate): Possible fields to update (`name`, `email`, `password`).
        current_user (User): Injected authenticated user performing the update.
        sql_db (AsyncSession): SQLAlchemy session for DB operations.

    Returns:
        dict: Success message + which fields were updated.
              Returns `"Nothing to update"` if no fields were supplied.

    Raises:
        None explicitly here — update validations may occur downstream.
    """
    updates = {}

    if payload.name is not None:
        updates["name"] = payload.name

    if payload.email is not None:
        updates["email"] = payload.email

    if payload.password is not None:
        updates["password_hash"] = hash_password(payload.password)

    if not updates:
        return {"message": "Nothing to update"}

    updated = await update_user(sql_db, current_user.id, updates)

    return {
        "message": "User updated successfully",
        "updated_fields": list(updates.keys())
    }

@router.get("/enrollments", response_model=list[EnrollmentOut], summary="List all courses the user is enrolled in")
async def get_my_enrollments(
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    """
    Retrieve all course enrollments belonging to the authenticated user.

    This endpoint joins **SQL enrollment records** with **MongoDB course metadata**
    to produce a complete and structured response, suitable for direct
    front-end consumption.

    Workflow:
        1. Fetch all enrollment rows from SQL.
        2. For each, fetch course details from MongoDB.
        3. Merge results into `EnrollmentOut` objects.

    Args:
        current_user (User): Currently authenticated user (dependency).
        sql_db (AsyncSession): Database session to query user enrollments.

    Returns:
        list[EnrollmentOut]: Array of all enrollments belonging to the user.
                             Courses missing in MongoDB are skipped.

    Example response:
        [
            {
                "enrollment_id": 12,
                "course_id": "abc123",
                "course_title": "Python for APIs",
                "course_description": "Learn FastAPI step-by-step",
                "enrolled_at": "2025-02-10T14:28:51Z"
            }
        ]
    """
    enrollments = await get_enrollments_for_user(sql_db, current_user.id)

    result = []
    for enr in enrollments:
        course = await get_course_by_id(enr.course_id)

        if not course:
            continue  

        result.append({
            "enrollment_id": enr.id,
            "course_id": enr.course_id,
            "course_title": course.get("title"),
            "course_description": course.get("description"),
            "enrolled_at": enr.enrolled_at
        })

    return result
