from fastapi import status
from fastapi.testclient import TestClient


def test_create_user(
    client: TestClient,
) -> None:
    response = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
        },
    )

    assert response.status_code == (
        status.HTTP_201_CREATED
    )

    data = response.json()

    assert data["name"] == "Ana"
    assert data["email"] == "ana@example.com"
    assert data["is_active"] is True

    assert isinstance(
        data["id"],
        int,
    )

    assert "created_at" in data

def test_get_users_starts_empty(
    client: TestClient,
) -> None:
    response = client.get("/users")

    assert response.status_code == (
        status.HTTP_200_OK
    )

    assert response.json() == []