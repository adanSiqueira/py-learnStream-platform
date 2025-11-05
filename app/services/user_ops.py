"""
This module provides database operations for user management,
including user creation and retrieval. It abstracts raw SQLAlchemy
operations behind a simple interface, keeping the API layer clean.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.user import User
from app.models.sql.enrollment import Enrollment

async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user by email address.

    Args:
        db (AsyncSession): Active database session.
        email (str): Email address of the user.

    Returns:
        User | None: The matching user instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_by_id(db: AsyncSession, id: int) -> User | None:
    """
    Retrieve a user by id.

    Args:
        db (AsyncSession): Active database session.
        id (str): User's Id.

    Returns:
        User | None: The matching user instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.id == id))
    return result.scalars().first()


async def create_user(db: AsyncSession, name: str, email: str, password_hash: str) -> User:
    """
    Create a new user in the database.

    Args:
        db (AsyncSession): Active database session.
        name (str): User's full name.
        email (str): User's email address.
        password_hash (str): Secure hash of the user's password.

    Returns:
        User: The created user instance.
    """
    user = User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def is_enrolled (db: AsyncSession, user_id: int, course_id:str) -> bool:
    """
    Check if a given user is enrolled in a specific course.

    Args:
        db (AsyncSession): Active SQLAlchemy session.
        user_id (int): User's ID from the SQL database.
        course_id (str): Course ID from the MongoDB collection (stored as string in Enrollment).

    Returns:
        bool: True if the user is enrolled in the course, False otherwise.
    """
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        )
    )
    enrollment = result.scalars().first()
    return enrollment is not None