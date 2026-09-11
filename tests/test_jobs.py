from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.jobs import JobStatus
from app.models import Job
from app.security.scopes import APIKeyScope


def auth_headers(
    raw_key: str,
) -> dict[str, str]:
    return {
        "X-API-Key": raw_key,
    }


def test_submit_job_returns_202(
    client: TestClient,
    db_session: Session,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {
                "report_id": 42,
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_202_ACCEPTED)

    data = response.json()

    job_id = UUID(data["id"])

    assert data["job_type"] == "generate_report"
    assert data["status"] == JobStatus.PENDING.value
    assert data["created_at"] is not None

    assert "user_id" not in data
    assert "payload" not in data
    assert "result" not in data

    stored_job = db_session.get(
        Job,
        job_id,
    )

    assert stored_job is not None
    assert stored_job.user_id == user["id"]
    assert stored_job.status == JobStatus.PENDING

    assert stored_job.payload == {
        "report_id": 42,
        "format": "pdf",
    }


def test_submit_job_requires_api_key(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/jobs",
        json={
            "job_type": "generate_report",
            "payload": {},
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_MISSING")


def test_submit_job_requires_jobs_write_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {},
        },
    )

    assert response.status_code == (status.HTTP_403_FORBIDDEN)

    data = response.json()

    assert data["error"]["code"] == ("INSUFFICIENT_SCOPE")

    assert data["error"]["details"] == [{"missing_scopes": ["jobs:write"]}]


def test_submit_job_rejects_unknown_job_type(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
        json={
            "job_type": "unknown_job",
            "payload": {},
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    assert response.json()["error"]["code"] == ("VALIDATION_ERROR")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "user_id",
            999999999,
        ),
        (
            "status",
            "succeeded",
        ),
        (
            "attempts",
            100,
        ),
        (
            "result",
            {
                "url": "fake",
            },
        ),
        (
            "error_code",
            "FAKE_ERROR",
        ),
    ],
)
def test_submit_job_rejects_server_managed_fields(
    client: TestClient,
    user_factory,
    api_key_factory,
    field: str,
    value: object,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    body = {
        "job_type": "generate_report",
        "payload": {},
        field: value,
    }

    response = client.post(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
        json=body,
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    assert response.json()["error"]["code"] == ("VALIDATION_ERROR")


def test_job_owner_comes_from_authenticated_api_key(
    client: TestClient,
    db_session: Session,
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

    api_key = api_key_factory(
        user_id=first_user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {"requested_user": (second_user["id"])},
        },
    )

    assert response.status_code == (status.HTTP_202_ACCEPTED)

    job = db_session.get(
        Job,
        UUID(response.json()["id"]),
    )

    assert job is not None
    assert job.user_id == first_user["id"]


def test_submit_job_is_documented_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == (status.HTTP_200_OK)

    operation = response.json()["paths"]["/api/v1/jobs"]["post"]

    assert "202" in operation["responses"]

    assert {"ApiKeyAuth": []} in operation["security"]
