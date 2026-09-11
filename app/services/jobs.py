from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.domain.jobs import JobStatus, JobType
from app.models import Job, OutboxEvent

JOB_AGGREGATE_TYPE = "job"
JOB_SUBMITTED_EVENT_VERSION = 1


def submit_job(
    db: Session,
    *,
    user_id: int,
    job_type: JobType,
    payload: Mapping[str, Any],
) -> Job:
    job = Job(
        id=uuid4(),
        user_id=user_id,
        job_type=job_type.value,
        status=JobStatus.PENDING,
        payload=dict(payload),
        attempts=0,
    )

    outbox_event = _build_job_submitted_event(
        job=job,
    )

    db.add_all(
        [
            job,
            outbox_event,
        ]
    )

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(job)

    return job


class JobNotFoundError(LookupError):
    pass


def get_job(
    db: Session,
    *,
    user_id: int,
    job_id: UUID,
) -> Job:
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.user_id == user_id,
        )
    )

    if job is None:
        raise JobNotFoundError("Job no encontrado")

    return job


def list_jobs(
    db: Session,
    *,
    user_id: int,
    limit: int,
    offset: int,
) -> list[Job]:
    statement = (
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(
            Job.created_at.desc(),
            Job.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return list(db.scalars(statement).all())


def _build_job_submitted_event(
    *,
    job: Job,
) -> OutboxEvent:
    return OutboxEvent(
        id=uuid4(),
        event_type=EventType.JOB_SUBMITTED.value,
        event_version=JOB_SUBMITTED_EVENT_VERSION,
        aggregate_type=JOB_AGGREGATE_TYPE,
        aggregate_id=job.id,
        payload={
            "job_type": job.job_type,
        },
    )
