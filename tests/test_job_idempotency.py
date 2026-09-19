from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.idempotency import (
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
