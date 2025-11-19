"""
This module handles database persistence of refresh tokens.
Each refresh token is stored in its hashed form for security.
"""

from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql.refresh_token import RefreshToken
from typing import Optional

async def save_refresh_token(
    db: AsyncSession,
    user_id: int,
    hashed_token: str,
    expires_at: datetime,
) -> RefreshToken:
    """
    Store a new refresh token hash in the database.

    Args:
        db (AsyncSession): Active database session.
        user_id (int): The user ID that owns the token.
        hashed_token (str): The hashed refresh token string.
        expires_at (datetime): Expiration datetime of the token.

    Returns:
        RefreshToken: The created refresh token record.
    """
    token = RefreshToken(
        user_id=user_id,
        token_hash=hashed_token,
        expires_at=expires_at,
    )
    
    db.add(token) #NOTE: db.add is synchronous and returns None -> we are not awaiting it

    await db.commit()
    await db.refresh(token)
    return token

async def get_refresh_token(db: AsyncSession, user_id: int | str, hashed_token: str) -> RefreshToken | None:
    """
    Retrieve a refresh token record by user and hash.

    Args:
        db (AsyncSession): Active database session.
        user_id (int): Owner of the token.
        hashed_token (str): Hashed token string.

    Returns:
        RefreshToken | None: The matching record if found.
    """
    user_id_int = int(user_id)  # Ensure user_id is an int to avoid SQL type mismatch
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id_int,
            RefreshToken.token_hash == hashed_token,
        )
    )
    return result.scalars().first()

async def delete_refresh_token(db: AsyncSession, user_id: int | str, hashed_token: Optional[str] = None) -> None:
    """
    Delete one or more refresh tokens from the database for a specific user.

    Args:
        db (AsyncSession): The active SQLAlchemy async database session.
        user_id (int | str): The ID of the user whose refresh token(s) will be deleted.
        hashed_token (str): Optional. The hashed value of a specific refresh token to delete.
    """
    user_id_int = int(user_id)  # Ensure user_id is an int to avoid SQL type mismatch
    stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id_int)
    if hashed_token:
        stmt = stmt.where(RefreshToken.token_hash == hashed_token)
    await db.execute(stmt)
    await db.commit()

async def revoke_tokens_for_user(db: AsyncSession, user_id: int | str) -> None:
    """
    Delete all refresh tokens for a given user (e.g., logout everywhere).

    Args:
        db (AsyncSession): Active database session.
        user_id (int | str): The user whose tokens will be removed.
    """
    user_id_int = int(user_id)  # Ensure user_id is an int to avoid SQL type mismatch
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id_int))
    await db.commit()

### ------------------ ###
### New function Added ###
### ------------------ ###
async def delete_all_refresh_tokens_for_user(db: AsyncSession, user_id: int | str) -> None:
    """
    Alternative implementation that loads, deletes, and commits.
    (keeps same behavior but uses correct sync/async calls)
    """
    user_id_int = int(user_id)  # Ensure user_id is an int to avoid SQL type mismatch
    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id_int))
    tokens = result.scalars().all()
    for t in tokens:
        db.delete(t)    # Not awaitable
    await db.commit()
