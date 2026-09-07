from typing import Any

from fastapi import APIRouter, status

from app.api.errors import ErrorResponse
from app.routers import auth, tasks, users

VALIDATION_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "Error de validación",
    }
}


api_router = APIRouter()

api_router.include_router(
    users.router,
    responses=VALIDATION_ERROR_RESPONSES,
)

api_router.include_router(
    tasks.router,
    responses=VALIDATION_ERROR_RESPONSES,
)

api_router.include_router(auth.router)
