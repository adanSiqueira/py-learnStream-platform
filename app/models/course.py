from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key = True)
    title = Column(String(100), unique = True, nullable=False)
    description = Column(String(400))
    created_at = Column(DateTime, default = datetime.now)
    updated_at = Column(DateTime, default = datetime.now)

    lessons = relationship('Lesson', back_populates='course') 
    #In the Lesson class, there is a relationship attribute called course that points back here.”
    progress = relationship('Progress', back_populates='course')
    #In the Progress class, there is a relationship attribute called course that points back here.”