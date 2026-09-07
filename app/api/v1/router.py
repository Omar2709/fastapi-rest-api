from fastapi import APIRouter

from app.routers import tasks, users

api_router = APIRouter()

api_router.include_router(users.router)
api_router.include_router(tasks.router)
