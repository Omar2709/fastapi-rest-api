from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models import ApiKey, User
from app.security.api_keys import (
    GeneratedAPIKey,
    extract_api_key_id,
    verify_api_key,
)
from app.services import api_keys as api_key_service

TEST_PEPPER = "test-api-key-pepper-with-more-than-32-characters"


def create_user(
    db_session: Session,
) -> User:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_provision_api_key_persists_digest(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    result = api_key_service.provision_api_key(
        db_session,
        user_id=user.id,
        name="Local development",
        pepper=TEST_PEPPER,
    )

    stored_api_key = db_session.get(
        ApiKey,
        result.api_key.id,
    )

    assert stored_api_key is not None

    assert stored_api_key.key_id == (extract_api_key_id(result.raw_key))

    assert stored_api_key.key_digest != result.raw_key

    assert verify_api_key(
        result.raw_key,
        stored_api_key.key_digest,
        TEST_PEPPER,
    )

    assert not hasattr(
        stored_api_key,
        "raw_key",
    )


def test_provision_api_key_normalizes_name(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    result = api_key_service.provision_api_key(
        db_session,
        user_id=user.id,
        name="  Local development  ",
        pepper=TEST_PEPPER,
    )

    assert result.api_key.name == "Local development"


def test_provision_api_key_for_nonexistent_user_fails(
    db_session: Session,
) -> None:
    with pytest.raises(api_key_service.APIKeyOwnerNotFoundError):
        api_key_service.provision_api_key(
            db_session,
            user_id=999999999,
            name="Test key",
            pepper=TEST_PEPPER,
        )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        "A" * 101,
    ],
)
def test_provision_api_key_rejects_invalid_name(
    db_session: Session,
    name: str,
) -> None:
    user = create_user(db_session)

    with pytest.raises(api_key_service.InvalidAPIKeyNameError):
        api_key_service.provision_api_key(
            db_session,
            user_id=user.id,
            name=name,
            pepper=TEST_PEPPER,
        )


def test_provision_api_key_accepts_future_expiration(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    expires_at = datetime.now(UTC) + timedelta(days=30)

    result = api_key_service.provision_api_key(
        db_session,
        user_id=user.id,
        name="Temporary key",
        pepper=TEST_PEPPER,
        expires_at=expires_at,
    )

    assert result.api_key.expires_at == expires_at


def test_provision_api_key_rejects_past_expiration(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    expires_at = datetime.now(UTC) - timedelta(days=1)

    with pytest.raises(api_key_service.InvalidAPIKeyExpirationError):
        api_key_service.provision_api_key(
            db_session,
            user_id=user.id,
            name="Expired key",
            pepper=TEST_PEPPER,
            expires_at=expires_at,
        )


def test_provision_api_key_rejects_naive_expiration(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    expires_at = datetime.now() + timedelta(days=1)

    with pytest.raises(api_key_service.InvalidAPIKeyExpirationError):
        api_key_service.provision_api_key(
            db_session,
            user_id=user.id,
            name="Invalid expiration",
            pepper=TEST_PEPPER,
            expires_at=expires_at,
        )


def test_provision_api_key_retries_key_id_collision(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = create_user(db_session)

    existing_key_id = "a" * 24

    existing_api_key = ApiKey(
        user_id=user.id,
        name="Existing key",
        key_id=existing_key_id,
        key_digest="b" * 64,
    )

    db_session.add(existing_api_key)
    db_session.commit()

    generated_keys = iter(
        [
            GeneratedAPIKey(
                key_id=existing_key_id,
                raw_key=(f"fapi_{existing_key_id}_first-secret"),
            ),
            GeneratedAPIKey(
                key_id="c" * 24,
                raw_key=(f"fapi_{'c' * 24}_second-secret"),
            ),
        ]
    )

    monkeypatch.setattr(
        api_key_service,
        "generate_api_key",
        lambda: next(generated_keys),
    )

    result = api_key_service.provision_api_key(
        db_session,
        user_id=user.id,
        name="New key",
        pepper=TEST_PEPPER,
    )

    assert result.api_key.key_id == "c" * 24


def test_provision_api_key_fails_after_collisions(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = create_user(db_session)

    existing_key_id = "a" * 24

    existing_api_key = ApiKey(
        user_id=user.id,
        name="Existing key",
        key_id=existing_key_id,
        key_digest="b" * 64,
    )

    db_session.add(existing_api_key)
    db_session.commit()

    monkeypatch.setattr(
        api_key_service,
        "generate_api_key",
        lambda: GeneratedAPIKey(
            key_id=existing_key_id,
            raw_key=(f"fapi_{existing_key_id}_colliding-secret"),
        ),
    )

    with pytest.raises(api_key_service.APIKeyGenerationError):
        api_key_service.provision_api_key(
            db_session,
            user_id=user.id,
            name="New key",
            pepper=TEST_PEPPER,
        )
