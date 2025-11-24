"""
Routing layer for Course operations.

This module exposes endpoints under the `/courses` prefix and provides
features related to course discovery and enrollment.

Key responsibilities include:
- Listing all available courses stored in MongoDB.
- Retrieving detailed information for a specific course by ID.
- Handling user enrollment into a course (SQL-based).

Architecture notes:
- Course records live in **MongoDB**.
- Enrollment records live in **PostgreSQL/MySQL** via SQLAlchemy.
- Endpoints enforce authentication where required and return consistent,
  front-end-friendly JSON payloads.
- 404 errors are returned when a course does not exist.
- Enrollment endpoint ensures idempotency: users cannot enroll twice.
"""

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

@router.post("/{course_id}/enroll", summary="Enroll the user into a course")
async def enroll_in_course(
    course_id: str,
    current_user = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_sql_db)
):
    """
        Enroll the authenticated user into a course.

        Validations:
        - Ensures the course exists in MongoDB.
        - Prevents duplicate enrollments by checking whether the user
        is already enrolled in the given course.
        - Creates a new enrollment record in the SQL database.

        Args:
            course_id (str): The ID of the course stored in MongoDB.
            current_user: The authenticated user object injected by FastAPI.
            sql_db (AsyncSession): SQLAlchemy async session.

        Returns:
            dict: A JSON object containing:
                - message (str): Confirmation message.
                - course_id (str): The course the user enrolled in.
                - user_id (int): The ID of the enrolled user.
                - enrollment_id (int): Newly created enrollment record ID.

        Raises:
            HTTPException:
                - 404: If the course does not exist.
                - 400: If the user is already enrolled in the course.
                - 409: If an enrollment conflict occurs during creation.
    """

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