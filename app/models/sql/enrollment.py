from .database import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime

class Enrollment (Base):
    __tablename__ = 'enrollments'

    id = Column(Integer, primary_key = True, index = True )
    user_id = Column (Integer, ForeignKey('users.id'), index = True, nullable=False)
    course_id = Column(String, index=True, nullable=False)  # store Mongo course_id here
    enrolled_at = Column(DateTime, default= datetime.now())
    expires_at = Column(DateTime, default= datetime.now())

    user = relationship("User", back_populates="enrollments")