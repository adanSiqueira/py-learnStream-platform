from fastapi import FastAPI
from app.services.cache_service import init_redis, close_redis
from app.lessons.router import router as lessons_router
from app.admin.router import router as admin_router
from app.mux_webhooks.router import router as mux_webhooks_router
from app.auth.router import router as auth_router
from app.courses.router import router as courses_router
from app.lessons.router import router as lessons_router

import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app.include_router(lessons_router)
app.include_router(admin_router)
app.include_router(mux_webhooks_router)
app.include_router(auth_router)
app.include_router(courses_router)

@app.event("startup")
async def on_startup():
    """
    Application startup event handler.
    Initializes Redis connection for caching.
    """
    await init_redis()
    logging.info("Application startup: Redis initialized.")

