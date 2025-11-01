"""
This module provides password hashing and verification utilities, 
as well as access to JWT configuration parameters. It forms the 
cryptographic foundation for user authentication in the application.

"""
from passlib.context import CryptContext
from core import config

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