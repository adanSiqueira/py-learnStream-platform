"""
This module defines authentication and authorization endpoints for the API,
including user registration, login, and token refresh functionality.

It coordinates interactions between the service layer and the database,
handling password hashing, JWT generation, and secure refresh token rotation.

Endpoints:
    - POST /auth/register: Register a new user.
    - POST /auth/login: Authenticate a user and issue tokens.
    - POST /auth/refresh: Exchange a valid refresh token for new tokens.
    - POST /auth/logout: Ends user section.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    hash_token,
    decode_token
)
from app.models.sql.database import get_db
from app.services import user_ops, refresh_token_ops
from datetime import datetime, timedelta
from app.auth.deps import get_current_user

router = APIRouter(prefix='/auth')

class RegisterIn(BaseModel):
    """
    Request body for user registration.

    Attributes:
        name (str): Full name of the user.
        email (str): Email address of the user.
        password (str): Plaintext password for the account.
    """
    name: str
    email: str
    password: str

class LoginIn(BaseModel):
    """
    Request body for user login.

    Attributes:
        email (str): Email address of the user.
        password (str): Plaintext password for authentication.
    """
    email: str
    password: str

class RefreshIn(BaseModel):
    """
    Request body for token refresh.

    Attributes:
        refresh_token (str): Valid refresh token previously issued to the user.
    """
    refresh_token: str

class TokenOut(BaseModel):
    """
    Response model for access and refresh tokens.

    Attributes:
        access_token (str): JWT access token for API authentication.
        refresh_token (str): JWT refresh token to obtain new access tokens.
        token_type (str): Type of token, default is "bearer".
    """
    acess_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", status_code=201)
async def register (data: RegisterIn, db: AsyncSession = Depends(get_db)):
    """
    Register a new user in the system.

    Steps:
    1. Check if the email is already registered.
    2. Hash the provided password.
    3. Create a new user record in the database.
    4. Return the user ID and email.

    Args:
        data (RegisterIn): User registration information.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        dict: Contains `id` and `email` of the newly registered user.

    Raises:
        HTTPException: 400 if email is already registered.
    """
    existing = await user_ops.get_by_email(db, data.email)
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    hashed = hash_password(data.password)
    user = await user_ops.create_user(db, name = data.name, email = data.email, password_hash = hashed)
    return {"id": user.id, "email": user.email}

@router.post("/login", response_model = TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and return access and refresh tokens.

    Steps:
    1. Fetch the user by email.
    2. Verify the password matches the stored hash.
    3. Generate a short-lived access token.
    4. Generate a long-lived refresh token.
    5. Store the hashed refresh token in the database.
    6. Return both tokens to the client.

    Args:
        data (LoginIn): User login credentials.
        db (AsyncSession): SQLAlchemy async database session.

    Returns:
        dict: Contains `access_token` and `refresh_token`.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = await user_ops.get_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    refresh_token_hashed = hash_token(refresh_token)

    #store hashed refresh token
    await refresh_token_ops.save_refresh_token(db, user.id, refresh_token_hashed, expires_at= datetime.now() + timedelta(weeks=2))
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh", response_model=TokenOut)
async def refresh_token(data: RefreshIn, db: AsyncSession = Depends(get_db)):
    """
    Exchange a valid refresh token for a new pair of access + refresh tokens.

    Steps:
    1. Decode refresh token (JWT) to extract user_id (subject)
    2. Verify the token exists and is valid in DB
    3. Delete old refresh token (rotation)
    4. Create new access and refresh tokens
    5. Save new refresh token in DB
    6. Return both tokens
    """
    try:
        payload = decode_token(data.refresh_token)
        user_id: int = payload.get("sub")
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    hashed_refresh_token = hash_token(data.refresh_token)
    token_record = await refresh_token_ops.get_refresh_token(db, user_id, hashed_refresh_token)

    if not token_record:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token not found or revoked")

    #Check expiration
    if token_record.expires_at < datetime.now():
        await refresh_token_ops.delete_refresh_token(db, user_id, hashed_refresh_token)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    #Rotate refresh tokens
    await refresh_token_ops.delete_refresh_token(db, user_id, hashed_refresh_token)

    #Create new tokens
    new_access = create_access_token(subject=user_id)
    new_refresh = create_refresh_token(subject=user_id)

    #Persist new refresh
    expires_at = datetime.now() + timedelta(weeks=2) 
    await refresh_token_ops.save_refresh_token(db, user_id, hash_token(new_refresh), expires_at)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }

@router.post('/logout')
async def logout(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await refresh_token_ops (db, current_user.id)
    return {'detail': 'Logged out'}