from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.idempotency import (
    InvalidIdempotencyKeyError,
    create_job_submission_fingerprint,
)
from app.domain.jobs import JobType
from app.models import (
    Job,
    JobIdempotencyKey,
    OutboxEvent,
    User,
)
from app.services import jobs as job_service


def test_job_fingerprint_is_deterministic() -> None:
    first = create_job_submission_fingerprint(
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Monthly sales",
            "content": "Report content",
            "format": "pdf",
        },
    )

    second = create_job_submission_fingerprint(
        job_type=JobType.GENERATE_REPORT,
        payload={
            "format": "pdf",
            "content": "Report content",
            "title": "Monthly sales",
        },
    )

    assert first == second
    assert len(first) == 64


def test_job_fingerprint_changes_when_request_changes() -> None:
    first = create_job_submission_fingerprint(
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Monthly sales",
            "content": "First content",
            "format": "pdf",
        },
    )

    second = create_job_submission_fingerprint(
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Monthly sales",
            "content": "Different content",
            "format": "pdf",
        },
    )

    assert first != second


def create_user(
    db_session: Session,
) -> User:
    user = User(
        name="Ana",
        email="ana@example.com",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_concurrent_same_idempotency_key_creates_single_job(
    db_session: Session,
    db_session_factory,
) -> None:
    user = create_user(db_session)

    barrier = Barrier(2)

    def submit() -> tuple[UUID, bool]:
        with db_session_factory() as session:
            barrier.wait()

            submission = job_service.submit_job(
                session,
                user_id=user.id,
                idempotency_key=("concurrent-request-001"),
                job_type=(JobType.GENERATE_REPORT),
                payload={
                    "title": "Test report",
                    "content": ("Test report content"),
                    "format": "pdf",
                },
            )

            return (
                submission.job.id,
                submission.replayed,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: submit(),
                range(2),
            )
        )

    job_ids = {result[0] for result in results}

    replay_flags = sorted(result[1] for result in results)

    assert len(job_ids) == 1

    assert replay_flags == [
        False,
        True,
    ]

    job_count = db_session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user.id)
    )

    outbox_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    idempotency_count = db_session.scalar(
        select(func.count()).select_from(JobIdempotencyKey)
    )

    assert job_count == 1
    assert outbox_count == 1
    assert idempotency_count == 1


@pytest.mark.parametrize(
    "idempotency_key",
    [
        "",
        "contains spaces",
        "x" * 129,
    ],
)
def test_service_rejects_invalid_idempotency_key(
    db_session: Session,
    idempotency_key: str,
) -> None:
    user = create_user(db_session)

    with pytest.raises(InvalidIdempotencyKeyError):
        job_service.submit_job(
            db_session,
            user_id=user.id,
            idempotency_key=idempotency_key,
            job_type=JobType.GENERATE_REPORT,
            payload={
                "title": "Test report",
                "content": ("Test report content"),
                "format": "pdf",
            },
        )

    job_count = db_session.scalar(select(func.count()).select_from(Job))

    event_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    idempotency_count = db_session.scalar(
        select(func.count()).select_from(JobIdempotencyKey)
    )

    assert job_count == 0
    assert event_count == 0
    assert idempotency_count == 0


def test_idempotency_rejects_job_with_different_owner(
    db_session: Session,
) -> None:
    first_user = create_user(db_session)

    second_user = User(
        name="Carlos",
        email="carlos@example.com",
    )

    db_session.add(second_user)
    db_session.commit()
    db_session.refresh(second_user)

    payload = {
        "title": "Test report",
        "content": "Test report content",
        "format": "pdf",
    }

    submission = job_service.submit_job(
        db_session,
        user_id=first_user.id,
        idempotency_key=("first-owner-request"),
        job_type=JobType.GENERATE_REPORT,
        payload=payload,
    )

    fingerprint = create_job_submission_fingerprint(
        job_type=JobType.GENERATE_REPORT,
        payload=payload,
    )

    invalid_record = JobIdempotencyKey(
        user_id=second_user.id,
        idempotency_key=("invalid-owner-record"),
        request_fingerprint=fingerprint,
        job_id=submission.job.id,
    )

    db_session.add(invalid_record)
    db_session.commit()

    with pytest.raises(job_service.IdempotencyInvariantError):
        job_service.submit_job(
            db_session,
            user_id=second_user.id,
            idempotency_key=("invalid-owner-record"),
            job_type=JobType.GENERATE_REPORT,
            payload=payload,
        )


def test_concurrent_same_key_different_requests_create_one_job(
    db_session: Session,
    db_session_factory,
) -> None:
    user = create_user(db_session)

    barrier = Barrier(2)

    def submit(
        content: str,
    ) -> str:
        with db_session_factory() as session:
            barrier.wait()

            try:
                job_service.submit_job(
                    session,
                    user_id=user.id,
                    idempotency_key=("concurrent-conflict-001"),
                    job_type=(JobType.GENERATE_REPORT),
                    payload={
                        "title": "Test report",
                        "content": content,
                        "format": "pdf",
                    },
                )

            except job_service.IdempotencyKeyConflictError:
                return "conflict"

            return "created"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [
            executor.submit(
                submit,
                "First content",
            ),
            executor.submit(
                submit,
                "Different content",
            ),
        ]

        outcomes = sorted(future.result() for future in results)

    assert outcomes == [
        "conflict",
        "created",
    ]

    job_count = db_session.scalar(select(func.count()).select_from(Job))

    outbox_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    idempotency_count = db_session.scalar(
        select(func.count()).select_from(JobIdempotencyKey)
    )

    assert job_count == 1
    assert outbox_count == 1
    assert idempotency_count == 1
