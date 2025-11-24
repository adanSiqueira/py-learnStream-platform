"""
This file initializes the FastAPI instance, configures middleware, logging,
and lifespan events, and registers all modular routers across the application.

Routers:
    - Auth (/auth)
    - Admin (/admin)
    - Lessons (/lessons)
    - Mux Webhooks (/webhooks/mux)
    - Courses (/courses)
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.services.cache_service import init_redis, close_redis
from app.models.sql.database import AsyncSessionLocal
from app.services import user_ops
from app.services.security import hash_password

from app.auth.router import router as auth_router
from app.admin.router import router as admin_router
from app.lessons.router import router as lessons_router
from app.mux_webhooks.router import router as mux_webhooks_router
from app.courses.router import router as courses_router
from app.user.router import router as user_router

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Defines startup and shutdown lifecycle logic for the FastAPI application.
    """
    # --- Startup ---
    await init_redis()
    logger.info("Redis connection established.")
    
    # --- Bootstrap admin user ---
    async with AsyncSessionLocal() as db:
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD

        existing_admin = await user_ops.get_by_email(db, admin_email)

        if not existing_admin:
            logger.info("No admin found. Creating initial admin...")

            hashed = hash_password(admin_password)

            await user_ops.create_user(
                db,
                name="Platform Admin",
                email=admin_email,
                password_hash=hashed,
                role="admin"
            )

            logger.warning(f"Initial admin created:")
            logger.warning("CHANGE THE PASSWORD IMMEDIATELY IN PRODUCTION!")
        else:
            logger.info("Admin user already exists. Skipping bootstrap.")

    yield  # Application runs during this period

    # --- Shutdown ---
    await close_redis()
    logger.info("Redis connection closed.")


def create_app() -> FastAPI:
    """
    Application factory pattern for creating and configuring the FastAPI app.
    """
    app = FastAPI(
        title="LearnStream API",
        version="1.0.0",
        description="Backend API for LearnStream platform, including lessons, authentication, and video handling.",
        lifespan=lifespan,  # Modern lifespan context manager
    )

    # Middleware (CORS, etc.)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Opening endpoint
    @app.get("/", tags=["System"])
    async def root():
        html_path = Path("static/index.html")
        if html_path.exists():
            return FileResponse(html_path, media_type="text/html")
        return {"message": "Welcome to the LearnStream API!"}

    # Routers
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(lessons_router)
    app.include_router(mux_webhooks_router)
    app.include_router(courses_router)
    app.include_router(user_router)

    # Health Check
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)