from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.jobs import JobStatus
from app.models import Job, User


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


def test_job_can_be_persisted(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = Job(
        user_id=user.id,
        job_type="generate_report",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert isinstance(job.id, UUID)

    assert job.user_id == user.id
    assert job.job_type == "generate_report"
    assert job.status == JobStatus.PENDING

    assert job.payload == {
        "title": "Test report",
        "content": "Test report content",
        "format": "pdf",
    }

    assert job.result is None
    assert job.error_code is None
    assert job.error_message is None

    assert job.attempts == 0

    assert job.created_at is not None
    assert job.queued_at is None
    assert job.started_at is None
    assert job.completed_at is None


def test_job_status_persists_public_enum_value(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = Job(
        user_id=user.id,
        job_type="generate_report",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    db_session.add(job)
    db_session.commit()

    stored_status = db_session.execute(
        text(
            """
            SELECT status
            FROM jobs
            WHERE id = CAST(:job_id AS uuid)
            """
        ),
        {
            "job_id": str(job.id),
        },
    ).scalar_one()

    assert stored_status == "pending"


def test_job_type_cannot_be_blank(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = Job(
        user_id=user.id,
        job_type="   ",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    db_session.add(job)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23514"
    )

    db_session.rollback()


def test_job_attempts_cannot_be_negative(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = Job(
        user_id=user.id,
        job_type="generate_report",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
        attempts=-1,
    )

    db_session.add(job)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23514"
    )

    db_session.rollback()


def test_job_requires_existing_user(
    db_session: Session,
) -> None:
    job = Job(
        user_id=999999999,
        job_type="generate_report",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    db_session.add(job)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23503"
    )

    db_session.rollback()


def test_database_rejects_invalid_job_status(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    invalid_job_id = uuid4()

    with pytest.raises(IntegrityError) as exc_info:
        db_session.execute(
            text(
                """
                INSERT INTO jobs (
                    id,
                    user_id,
                    job_type,
                    status,
                    payload,
                    attempts
                )
                VALUES (
                    CAST(:job_id AS uuid),
                    :user_id,
                    'generate_report',
                    'invalid-status',
                    '{}'::jsonb,
                    0
                )
                """
            ),
            {
                "job_id": str(invalid_job_id),
                "user_id": user.id,
            },
        )

        db_session.commit()

    assert (
        getattr(
            exc_info.value.orig,
            "sqlstate",
            None,
        )
        == "23514"
    )

    db_session.rollback()


def test_deleting_user_with_job_is_restricted(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = Job(
        user_id=user.id,
        job_type="generate_report",
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    db_session.add(job)
    db_session.commit()

    with pytest.raises(IntegrityError) as exc_info:
        db_session.execute(delete(User).where(User.id == user.id))

        db_session.commit()

    assert getattr(
        exc_info.value.orig,
        "sqlstate",
        None,
    ) in {"23001", "23503"}

    db_session.rollback()
