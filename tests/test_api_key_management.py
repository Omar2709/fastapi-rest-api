from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiKey
from app.routers import api_keys as api_keys_router


def auth_headers(
    raw_key: str,
) -> dict[str, str]:
    return {
        "X-API-Key": raw_key,
    }


def test_create_api_key_for_authenticated_user(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    authentication_key = api_key_factory(
        user_id=user["id"],
        name="Authentication key",
        scopes=("api-keys:write",),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(authentication_key.raw_key),
        json={
            "name": "CI integration",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.headers["cache-control"] == "no-store"

    data = response.json()

    assert data["name"] == "CI integration"
    assert data["api_key"].startswith(f"fapi_{data['key_id']}_")

    assert "key_digest" not in data
    assert "user_id" not in data

    stored_api_key = db_session.scalar(
        select(ApiKey).where(ApiKey.key_id == data["key_id"])
    )

    assert stored_api_key is not None
    assert stored_api_key.user_id == user["id"]
    assert stored_api_key.key_digest != data["api_key"]


def test_create_api_key_rejects_user_id(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    first_user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    second_user = user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    authentication_key = api_key_factory(
        user_id=first_user["id"],
        scopes=("api-keys:write",),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(authentication_key.raw_key),
        json={
            "name": "Malicious key",
            "user_id": second_user["id"],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_api_keys_returns_only_owner_keys(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    first_user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    second_user = user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    authentication_key = api_key_factory(
        user_id=first_user["id"],
        name="Auth key",
        scopes=("api-keys:read",),
    )

    second_first_user_key = api_key_factory(
        user_id=first_user["id"],
        name="CI key",
    )

    second_user_key = api_key_factory(
        user_id=second_user["id"],
        name="Private key",
    )

    response = client.get(
        "/api/v1/api-keys",
        headers=auth_headers(authentication_key.raw_key),
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    returned_key_ids = {item["key_id"] for item in data}

    assert returned_key_ids == {
        authentication_key.api_key.key_id,
        second_first_user_key.api_key.key_id,
    }

    assert second_user_key.api_key.key_id not in returned_key_ids

    for item in data:
        assert "api_key" not in item
        assert "raw_key" not in item
        assert "key_digest" not in item


def test_revoke_api_key(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    authentication_key = api_key_factory(
        user_id=user["id"],
        scopes=("api-keys:write",),
    )

    target_key = api_key_factory(
        user_id=user["id"],
        name="Temporary key",
    )

    response = client.post(
        f"/api/v1/api-keys/{target_key.api_key.key_id}/revoke",
        headers=auth_headers(authentication_key.raw_key),
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["revoked_at"] is not None

    db_session.refresh(target_key.api_key)

    assert target_key.api_key.revoked_at is not None


def test_cannot_revoke_another_users_api_key(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    first_user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    second_user = user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    authentication_key = api_key_factory(
        user_id=first_user["id"],
        scopes=("api-keys:write",),
    )

    foreign_key = api_key_factory(
        user_id=second_user["id"],
    )

    response = client.post(
        f"/api/v1/api-keys/{foreign_key.api_key.key_id}/revoke",
        headers=auth_headers(authentication_key.raw_key),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json()["error"]["code"] == "API_KEY_NOT_FOUND"


def test_revoke_already_revoked_api_key_returns_409(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    authentication_key = api_key_factory(
        user_id=user["id"],
        scopes=("api-keys:write",),
    )

    target_key = api_key_factory(
        user_id=user["id"],
    )

    url = f"/api/v1/api-keys/{target_key.api_key.key_id}/revoke"

    first_response = client.post(
        url,
        headers=auth_headers(authentication_key.raw_key),
    )

    assert first_response.status_code == status.HTTP_200_OK

    second_response = client.post(
        url,
        headers=auth_headers(authentication_key.raw_key),
    )

    assert second_response.status_code == status.HTTP_409_CONFLICT

    assert second_response.json()["error"]["code"] == "API_KEY_ALREADY_REVOKED"


def test_api_key_can_revoke_itself(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    authentication_key = api_key_factory(
        user_id=user["id"],
        scopes=("api-keys:write",),
    )

    response = client.post(
        f"/api/v1/api-keys/{authentication_key.api_key.key_id}/revoke",
        headers=auth_headers(authentication_key.raw_key),
    )

    assert response.status_code == status.HTTP_200_OK

    next_response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(authentication_key.raw_key),
    )

    assert next_response.status_code == status.HTTP_401_UNAUTHORIZED

    assert next_response.json()["error"]["code"] == "API_KEY_REVOKED"


def test_create_api_key_returns_409_when_limit_reached(
    client: TestClient,
    user_factory,
    api_key_factory,
    monkeypatch,
) -> None:
    user = user_factory()

    authentication_key = api_key_factory(
        user_id=user["id"],
        scopes=("api-keys:write",),
    )

    monkeypatch.setattr(
        api_keys_router.settings,
        "api_key_max_active_per_user",
        1,
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(authentication_key.raw_key),
        json={
            "name": "Another key",
        },
    )

    assert response.status_code == (status.HTTP_409_CONFLICT)

    assert response.json()["error"]["code"] == ("API_KEY_LIMIT_REACHED")

    assert response.json()["error"]["details"] == [
        {
            "limit": 1,
        }
    ]


def test_api_key_openapi_schemas_do_not_expose_digest(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == (status.HTTP_200_OK)

    schemas = response.json()["components"]["schemas"]

    api_key_response_fields = schemas["APIKeyResponse"]["properties"]

    created_response_fields = schemas["APIKeyCreatedResponse"]["properties"]

    assert "key_digest" not in api_key_response_fields
    assert "api_key" not in api_key_response_fields
    assert "user_id" not in api_key_response_fields

    assert "api_key" in created_response_fields
    assert "key_digest" not in created_response_fields
