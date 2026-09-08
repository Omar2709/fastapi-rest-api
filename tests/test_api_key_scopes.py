from fastapi import status
from fastapi.testclient import TestClient

from app.security.scopes import APIKeyScope


def auth_headers(
    raw_key: str,
) -> dict[str, str]:
    return {
        "X-API-Key": raw_key,
    }


def test_list_api_keys_requires_read_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_WRITE,),
    )

    response = client.get(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["code"] == "INSUFFICIENT_SCOPE"
    assert response.json()["error"]["details"] == [
        {
            "missing_scopes": [
                "api-keys:read",
            ]
        }
    ]


def test_list_api_keys_accepts_read_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_READ,),
    )

    response = client.get(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == status.HTTP_200_OK


def test_create_api_key_requires_write_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_READ,),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
        json={
            "name": "New key",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["code"] == "INSUFFICIENT_SCOPE"


def test_api_key_can_delegate_owned_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(
            APIKeyScope.API_KEYS_READ,
            APIKeyScope.API_KEYS_WRITE,
        ),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
        json={
            "name": "Read only integration",
            "scopes": [
                "api-keys:read",
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["scopes"] == [
        "api-keys:read",
    ]


def test_api_key_cannot_delegate_scope_it_does_not_have(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_WRITE,),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
        json={
            "name": "Escalated key",
            "scopes": [
                "api-keys:read",
            ],
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["code"] == "INSUFFICIENT_SCOPE"


def test_create_api_key_rejects_unknown_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_WRITE,),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
        json={
            "name": "Invalid key",
            "scopes": [
                "admin:everything",
            ],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_api_key_rejects_duplicate_scopes(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.API_KEYS_WRITE,),
    )

    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
        json={
            "name": "Invalid key",
            "scopes": [
                "api-keys:write",
                "api-keys:write",
            ],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_api_key_without_scopes_can_authenticate(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["scopes"] == []

    list_response = client.get(
        "/api/v1/api-keys",
        headers=auth_headers(api_key.raw_key),
    )

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
