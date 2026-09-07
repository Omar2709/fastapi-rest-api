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
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "details": None,
        }
    }


def test_unknown_route_uses_standard_error_format(
    client: TestClient,
) -> None:
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "details": None,
        }
    }


def test_method_not_allowed_uses_standard_error_format(
    client: TestClient,
) -> None:
    response = client.post("/health")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    assert response.json() == {
        "error": {
            "code": "METHOD_NOT_ALLOWED",
            "message": "Method Not Allowed",
            "details": None,
        }
    }
