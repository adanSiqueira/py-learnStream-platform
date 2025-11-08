"""
This file initializes the FastAPI instance, configures middleware, logging,
and event handlers, and registers all modular routers across the application.

Routers:
    - Auth (/auth)
    - Admin (/admin)
    - Lessons (/lessons)
    - Mux Webhooks (/webhooks/mux)
    - Courses (/courses)
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.cache_service import init_redis, close_redis

from app.auth.router import router as auth_router
from app.admin.router import router as admin_router
from app.lessons.router import router as lessons_router
from app.mux_webhooks.router import router as mux_webhooks_router
from app.courses.router import router as courses_router

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI Application Instance
def create_app() -> FastAPI:
    """
    Application factory pattern for creating and configuring the FastAPI app.
    """
    app = FastAPI(
        title="LearnStream API",
        version="1.0.0",
        description="Backend API for LearnStream platform, including lessons, authentication, and video handling."
    )

    # Middleware (CORS, etc.)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(lessons_router)
    app.include_router(mux_webhooks_router)
    app.include_router(courses_router)

    # Events
    @app.event("startup")
    async def on_startup():
        await init_redis()
        logger.info("Redis connection established.")

    @app.event("shutdown")
    async def on_shutdown():
        await close_redis()
        logger.info("Redis connection closed.")

    # Health Check
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    app = create_app()
