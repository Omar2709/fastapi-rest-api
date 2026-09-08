from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User


def test_auth_requires_api_key(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json() == {
        "error": {
            "code": "API_KEY_MISSING",
            "message": "Se requiere una API Key",
            "details": None,
        }
    }

    assert response.headers["www-authenticate"] == ("APIKey")


def test_auth_rejects_invalid_api_key_format(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": "invalid-key",
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_INVALID")


def test_auth_rejects_unknown_api_key(
    client: TestClient,
) -> None:
    raw_key = f"fapi_{'a' * 24}_unknown-secret"

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": raw_key,
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_INVALID")


def test_auth_rejects_wrong_api_key_secret(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
    )

    modified_raw_key = f"{api_key.raw_key}modified"

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": modified_raw_key,
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_INVALID")


def test_auth_accepts_valid_api_key(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        name="Local development",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": api_key.raw_key,
        },
    )

    assert response.status_code == (status.HTTP_200_OK)

    assert response.json() == {
        "user_id": user["id"],
        "key_id": api_key.api_key.key_id,
        "api_key_name": "Local development",
        "scopes": [],
    }


def test_auth_updates_last_used_at(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    provisioned = api_key_factory(
        user_id=user["id"],
    )

    assert provisioned.api_key.last_used_at is None

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": provisioned.raw_key,
        },
    )

    assert response.status_code == (status.HTTP_200_OK)

    db_session.refresh(provisioned.api_key)

    assert provisioned.api_key.last_used_at is not None


def test_auth_rejects_revoked_api_key(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    provisioned = api_key_factory(
        user_id=user["id"],
    )

    provisioned.api_key.revoked_at = datetime.now(UTC)

    db_session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": provisioned.raw_key,
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_REVOKED")


def test_auth_rejects_expired_api_key(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    provisioned = api_key_factory(
        user_id=user["id"],
        expires_at=(datetime.now(UTC) + timedelta(days=1)),
    )

    provisioned.api_key.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    db_session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": provisioned.raw_key,
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_EXPIRED")


def test_auth_rejects_inactive_owner(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user_data = user_factory()

    provisioned = api_key_factory(
        user_id=user_data["id"],
    )

    user = db_session.get(
        User,
        user_data["id"],
    )

    assert user is not None

    user.is_active = False
    db_session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-API-Key": provisioned.raw_key,
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_OWNER_INACTIVE")


def test_api_key_auth_is_documented_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == (status.HTTP_200_OK)

    schema = response.json()

    security_scheme = schema["components"]["securitySchemes"]["ApiKeyAuth"]

    assert security_scheme["type"] == "apiKey"
    assert security_scheme["in"] == "header"
    assert security_scheme["name"] == "X-API-Key"

    operation = schema["paths"]["/api/v1/auth/me"]["get"]

    assert {"ApiKeyAuth": []} in operation["security"]
