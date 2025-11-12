from app.models.sql.user import User, UserRole
from datetime import datetime

def test_user_role_enum():
    """Ensure UserRole enum values are defined correctly."""
    assert UserRole.student.value == "student"
    assert UserRole.admin.value == "admin"

def test_user_instance_creation():
    """Test creation of User instance with default values."""
    user = User(
        name="Ada Lovelace",
        email="ada@example.com",
        password_hash="hashed_pw",
        role=UserRole.student
    )

    assert user.name == "Ada Lovelace"
    assert user.email == "ada@example.com"
    assert user.password_hash == "hashed_pw"
    assert user.role == UserRole.student  # default value
    assert isinstance(user.created_at, datetime)
    assert user.__tablename__ == "users"
