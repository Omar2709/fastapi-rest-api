from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.domain.jobs import JobStatus
from app.models import (
    Job,
    JobIdempotencyKey,
    OutboxEvent,
)
from app.security.scopes import APIKeyScope


def auth_headers(
    raw_key: str,
) -> dict[str, str]:
    return {
        "X-API-Key": raw_key,
    }


def job_submit_headers(
    raw_key: str,
    *,
    idempotency_key: str = "test-job-submission-001",
) -> dict[str, str]:
    return {
        "X-API-Key": raw_key,
        "Idempotency-Key": idempotency_key,
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
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "content": "Report content",
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_202_ACCEPTED)

    data = response.json()

    job_id = UUID(data["id"])

    assert response.headers["location"] == (f"/api/v1/jobs/{job_id}")

    assert response.headers["cache-control"] == ("no-store")
    assert response.headers["idempotency-replayed"] == "false"

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
        "title": "Monthly sales",
        "content": "Report content",
        "format": "pdf",
    }

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(
            OutboxEvent.aggregate_id == job_id,
            OutboxEvent.event_type == EventType.JOB_SUBMITTED.value,
        )
    )

    assert outbox_event is not None
    assert outbox_event.aggregate_type == "job"

    assert outbox_event.payload == {
        "job_type": "generate_report",
    }

    assert outbox_event.published_at is None


def test_submit_job_requires_api_key(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/jobs",
        headers={
            "Idempotency-Key": "missing-api-key-001",
        },
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_401_UNAUTHORIZED)

    assert response.json()["error"]["code"] == ("API_KEY_MISSING")


def test_submit_job_requires_idempotency_key(
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
            "job_type": "generate_report",
            "payload": {
                "title": "Test report",
                "content": ("Test report content"),
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_same_idempotency_key_and_request_returns_same_job(
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

    headers = job_submit_headers(
        api_key.raw_key,
        idempotency_key=("monthly-sales-replay-001"),
    )

    body = {
        "job_type": "generate_report",
        "payload": {
            "title": "Monthly sales",
            "content": "Report content",
            "format": "pdf",
        },
    }

    first_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json=body,
    )

    second_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json=body,
    )

    assert first_response.status_code == (status.HTTP_202_ACCEPTED)

    assert second_response.status_code == (status.HTTP_202_ACCEPTED)

    assert first_response.json()["id"] == second_response.json()["id"]

    assert second_response.headers["idempotency-replayed"] == "true"

    assert first_response.headers["location"] == second_response.headers["location"]

    job_count = db_session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user["id"])
    )

    outbox_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    idempotency_count = db_session.scalar(
        select(func.count()).select_from(JobIdempotencyKey)
    )

    assert job_count == 1
    assert outbox_count == 1
    assert idempotency_count == 1


def test_same_idempotency_key_with_different_request_returns_409(
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

    headers = job_submit_headers(
        api_key.raw_key,
        idempotency_key=("conflicting-request-001"),
    )

    first_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "content": "First content",
                "format": "pdf",
            },
        },
    )

    assert first_response.status_code == (status.HTTP_202_ACCEPTED)

    second_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "content": ("Different content"),
                "format": "pdf",
            },
        },
    )

    assert second_response.status_code == (status.HTTP_409_CONFLICT)

    assert second_response.json() == {
        "error": {
            "code": ("IDEMPOTENCY_KEY_CONFLICT"),
            "message": (
                "La Idempotency-Key ya fue utilizada con una solicitud diferente"
            ),
            "details": None,
        }
    }

    job_count = db_session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user["id"])
    )

    outbox_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    idempotency_count = db_session.scalar(
        select(func.count()).select_from(JobIdempotencyKey)
    )

    assert job_count == 1
    assert outbox_count == 1
    assert idempotency_count == 1


def test_idempotency_uses_normalized_job_payload(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    headers = job_submit_headers(
        api_key.raw_key,
        idempotency_key=("normalized-request-001"),
    )

    first_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "job_type": "generate_report",
            "payload": {
                "title": " Monthly sales ",
                "content": " Report content ",
                "format": "pdf",
            },
        },
    )

    second_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "content": "Report content",
                "format": "pdf",
            },
        },
    )

    assert first_response.json()["id"] == second_response.json()["id"]

    assert second_response.headers["idempotency-replayed"] == "true"


def test_idempotency_key_namespace_is_per_user(
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

    first_key = api_key_factory(
        user_id=first_user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    second_key = api_key_factory(
        user_id=second_user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    body = {
        "job_type": "generate_report",
        "payload": {
            "title": "Test report",
            "content": "Test content",
            "format": "pdf",
        },
    }

    first_response = client.post(
        "/api/v1/jobs",
        headers=job_submit_headers(
            first_key.raw_key,
            idempotency_key=("shared-key-001"),
        ),
        json=body,
    )

    second_response = client.post(
        "/api/v1/jobs",
        headers=job_submit_headers(
            second_key.raw_key,
            idempotency_key=("shared-key-001"),
        ),
        json=body,
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    assert first_response.json()["id"] != second_response.json()["id"]


@pytest.mark.parametrize(
    "idempotency_key",
    [
        "",
        "contains spaces",
        "x" * 129,
    ],
)
def test_submit_job_rejects_invalid_idempotency_key(
    client: TestClient,
    user_factory,
    api_key_factory,
    idempotency_key: str,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers={
            "X-API-Key": api_key.raw_key,
            "Idempotency-Key": idempotency_key,
        },
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Test report",
                "content": "Test content",
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)


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
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            },
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
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "unknown_job",
            "payload": {
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            },
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
        "payload": {
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
        field: value,
    }

    response = client.post(
        "/api/v1/jobs",
        headers=job_submit_headers(api_key.raw_key),
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

    api_key = api_key_factory(
        user_id=first_user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "content": "Report content",
                "format": "pdf",
            },
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


def test_get_job_returns_owned_job(
    client: TestClient,
    user_factory,
    api_key_factory,
    job_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    job = job_factory(
        user_id=user["id"],
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    response = client.get(
        f"/api/v1/jobs/{job.id}",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_200_OK)

    assert response.headers["cache-control"] == ("no-store")

    data = response.json()

    assert data["id"] == str(job.id)
    assert data["job_type"] == "generate_report"
    assert data["status"] == "pending"
    assert data["attempts"] == 0

    assert data["payload"] == {
        "title": "Test report",
        "content": "Test report content",
        "format": "pdf",
    }

    assert data["result"] is None
    assert data["error_code"] is None
    assert data["error_message"] is None


def test_get_foreign_job_returns_404(
    client: TestClient,
    user_factory,
    api_key_factory,
    job_factory,
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
        scopes=(APIKeyScope.JOBS_READ,),
    )

    foreign_job = job_factory(
        user_id=second_user["id"],
    )

    response = client.get(
        f"/api/v1/jobs/{foreign_job.id}",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json() == {
        "error": {
            "code": "JOB_NOT_FOUND",
            "message": "Job no encontrado",
            "details": None,
        }
    }


def test_get_unknown_job_returns_404(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    response = client.get(
        f"/api/v1/jobs/{uuid4()}",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_404_NOT_FOUND)

    assert response.json()["error"]["code"] == ("JOB_NOT_FOUND")


def test_get_job_rejects_invalid_uuid(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    response = client.get(
        "/api/v1/jobs/not-a-valid-uuid",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    assert response.json()["error"]["code"] == ("VALIDATION_ERROR")


def test_get_job_requires_jobs_read_scope(
    client: TestClient,
    user_factory,
    api_key_factory,
    job_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    job = job_factory(
        user_id=user["id"],
    )

    response = client.get(
        f"/api/v1/jobs/{job.id}",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_403_FORBIDDEN)

    assert response.json()["error"]["code"] == ("INSUFFICIENT_SCOPE")

    assert response.json()["error"]["details"] == [{"missing_scopes": ["jobs:read"]}]


def test_list_jobs_returns_only_owner_jobs(
    client: TestClient,
    user_factory,
    api_key_factory,
    job_factory,
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
        scopes=(APIKeyScope.JOBS_READ,),
    )

    first_job = job_factory(
        user_id=first_user["id"],
    )

    second_job = job_factory(
        user_id=first_user["id"],
    )

    foreign_job = job_factory(
        user_id=second_user["id"],
    )

    response = client.get(
        "/api/v1/jobs",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_200_OK)

    assert response.headers["cache-control"] == ("no-store")

    data = response.json()

    returned_ids = {item["id"] for item in data}

    assert returned_ids == {
        str(first_job.id),
        str(second_job.id),
    }

    assert str(foreign_job.id) not in returned_ids

    for item in data:
        assert "payload" not in item
        assert "result" not in item
        assert "error_message" not in item


def test_list_jobs_respects_limit(
    client: TestClient,
    user_factory,
    api_key_factory,
    job_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    for _ in range(3):
        job_factory(
            user_id=user["id"],
        )

    response = client.get(
        "/api/v1/jobs?limit=2",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_200_OK)

    assert len(response.json()) == 2


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
    ],
)
def test_list_jobs_rejects_invalid_pagination(
    client: TestClient,
    user_factory,
    api_key_factory,
    query: str,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_READ,),
    )

    response = client.get(
        f"/api/v1/jobs?{query}",
        headers=auth_headers(api_key.raw_key),
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)


def test_submit_job_location_points_to_status_resource(
    client: TestClient,
    user_factory,
    api_key_factory,
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(
            APIKeyScope.JOBS_READ,
            APIKeyScope.JOBS_WRITE,
        ),
    )

    submit_headers = job_submit_headers(
        api_key.raw_key,
    )

    read_headers = auth_headers(
        api_key.raw_key,
    )

    submit_response = client.post(
        "/api/v1/jobs",
        headers=submit_headers,
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            },
        },
    )

    assert submit_response.status_code == (status.HTTP_202_ACCEPTED)

    location = submit_response.headers["location"]

    status_response = client.get(
        location,
        headers=read_headers,
    )

    assert status_response.status_code == (status.HTTP_200_OK)

    assert status_response.json()["id"] == (submit_response.json()["id"])

    assert status_response.json()["status"] == ("pending")


def test_job_queries_are_documented_in_openapi(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()

    jobs_path = schema["paths"]["/api/v1/jobs"]

    job_detail_path = schema["paths"]["/api/v1/jobs/{job_id}"]

    assert "post" in jobs_path
    assert "get" in jobs_path
    assert "get" in job_detail_path

    assert {"ApiKeyAuth": []} in jobs_path["get"]["security"]

    assert {"ApiKeyAuth": []} in job_detail_path["get"]["security"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "title": "",
            "content": "Report content",
            "format": "pdf",
        },
        {
            "title": "Monthly sales",
            "content": "   ",
            "format": "pdf",
        },
        {
            "title": "Monthly sales",
            "content": "Report content",
            "format": "docx",
        },
        {
            "title": "Monthly sales",
            "content": "Report content",
            "format": "pdf",
            "unexpected": True,
        },
    ],
)
def test_submit_job_rejects_invalid_generate_report_payload(
    client: TestClient,
    user_factory,
    api_key_factory,
    payload: dict[str, object],
) -> None:
    user = user_factory()

    api_key = api_key_factory(
        user_id=user["id"],
        scopes=(APIKeyScope.JOBS_WRITE,),
    )

    response = client.post(
        "/api/v1/jobs",
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": payload,
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    assert response.json()["error"]["code"] == ("VALIDATION_ERROR")


def test_invalid_job_payload_creates_no_records(
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
        headers=job_submit_headers(api_key.raw_key),
        json={
            "job_type": "generate_report",
            "payload": {
                "title": "Monthly sales",
                "format": "pdf",
            },
        },
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    jobs = db_session.scalars(select(Job).where(Job.user_id == user["id"])).all()

    events = db_session.scalars(select(OutboxEvent)).all()

    assert jobs == []
    assert events == []


def test_generate_report_payload_is_documented_in_openapi(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()

    job_submit = schema["components"]["schemas"]["JobSubmit"]

    payload_schema = job_submit["properties"]["payload"]

    assert payload_schema == {"$ref": ("#/components/schemas/GenerateReportPayload")}

    report_payload = schema["components"]["schemas"]["GenerateReportPayload"]

    assert set(report_payload["required"]) == {
        "title",
        "content",
        "format",
    }

    assert report_payload["additionalProperties"] is False


def test_job_submission_documents_idempotency_key(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/api/v1/jobs"]["post"]

    idempotency_parameter = next(
        parameter
        for parameter in operation["parameters"]
        if (parameter["name"] == "Idempotency-Key")
    )

    assert idempotency_parameter["in"] == "header"

    assert idempotency_parameter["required"] is True

    assert "409" in operation["responses"]
