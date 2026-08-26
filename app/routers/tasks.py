from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services import tasks as task_service
from app.services import users as user_service


router = APIRouter(
    tags=["tasks"],
)


SessionDep = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "/users/{user_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    user_id: int,
    task_data: TaskCreate,
    db: SessionDep,
):
    user = user_service.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return task_service.create_task(
        db,
        user,
        task_data,
    )


@router.get(
    "/users/{user_id}/tasks",
    response_model=list[TaskResponse],
)
def get_user_tasks(
    user_id: int,
    db: SessionDep,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    user = user_service.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return task_service.get_tasks_by_user(
        db,
        user_id,
        limit,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    db: SessionDep,
):
    task = task_service.get_task(
        db,
        task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada",
        )

    return task

@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: SessionDep,
):
    task = task_service.get_task(
        db,
        task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada",
        )

    return task_service.update_task(
        db,
        task,
        task_data,
    )

@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    db: SessionDep,
) -> None:
    task = task_service.get_task(
        db,
        task_id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada",
        )

    task_service.delete_task(
        db,
        task,
    )