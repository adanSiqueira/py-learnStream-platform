"""
Routing layer for User-specific operations.

This module groups endpoints that operate on data tied to the currently
authenticated user. All routes are exposed under the `/user` prefix.

Current capabilities:
- Retrieve a list of all course enrollments for the logged-in user.
  This combines SQL (enrollment records) with MongoDB (course metadata),
  returning a unified, front-end-ready response.

Design rationale:
- User-centric endpoints are grouped separately from course routers
  because `/courses/enrollments` could be misinterpreted as "all users
  enrolled in a course". Instead, `/user/enrollments` clearly expresses
  ownership: *the enrollments belonging to the authenticated user*.
"""

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
    enrollment_id: int
    course_id: str
    course_title: str | None
    course_description: str | None
    enrolled_at: datetime

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None

@router.patch("/update", summary="Update current user profile")
async def update_my_user(
    payload: UserUpdate,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
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

@router.get("/enrollments", response_model = list[EnrollmentOut], summary="List all courses the user is enrolled in")
async def get_my_enrollments(
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    enrollments = await get_enrollments_for_user(sql_db, current_user.id)

    result = []
    for enr in enrollments:
        course = await get_course_by_id(enr.course_id)

        if not course:
            continue  # course deleted?

        result.append({
            "enrollment_id": enr.id,
            "course_id": enr.course_id,
            "course_title": course.get("title"),
            "course_description": course.get("description"),
            "enrolled_at": enr.enrolled_at
        })

    return result