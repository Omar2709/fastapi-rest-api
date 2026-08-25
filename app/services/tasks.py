from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, User
from app.schemas import TaskCreate


def create_task(
    db: Session,
    user: User,
    task_data: TaskCreate,
) -> Task:
    task = Task(
        title=task_data.title,
        description=task_data.description,
        user_id=user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def get_tasks_by_user(
    db: Session,
    user_id: int,
    limit: int,
) -> list[Task]:
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.id)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def get_task(
    db: Session,
    task_id: int,
) -> Task | None:
    return db.get(
        Task,
        task_id,
    )