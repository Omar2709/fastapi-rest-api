from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services import users as user_service


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


SessionDep = Annotated[
    Session,
    Depends(get_db),
]


def get_user_or_404(
    db: Session,
    user_id: int,
) -> User:
    user = user_service.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(
    db: SessionDep,
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
):
    return user_service.get_users(
        db,
        limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: SessionDep,
):
    return get_user_or_404(
        db,
        user_id,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: SessionDep,
):
    try:
        return user_service.create_user(
            db,
            user_data,
        )

    except user_service.DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        ) from exc


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: SessionDep,
):
    user = get_user_or_404(
        db,
        user_id,
    )

    try:
        return user_service.update_user(
            db,
            user,
            user_data,
        )

    except user_service.DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        ) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: SessionDep,
) -> Response:
    user = get_user_or_404(
        db,
        user_id,
    )

    try:
        user_service.delete_user(
            db,
            user,
        )

    except user_service.UserHasTasksError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede eliminar el usuario "
                "porque tiene tareas asociadas"
            ),
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )