from enum import StrEnum
from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    USER_HAS_TASKS = "USER_HAS_TASKS"

    VALIDATION_ERROR = "VALIDATION_ERROR"

    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    HTTP_ERROR = "HTTP_ERROR"


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    type: str


class ErrorData(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorData


class APIError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

        super().__init__(message)


async def api_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    api_error = cast(APIError, exc)

    return JSONResponse(
        status_code=api_error.status_code,
        content={
            "error": {
                "code": api_error.code.value,
                "message": api_error.message,
                "details": api_error.details,
            }
        },
    )


async def validation_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    validation_error = cast(RequestValidationError, exc)

    details = []

    for error in validation_error.errors():
        field = ".".join(str(part) for part in error["loc"])

        details.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Los datos enviados no son válidos",
                "details": details,
            }
        },
    )


async def http_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    http_exception = cast(StarletteHTTPException, exc)

    error_code = ErrorCode.HTTP_ERROR

    if http_exception.status_code == status.HTTP_404_NOT_FOUND:
        error_code = ErrorCode.NOT_FOUND
    elif http_exception.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        error_code = ErrorCode.METHOD_NOT_ALLOWED

    message = (
        http_exception.detail
        if isinstance(http_exception.detail, str)
        else "Error HTTP"
    )

    return JSONResponse(
        status_code=http_exception.status_code,
        content={
            "error": {
                "code": error_code.value,
                "message": message,
                "details": None,
            }
        },
        headers=http_exception.headers,
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    app.add_exception_handler(
        APIError,
        api_error_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )

    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
