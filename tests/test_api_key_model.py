import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ApiKey, User


def test_api_key_can_be_persisted(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    api_key = ApiKey(
        user_id=user.id,
        name="Local development",
        key_id="a" * 24,
        key_digest="b" * 64,
    )

    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert isinstance(api_key.id, int)
    assert api_key.user_id == user.id
    assert api_key.name == "Local development"
    assert api_key.created_at is not None

    assert api_key.expires_at is None
    assert api_key.revoked_at is None
    assert api_key.last_used_at is None


def test_api_key_id_must_be_unique(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    first_api_key = ApiKey(
        user_id=user.id,
        name="First key",
        key_id="a" * 24,
        key_digest="b" * 64,
    )

    second_api_key = ApiKey(
        user_id=user.id,
        name="Second key",
        key_id="a" * 24,
        key_digest="c" * 64,
    )

    db_session.add_all(
        [
            first_api_key,
            second_api_key,
        ]
    )

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23505"
    )

    db_session.rollback()


def test_api_key_name_cannot_be_blank(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    api_key = ApiKey(
        user_id=user.id,
        name="   ",
        key_id="a" * 24,
        key_digest="b" * 64,
    )

    db_session.add(api_key)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23514"
    )

    db_session.rollback()


def test_deleting_user_cascades_api_keys(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    api_key = ApiKey(
        user_id=user.id,
        name="Temporary key",
        key_id="a" * 24,
        key_digest="b" * 64,
    )

    db_session.add(api_key)
    db_session.commit()

    db_session.execute(delete(User).where(User.id == user.id))
    db_session.commit()

    remaining_api_keys = db_session.scalar(
        select(func.count()).select_from(ApiKey).where(ApiKey.user_id == user.id)
    )

    assert remaining_api_keys == 0


def test_api_key_scopes_are_persisted(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    api_key = ApiKey(
        user_id=user.id,
        name="Scoped key",
        key_id="a" * 24,
        key_digest="b" * 64,
        scopes=[
            "api-keys:read",
            "api-keys:write",
        ],
    )

    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.scopes == [
        "api-keys:read",
        "api-keys:write",
    ]


def test_api_key_scopes_default_to_empty(
    db_session: Session,
) -> None:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    api_key = ApiKey(
        user_id=user.id,
        name="No permissions",
        key_id="a" * 24,
        key_digest="b" * 64,
    )

    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.scopes == []
