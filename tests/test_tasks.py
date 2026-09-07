import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_create_task(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory()

    response = client.post(
        f"/api/v1/users/{user['id']}/tasks",
        json={
            "title": "Aprender testing",
            "description": "Probar endpoints de Tasks",
        },
    )

    assert response.status_code == (status.HTTP_201_CREATED)

    data = response.json()

    assert data["title"] == "Aprender testing"
    assert data["description"] == ("Probar endpoints de Tasks")
    assert data["is_completed"] is False
    assert data["user_id"] == user["id"]

    assert isinstance(data["id"], int)
    assert "created_at" in data


def test_get_tasks_by_user(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task_factory(
        user_id=user["id"],
        title="Primera tarea",
    )

    task_factory(
        user_id=user["id"],
        title="Segunda tarea",
    )

    response = client.get(f"/api/v1/users/{user['id']}/tasks")

    assert response.status_code == (status.HTTP_200_OK)

    data = response.json()

    assert len(data) == 2

    titles = {task["title"] for task in data}

    assert titles == {
        "Primera tarea",
        "Segunda tarea",
    }


def test_get_tasks_returns_only_user_tasks(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    first_user = user_factory(
        name="Ana",
        email="ana@example.com",
    )

    second_user = user_factory(
        name="Carlos",
        email="carlos@example.com",
    )

    task_factory(
        user_id=first_user["id"],
        title="Tarea de Ana",
    )

    task_factory(
        user_id=second_user["id"],
        title="Tarea de Carlos",
    )

    response = client.get(f"/api/v1/users/{first_user['id']}/tasks")

    assert response.status_code == (status.HTTP_200_OK)

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Tarea de Ana"
    assert data[0]["user_id"] == first_user["id"]


def test_get_task_by_id(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
        title="Aprender FastAPI",
        description="Estudiar TestClient",
    )

    response = client.get(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == (status.HTTP_200_OK)

    data = response.json()

    assert data["id"] == task["id"]
    assert data["title"] == "Aprender FastAPI"
    assert data["description"] == "Estudiar TestClient"
    assert data["user_id"] == user["id"]


def test_update_task(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
        title="Aprender FastAPI",
        description="Descripción original",
    )

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "title": "Dominar FastAPI",
            "is_completed": True,
        },
    )

    assert response.status_code == (status.HTTP_200_OK)

    data = response.json()

    assert data["title"] == "Dominar FastAPI"
    assert data["description"] == "Descripción original"
    assert data["is_completed"] is True
    assert data["user_id"] == user["id"]

    get_response = client.get(f"/api/v1/tasks/{task['id']}")

    assert get_response.status_code == (status.HTTP_200_OK)

    stored_task = get_response.json()

    assert stored_task["title"] == "Dominar FastAPI"
    assert stored_task["description"] == ("Descripción original")
    assert stored_task["is_completed"] is True


def test_update_task_can_remove_description(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
        description="Descripción temporal",
    )

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "description": None,
        },
    )

    assert response.status_code == (status.HTTP_200_OK)

    data = response.json()

    assert data["description"] is None


def test_delete_task(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
    )

    response = client.delete(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == (status.HTTP_204_NO_CONTENT)

    assert response.content == b""

    get_response = client.get(f"/api/v1/tasks/{task['id']}")

    assert get_response.status_code == (status.HTTP_404_NOT_FOUND)


def test_create_task_for_nonexistent_user_returns_404(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/users/999999999/tasks",
        json={
            "title": "Tarea de prueba",
        },
    )

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "USER_NOT_FOUND",
            "message": "Usuario no encontrado",
            "details": None,
        }
    }


def test_get_tasks_for_nonexistent_user_returns_404(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users/999999999/tasks")

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "USER_NOT_FOUND",
            "message": "Usuario no encontrado",
            "details": None,
        }
    }


def test_get_nonexistent_task_returns_404(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/tasks/999999999")

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "TASK_NOT_FOUND",
            "message": "Tarea no encontrada",
            "details": None,
        }
    }


def test_update_nonexistent_task_returns_404(
    client: TestClient,
) -> None:
    response = client.patch(
        "/api/v1/tasks/999999999",
        json={
            "title": "Nuevo título",
        },
    )

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "TASK_NOT_FOUND",
            "message": "Tarea no encontrada",
            "details": None,
        }
    }


def test_delete_nonexistent_task_returns_404(
    client: TestClient,
) -> None:
    response = client.delete("/api/v1/tasks/999999999")

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "TASK_NOT_FOUND",
            "message": "Tarea no encontrada",
            "details": None,
        }
    }


@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "",
        },
        {
            "title": "     ",
        },
        {
            "title": "A" * 121,
        },
    ],
)
def test_create_task_with_invalid_data_returns_422(
    client: TestClient,
    user_factory,
    payload: dict,
) -> None:
    user = user_factory()

    response = client.post(
        f"/api/v1/users/{user['id']}/tasks",
        json=payload,
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Los datos enviados no son válidos"
    assert data["error"]["details"]
    assert "input" not in data["error"]["details"][0]


def test_update_task_with_empty_body_returns_422(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
    )

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={},
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Los datos enviados no son válidos"
    assert data["error"]["details"]
    assert "input" not in data["error"]["details"][0]


def test_update_task_with_null_title_returns_422(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
    )

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "title": None,
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Los datos enviados no son válidos"
    assert data["error"]["details"]
    assert "input" not in data["error"]["details"][0]


def test_update_task_with_null_status_returns_422(
    client: TestClient,
    user_factory,
    task_factory,
) -> None:
    user = user_factory()

    task = task_factory(
        user_id=user["id"],
    )

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "is_completed": None,
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Los datos enviados no son válidos"
    assert data["error"]["details"]
    assert "input" not in data["error"]["details"][0]
