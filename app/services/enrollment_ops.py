from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.enrollment import Enrollment
from sqlalchemy.exc import IntegrityError

async def create_enrollment(
        db: AsyncSession,
        user_id: int,
        course_id: str
) -> Enrollment:
    """
    Create a new Enrollment register on 'enrollments' table.
    """
    user_id = int(user_id)
    enrollment = Enrollment(user_id = user_id, course_id = course_id)
    db.add(enrollment)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(enrollment)
    return enrollment