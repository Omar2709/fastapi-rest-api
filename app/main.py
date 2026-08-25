from fastapi import FastAPI

from app.routers import tasks, users


app = FastAPI(
    title="FastAPI REST API",
    version="0.1.0",
)


app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {
        "message": "Mi primera API REST"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }