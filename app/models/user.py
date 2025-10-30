from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Enum
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(enum.Enum):
    student = "student"
    admin = "admin"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(Enum(UserRole))
    created_at = Column(DateTime, default = datetime.now())