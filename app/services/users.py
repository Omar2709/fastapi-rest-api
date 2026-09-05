from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserCreate, UserUpdate


class DuplicateEmailError(Exception):
    pass


class UserHasTasksError(Exception):
    pass


def get_users(
    db: Session,
    limit: int,
) -> list[User]:
    statement = select(User).order_by(User.id).limit(limit)

    return list(db.scalars(statement).all())


def get_user(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    user = User(
        name=user_data.name,
        email=str(user_data.email),
    )

    db.add(user)

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateEmailError from exc

        raise

    db.refresh(user)

    return user


def update_user(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        update_data["email"] = str(update_data["email"])

    for field_name, value in update_data.items():
        setattr(
            user,
            field_name,
            value,
        )

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateEmailError from exc

        raise

    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user: User,
) -> None:
    db.delete(user)

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        sqlstate = getattr(
            exc.orig,
            "sqlstate",
            None,
        )

        if sqlstate in {"23001", "23503"}:
            raise UserHasTasksError from exc

        raise
