from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

class Lesson(Base):
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key = True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(400))
    created_at = Column(DateTime, default = datetime.now)
    updated_at = Column(DateTime, default = datetime.now)

    course = relationship('Course', back_populates='lessons')
    # In the Course class, there is a relationship attribute called lessons that points back here.