from app.models.sql.enrollment import Enrollment
from datetime import datetime

def test_enrollment_creation():
    """Test creation of an Enrollment instance."""
    enrollment = Enrollment(
        user_id=42,
        course_id="abc123",
        enrolled_at=datetime(2025, 1, 1),
        expires_at=datetime(2026, 1, 1),
    )

    assert enrollment.user_id == 42
    assert enrollment.course_id == "abc123"
    assert isinstance(enrollment.enrolled_at, datetime)
    assert isinstance(enrollment.expires_at, datetime)
    assert enrollment.__tablename__ == "enrollments"
