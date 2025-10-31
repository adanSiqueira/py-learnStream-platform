from .database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum
import enum
from datetime import datetime

class UserRole(enum.Enum):
    student = "student"
    admin = "admin"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    created_at = Column(DateTime, default = datetime.now(), nullable=False)