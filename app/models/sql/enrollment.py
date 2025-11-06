"""
This module defines the 'Enrollments' ORM model, representing the relationship between a user and a course, linking user
records from the SQL database to course metadata stored in the NoSQL (MongoDB) database.

Each enrollment entry tracks when the user enrolled in a course, and when
their access expires. This model supports features such as course access control,
progress tracking, and subscription management.

Relations:
- Many-to-one relationship with the 'User' model.
- Courses are identified by their MongoDB '_id' (stored as 'course_id' string).
"""
from .database import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime

class Enrollment (Base):
    """
    ORM model representig a user's enrollment in a specific course.

    Each record links a user to a course and defines when the enrollment
    started ('enrolled_at') and when it expires ('expires_at').

    Attributes:
        id (int): Primary key for the enrollment record.
        user_id (int): Foreign key linking to the 'users' table.
        course_id (str): The MongoDB identifier of the course the user is enrolled in.
        enrolled_at (datetime): Timestamp indicating when the enrollment was created.
        expires_at (datetime): Timestamp for when the enrollment access expires.

    Relationships:
        user (User): Back-reference to the 'User' model via 'user.enrollments'.
    """
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key = True, index = True )
    user_id = Column (Integer, ForeignKey('users.id'), index = True, nullable=False)
    course_id = Column(String, index=True, nullable=False)  # store Mongo course_id here
    enrolled_at = Column(DateTime, default= datetime.now())
    expires_at = Column(DateTime, default= datetime.now())

    user = relationship("User", back_populates="enrollments")