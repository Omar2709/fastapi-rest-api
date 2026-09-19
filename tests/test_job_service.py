from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.contracts.jobs import InvalidJobPayloadError
from app.domain.events import EventType
from app.domain.jobs import JobStatus, JobType
from app.models import Job, OutboxEvent, User
from app.services import jobs as job_service
from app.services.jobs import submit_job


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


def test_submit_job_persists_pending_job(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    assert job.id is not None
    assert job.user_id == user.id
    assert job.job_type == JobType.GENERATE_REPORT.value
    assert job.status == JobStatus.PENDING

    assert job.payload == {
        "title": "Test report",
        "content": "Test report content",
        "format": "pdf",
    }

    assert job.attempts == 0

    assert job.result is None
    assert job.error_code is None
    assert job.error_message is None

    assert job.created_at is not None

    assert job.queued_at is None
    assert job.started_at is None
    assert job.completed_at is None

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(
            OutboxEvent.aggregate_type == "job",
            OutboxEvent.aggregate_id == job.id,
            OutboxEvent.event_type == EventType.JOB_SUBMITTED.value,
        )
    )

    assert outbox_event is not None
    assert outbox_event.event_version == 1

    assert outbox_event.payload == {
        "job_type": "generate_report",
    }

    assert outbox_event.attempts == 0
    assert outbox_event.published_at is None
    assert outbox_event.last_error is None


def test_get_job_returns_owned_job(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    created_job = submission.job

    job = job_service.get_job(
        db_session,
        user_id=user.id,
        job_id=created_job.id,
    )

    assert job.id == created_job.id
    assert job.user_id == user.id


def test_get_job_rejects_foreign_job(
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

    submission = job_service.submit_job(
        db_session,
        user_id=second_user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    with pytest.raises(job_service.JobNotFoundError):
        job_service.get_job(
            db_session,
            user_id=first_user.id,
            job_id=job.id,
        )


def test_get_job_rejects_unknown_job(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    with pytest.raises(job_service.JobNotFoundError):
        job_service.get_job(
            db_session,
            user_id=user.id,
            job_id=uuid4(),
        )


def test_list_jobs_returns_only_owner_jobs(
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

    first_submission = job_service.submit_job(
        db_session,
        user_id=first_user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Report 1",
            "content": "First report content",
            "format": "pdf",
        },
    )

    first_job = first_submission.job

    second_submission = job_service.submit_job(
        db_session,
        user_id=first_user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Report 2",
            "content": "Second report content",
            "format": "pdf",
        },
    )

    second_job = second_submission.job

    foreign_submission = job_service.submit_job(
        db_session,
        user_id=second_user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    foreign_job = foreign_submission.job

    jobs = job_service.list_jobs(
        db_session,
        user_id=first_user.id,
        limit=20,
        offset=0,
    )

    returned_ids = {job.id for job in jobs}

    assert returned_ids == {
        first_job.id,
        second_job.id,
    }

    assert foreign_job.id not in returned_ids


def test_submit_job_rolls_back_job_when_outbox_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = create_user(db_session)

    def build_invalid_event(
        *,
        job: Job,
    ) -> OutboxEvent:
        return OutboxEvent(
            id=uuid4(),
            event_type=EventType.JOB_SUBMITTED.value,
            event_version=0,
            aggregate_type="job",
            aggregate_id=job.id,
            payload={},
        )

    monkeypatch.setattr(
        job_service,
        "_build_job_submitted_event",
        build_invalid_event,
    )

    with pytest.raises(IntegrityError):
        job_service.submit_job(
            db_session,
            user_id=user.id,
            idempotency_key=f"test-{uuid4().hex}",
            job_type=JobType.GENERATE_REPORT,
            payload={
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            },
        )

    job_count = db_session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user.id)
    )

    event_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    assert job_count == 0
    assert event_count == 0


def test_submit_job_rejects_invalid_payload_before_persistence(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    with pytest.raises(InvalidJobPayloadError):
        job_service.submit_job(
            db_session,
            user_id=user.id,
            idempotency_key=f"test-{uuid4().hex}",
            job_type=JobType.GENERATE_REPORT,
            payload={},
        )

    job_count = db_session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == user.id)
    )

    outbox_count = db_session.scalar(select(func.count()).select_from(OutboxEvent))

    assert job_count == 0
    assert outbox_count == 0
