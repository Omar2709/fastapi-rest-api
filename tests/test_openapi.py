import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("path", "method"),
    [
        (
            "/api/v1/users",
            "post",
        ),
        (
            "/api/v1/users/{user_id}/tasks",
            "post",
        ),
        (
            "/api/v1/api-keys",
            "post",
        ),
        (
            "/api/v1/jobs",
            "post",
        ),
        (
            "/api/v1/jobs/{job_id}",
            "get",
        ),
    ],
)
def test_v1_validation_errors_use_standard_schema(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == (status.HTTP_200_OK)

    schema = response.json()

    validation_response = schema["paths"][path][method]["responses"]["422"]

    response_schema = validation_response["content"]["application/json"]["schema"]

    assert response_schema == {"$ref": ("#/components/schemas/ErrorResponse")}
