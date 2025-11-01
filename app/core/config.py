"""
Application configuration module.

This file centralizes all environment-based settings for the project,
including security parameters (JWT), database URIs, and expiration rules.
It uses Pydantic's BaseSettings to automatically load variables from
the environment or a `.env` file, with type validation and defaults.
"""
from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or `.env`.

    Attributes:
        JWT_SECRET (str): Secret key used for signing and verifying JWT tokens.
        JWT_ALGORITHM (str): Hashing algorithm used for JWT (default: HS256).
        ACESS_TOKEN_EXPIRE_MINUTES (int): Access token lifetime in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS (int): Refresh token lifetime in days.
        SQLALCHEMY_DATABASE_URI (str): Connection string for the PostgreSQL database.
    """
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    SQLALCHEMY_DATABASE_URI: str

    class Config:
        """
        Pydantic configuration for loading environment variables.

        By default, variables are read from a `.env` file located in the project root.
        """
        
        env_file = ".env"

settings = Settings()