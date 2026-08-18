from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse


app = FastAPI()


SessionDep = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return {"message": "Mi primera API REST"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/users",
    response_model=list[UserResponse],
)
def get_users(
    db: SessionDep,
    limit: int = Query(default=10, ge=1, le=100),
):
    statement = (
        select(User)
        .order_by(User.id)
        .limit(limit)
    )

    users = db.scalars(statement).all()

    return users


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: SessionDep,
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    db: SessionDep,
):
    db_user = User(
        name=user.name,
        email=str(user.email),
    )

    db.add(db_user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    db.refresh(db_user)

    return db_user