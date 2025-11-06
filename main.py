from fastapi import FastAPI
from app.services.cache_service import init_redis, close_redis
from app.lessons.router import router as lessons_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_redis()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis()

app.include_router(lessons_router)
