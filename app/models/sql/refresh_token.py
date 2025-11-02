from .database import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String
from sqlalchemy.orm import relationship
from datetime import datetime

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    token_hash = Column(String(255), nullable=False)
    issued_at = Column(DateTime, default=datetime.now())
    expires_at =  Column(DateTime)
    revoked = Column(Boolean, default = False)

    # Relationship to User
    user = relationship("User", back_populates="refresh_tokens")