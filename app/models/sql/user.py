"""
This module defines the 'User' ORM model, representing application users and 
their authentication credentials, roles, and relationships.

It also defines the 'UserRole' enumeration used to distinguish between 
different types of users within the system (e.g., student, admin).

Relationships:
    - One-to-many with 'RefreshToken' (a user can have multiple refresh tokens).

Used By:
    - Authentication and authorization services.
    - User management endpoints (registration, login, role assignment, etc.).
"""
from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

class UserRole(enum.Enum):
    """
    Enumeration representing user roles in the application.
    """
    student = "student"
    admin = "admin"

class User(Base):
    """
    ORM model representing a user in the system.

    Attributes:
        id (int): Primary key.
        name (str): Full name of the user.
        email (str): Unique email address used for authentication.
        password_hash (str): Secure hash of the user's password.
        role (UserRole): Role assigned to the user (student/admin).
        created_at (datetime): Account creation timestamp.
        refresh_tokens (List[RefreshToken]): List of user's refresh tokens.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, server_default="student", nullable=False)
    created_at = Column(DateTime, default = datetime.now, server_default=func.now(), nullable=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        """Initialize User instance with default created_at if not provided."""
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now()
        super().__init__(**kwargs)