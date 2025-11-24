"""
This module defines the routing layer for course-related endpoints.

It exposes routes under the /courses prefix, enabling clients to:
  - Retrieve a list of all available courses.
  - Fetch details for a specific course by ID.

Core responsibilities:
- Interact with MongoDB (NoSQL) through the `course` model.
- Return clean, consistent JSON responses for front-end consumption.
- Provide 404 responses when requested courses do not exist.

Dependencies:
- MongoDB connection and CRUD functions from `app.models.no_sql.course`.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.no_sql.course import list_courses, get_course_by_id
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_current_user
from app.models.sql.database import get_db as get_sql_db
from app.services.enrollment_ops import create_enrollment
from app.services.user_ops import is_enrolled

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("/", summary="List all available courses")
async def get_all_courses():
    """
    Retrieve a list of all available courses.

    Returns:
        list[dict]: A list of all courses stored in MongoDB.
    """
    courses = await list_courses()
    return [
        {
            "id": str(course["_id"]),
            "title": course.get("title"),
            "description": course.get("description"),
            "created_at": course.get("created_at"),
            "updated_at": course.get("updated_at"),
        }
        for course in courses
    ]


@router.get("/{course_id}", summary="Retrieve details for a specific course by ID")
async def get_course(course_id: str):
    """
    Retrieve details of a single course by its ObjectId.

    Args:
        course_id (str): The ObjectId of the course in MongoDB.

    Returns:
        dict: The course details if found.

    Raises:
        HTTPException:
            - 404: If the course does not exist.
    """
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found."
        )

    return {
        "id": str(course["_id"]),
        "title": course.get("title"),
        "description": course.get("description"),
        "created_at": course.get("created_at"),
        "updated_at": course.get("updated_at"),
    }

@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: str,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):

    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Course not found")
    
    user_id = int(current_user.id)

    already = await is_enrolled(sql_db, user_id, course_id)
    if already:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Already enrolled")
    
    try:
        enrollment = await create_enrollment(sql_db, user_id, course_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Enrollment already exists") from exc
    
    return {
        "message": "Enrollment successful",
        "course_id": course_id,
        "user_id": user_id,
        "enrollment_id": enrollment.id
    }