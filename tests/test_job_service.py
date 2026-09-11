from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.domain.jobs import JobStatus, JobType
from app.models import User
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

    job = submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={
            "report_id": 42,
            "format": "pdf",
        },
    )

    assert job.id is not None
    assert job.user_id == user.id
    assert job.job_type == JobType.GENERATE_REPORT.value
    assert job.status == JobStatus.PENDING

    assert job.payload == {
        "report_id": 42,
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


def test_get_job_returns_owned_job(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    created_job = submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={
            "report_id": 42,
        },
    )

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

    job = job_service.submit_job(
        db_session,
        user_id=second_user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

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

    first_job = job_service.submit_job(
        db_session,
        user_id=first_user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={
            "number": 1,
        },
    )

    second_job = job_service.submit_job(
        db_session,
        user_id=first_user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={
            "number": 2,
        },
    )

    foreign_job = job_service.submit_job(
        db_session,
        user_id=second_user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

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
