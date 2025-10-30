from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
import enum

class StatusProgress(enum.Enum):
    not_started = 'not_started'
    in_progress = 'in_progress'
    completed = 'completed'

class Progress(Base):
    __tablename__ = 'progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    status = Column(Enum(StatusProgress, name="status_progress_enum"))
    last_watched_at = Column(DateTime)
    percentage = Column(Float)

    user = relationship('User', back_populates='progress')
    course = relationship('Course', back_populates='progress')