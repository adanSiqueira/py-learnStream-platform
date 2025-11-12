"""
This module provides password hashing, verification, and JSON Web Token(JWT) 
generation and decoding utilities. Together, these functions form the 
cryptographic foundation for user authentication and authorization in the application.

It uses bcrypt (via Passlib) for secure password storage, and PyJWT for 
stateless access and refresh token management. 
"""
from typing import Any, Dict
from passlib.context import CryptContext
from app.core import config
from datetime import datetime, timedelta, timezone
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = config.settings.JWT_SECRET
ALGO = config.settings.JWT_ALGORITHM

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the configured CryptContext.
    Args:
        password (str): The user's plain-text password.

    Returns:
        str: The bcrypt hash of the password, suitable for database storage.
    """
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify whether a plain-text password matches a stored bcrypt hash.
    Args:
        plain (str): The plain-text password provided by the user.
        hashed (str): The hashed password retrieved from the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str | int, extra: Dict[str, Any] = None) -> str:
    """
    Generate a short-lived JSON Web Token (JWT) used for user authentication.

    Args:
        subject (str | int): Unique identifier of the token's subject 
            (typically the user's ID).
        extra (Dict[str, Any], optional): Additional claims to include in the payload, 
            such as roles or permissions.

    Returns:
        str: The encoded JWT as a compact string.

    Notes:
        - The access token includes a short expiration time (minutes) to limit 
          exposure if compromised.
        - The 'sub' claim identifies the user, while 'exp' defines token expiration.
        - The token is cryptographically signed using the application's SECRET and ALGO.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "access"
    }
    if extra:
        payload.update(extra)

    token = jwt.encode(payload, SECRET, algorithm=ALGO)

    return token

def create_refresh_token(subject: str | int) -> str:
    """
    Generate a long-lived JWT used to obtain new access tokens after expiration.

    Args:
        subject (str | int): The unique identifier of the token's owner (usually the user ID).

    Returns:
        str: The encoded refresh token as a string.

    Notes:
        - Refresh tokens have a longer lifespan (days or weeks).
        - They contain a 'typ' claim set to 'refresh' to distinguish them from access tokens.
        - Typically stored more securely (e.g., HTTP-only cookie) and used 
          to reissue new access tokens without requiring user login again.
    """
    expire = datetime.now() + timedelta(days=config.settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(subject), "exp": expire, "typ": "refresh"}
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT, returning its payload if valid.

    Args:
        token (str): The encoded JWT string to decode and verify.

    Returns:
        dict: The decoded payload (claims) if the token is valid and not expired.

    Raises:
        jwt.ExpiredSignatureError: If the token's expiration time ('exp') has passed.
        jwt.InvalidTokenError: If the token is malformed, tampered with, or 
            signed with an invalid secret.

    Notes:
        - This function is used during request authentication to validate 
          and extract user information from the provided token.
        - Only the server can verify a token, since it requires the same SECRET 
          used during encoding.
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise

def hash_token(token: str) -> str:
    """
    Hash a refresh token before storing it in the database.

    Args:
        token (str): The raw refresh token string to be hashed.

    Returns:
        str: The bcrypt hash of the token, suitable for secure storage.

    Notes:
        - Refresh tokens are hashed for the same reason as passwords: 
          to prevent misuse if the database is compromised.
        - The original token is never stored directly, only its hash.
    """
    return pwd_context.hash(token)

def verify_token_hash(token: str, hash_):
    """
    Verify whether a provided refresh token matches its stored hash.

    Args:
        token (str): The raw refresh token received from the client.
        hash_ (str): The hashed version of the token stored in the database.

    Returns:
        bool: True if the token corresponds to the stored hash, False otherwise.

    Notes:
        - Used during token rotation or validation to confirm that a given 
          refresh token is authentic and belongs to the requesting user.
        - Prevents attackers from using stolen token hashes directly, 
          since the verification process requires the original token.
    """
    return pwd_context.verify(token, hash_)
