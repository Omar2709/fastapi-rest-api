from fastapi import status
from fastapi.testclient import TestClient

def test_create_task(
    client: TestClient,
    user_factory,
) -> None:
    user = user_factory()

    response = client.post(
        f"/users/{user['id']}/tasks",
        json={
            "title": "Aprender testing",
            "description": "Probar endpoints de Tasks",
        },
    )

    assert response.status_code == (
        status.HTTP_201_CREATED
    )

    data = response.json()

    assert data["title"] == "Aprender testing"
    assert data["description"] == (
        "Probar endpoints de Tasks"
    )
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

    response = client.get(
        f"/users/{user['id']}/tasks"
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

    data = response.json()

    assert len(data) == 2

    titles = {
        task["title"]
        for task in data
    }

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

    response = client.get(
        f"/users/{first_user['id']}/tasks"
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

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

    response = client.get(
        f"/tasks/{task['id']}"
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

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
        f"/tasks/{task['id']}",
        json={
            "title": "Dominar FastAPI",
            "is_completed": True,
        },
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

    data = response.json()

    assert data["title"] == "Dominar FastAPI"
    assert data["description"] == "Descripción original"
    assert data["is_completed"] is True
    assert data["user_id"] == user["id"]

    get_response = client.get(
        f"/tasks/{task['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_200_OK
    )

    stored_task = get_response.json()

    assert stored_task["title"] == "Dominar FastAPI"
    assert stored_task["description"] == (
        "Descripción original"
    )
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
        f"/tasks/{task['id']}",
        json={
            "description": None,
        },
    )

    assert response.status_code == (
        status.HTTP_200_OK
    )

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

    response = client.delete(
        f"/tasks/{task['id']}"
    )

    assert response.status_code == (
        status.HTTP_204_NO_CONTENT
    )

    assert response.content == b""

    get_response = client.get(
        f"/tasks/{task['id']}"
    )

    assert get_response.status_code == (
        status.HTTP_404_NOT_FOUND
    )

