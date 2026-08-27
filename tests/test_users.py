from fastapi import status
from fastapi.testclient import TestClient
import pytest


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

def test_get_users_returns_created_users(
    client: TestClient,
    user_factory,
) -> None:
    user_factory(
        name="Ana",
        email="ana@example.com",
    )

    user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    response = client.get("/users")

    assert response.status_code == (
        status.HTTP_200_OK
    )

    data = response.json()

    assert len(data) == 2

    emails = {
        user["email"]
        for user in data
    }

    assert emails == {
        "ana@example.com",
        "carlos@example.com",
    }

def test_get_user_by_id(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    response = client.get(
        f"/users/{user['id']}"
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

    data = response.json()

    assert data["id"] == user["id"]
    assert data["name"] == "Ana"
    assert data["email"] == "ana@example.com"
    assert data["is_active"] is True

def test_update_user(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    response = client.patch(
        f"/users/{user['id']}",
        json={
            "name": "Ana Actualizada",
            "is_active": False,
        },
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

    data = response.json()

    assert data["id"] == user["id"]
    assert data["name"] == "Ana Actualizada"
    assert data["email"] == "ana@example.com"
    assert data["is_active"] is False

    get_response = client.get(
        f"/users/{user['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_200_OK
    )

    stored_user = get_response.json()

    assert stored_user["name"] == "Ana Actualizada"
    assert stored_user["is_active"] is False

def test_delete_user(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    response = client.delete(
        f"/users/{user['id']}"
    )

    assert response.status_code == (
        status.HTTP_204_NO_CONTENT
    )

    assert response.content == b""

    get_response = client.get(
        f"/users/{user['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_404_NOT_FOUND
    )

def test_get_nonexistent_user_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        "/users/999999999"
    )

    assert response.status_code == (
        status.HTTP_404_NOT_FOUND
    )

    assert response.json() == {
        "detail": "Usuario no encontrado"
    }

def test_update_user_with_empty_body_returns_422(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory()

    response = client.patch(
        f"/users/{user['id']}",
        json={},
    )

    assert response.status_code == (
        status.HTTP_422_UNPROCESSABLE_CONTENT
    )

    assert "detail" in response.json()

def test_update_nonexistent_user_returns_404(
    client: TestClient,
) -> None:
    response = client.patch(
        "/users/999999999",
        json={
            "name": "Nuevo Nombre",
        },
    )

    assert response.status_code == (
        status.HTTP_404_NOT_FOUND
    )

    assert response.json() == {
        "detail": "Usuario no encontrado"
    }

def test_delete_nonexistent_user_returns_404(
    client: TestClient,
) -> None:
    response = client.delete(
        "/users/999999999"
    )

    assert response.status_code == (
        status.HTTP_404_NOT_FOUND
    )

    assert response.json() == {
        "detail": "Usuario no encontrado"
    }

def test_create_user_with_duplicate_email_returns_409(
    client: TestClient,
    user_factory,
) -> None:
    user_factory(
        name="Ana",
        email="ana@example.com",
    )

    response = client.post(
        "/users",
        json={
            "name": "Carlos",
            "email": "ana@example.com",
        },
    )

    assert response.status_code == (
        status.HTTP_409_CONFLICT
    )

    assert response.json() == {
        "detail": (
            "Ya existe un usuario con ese email"
        )
    }

def test_update_user_with_duplicate_email_returns_409(
    client: TestClient,
    user_factory,
) -> None:
    first_user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    second_user = user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    response = client.patch(
        f"/users/{second_user['id']}",
        json={
            "email": first_user["email"],
        },
    )

    assert response.status_code == (
        status.HTTP_409_CONFLICT
    )

    assert response.json() == {
        "detail": (
            "Ya existe un usuario con ese email"
        )
    }

    get_response = client.get(
        f"/users/{second_user['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_200_OK
    )

    stored_user = get_response.json()

    assert stored_user["email"] == (
        "carlos@example.com"
    )

@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "A",
            "email": "ana@example.com",
        },
        {
            "name": "Ana",
            "email": "correo-invalido",
        },
    ],
)
def test_create_user_with_invalid_data_returns_422(
    client: TestClient,
    payload: dict,
) -> None:
    response = client.post(
        "/users",
        json=payload,
    )

    assert response.status_code == (
        status.HTTP_422_UNPROCESSABLE_CONTENT
    )

    assert "detail" in response.json()

def test_delete_user_with_tasks_returns_409(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task_factory(
        user_id=user["id"],
        title="Tarea pendiente",
    )

    response = client.delete(
        f"/users/{user['id']}"
    )

    assert response.status_code == (
        status.HTTP_409_CONFLICT
    )

    assert response.json() == {
        "detail": (
            "No se puede eliminar el usuario "
            "porque tiene tareas asociadas"
        )
    }

    get_response = client.get(
        f"/users/{user['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_200_OK
    )

def test_update_user_with_empty_body_returns_422(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory()

    response = client.patch(
        f"/users/{user['id']}",
        json={},
    )

    assert response.status_code == (
        status.HTTP_422_UNPROCESSABLE_CONTENT
    )

    assert "detail" in response.json()