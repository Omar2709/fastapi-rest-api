from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router

app = FastAPI(
    title="FastAPI REST API",
    version="0.1.0",
)

register_exception_handlers(app)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {"message": "Mi primera API REST"}


@app.get("/health")
def health():
    return {"status": "ok"}
