from sqlalchemy.orm import Session

from app.domain.jobs import JobStatus, JobType
from app.models import User
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
