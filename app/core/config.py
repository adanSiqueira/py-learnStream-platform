"""
Application configuration module.

This file centralizes all environment-based settings for the project,
including security parameters (JWT), database URIs, and expiration rules.
It uses Pydantic's BaseSettings to automatically load variables from
the environment or a .env file, with type validation and defaults.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or `.env`.

    Attributes:
        DATABASE_URL (str): SQLAlchemy-compatible connection string for the PostgreSQL database.
        MONGO_URL (str): Connection URI for the MongoDB database instance.
        MONGO_DB (str): The specific MongoDB database name to use.
        MUX_TOKEN_ID (str): Mux API access token ID for authenticated API requests.
        MUX_TOKEN_SECRET (str): Mux API secret key used in conjunction with MUX_TOKEN_ID.
        MUX_WEBHOOK_SECRET (str): Mux API secret key used in conjunction with MUX_TOKEN_ID for webhook verification.
        REDIS_URL (str): Connection URI for the Redis instance (used for caching or background tasks).
        JWT_SECRET (str): Secret key used to sign and verify JWT tokens.
        JWT_ALGORITHM (str): Cryptographic algorithm used for JWT signing (default: `"HS256"`).
        ADMIN_EMAIL (str): Email defined to the first admin user.
        ADMIN_PASSWORD (str): Secret key used to sign the first admin user.
    """
    DATABASE_URL: str
    MONGO_URL: str
    MONGO_DB: str
    MUX_TOKEN_ID: str
    MUX_TOKEN_SECRET: str
    MUX_WEBHOOK_SECRET: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    CORS_ALLOWED_ORIGINS: List[str] = ["*"]
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    """
    Configuration metadata for Pydantic Settings.

    Specifies that environment variables should be loaded from a .env file
    located in the project root directory, with UTF-8 encoding.
    Unrecognized fields in the .env file are ignored for flexibility.
    """

settings = Settings()