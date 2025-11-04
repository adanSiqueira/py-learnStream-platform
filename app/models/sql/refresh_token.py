"""
This module defines the `RefreshToken` ORM model, representing refresh tokens 
used in the authentication and session management system.

Each refresh token is associated with a user, and stores metadata about 
its issuance, expiration, and revocation status. This model supports 
secure and stateful refresh token rotation.

Relationships:
    - Belongs to `User` (many-to-one relationship).

Used By:
    - Authentication services for refresh token validation, rotation, and revocation.
"""

from .database import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String
from sqlalchemy.orm import relationship
from datetime import datetime

class RefreshToken(Base):
    """
    ORM model representing a refresh token entry in the database.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key referencing the associated user.
        token_hash (str): Hashed version of the refresh token for secure storage.
        issued_at (datetime): Timestamp when the token was issued.
        expires_at (datetime): Timestamp indicating token expiration.
        revoked (bool): Indicates whether the token has been manually invalidated.
        user (User): Relationship reference to the 'User' model.
    """
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    token_hash = Column(String(255), nullable=False)
    issued_at = Column(DateTime, default=datetime.now())
    expires_at =  Column(DateTime)
    revoked = Column(Boolean, default = False)

    # Relationship to User
    user = relationship("User", back_populates="refresh_tokens")