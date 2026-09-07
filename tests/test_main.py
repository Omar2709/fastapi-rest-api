from fastapi import status
from fastapi.testclient import TestClient


def test_root(
    client: TestClient,
) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Mi primera API REST"}


def test_health(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unversioned_users_route_is_not_available(
    client: TestClient,
) -> None:
    response = client.get("/users")

    assert response.status_code == status.HTTP_404_NOT_FOUND
