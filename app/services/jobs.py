from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.jobs import JobStatus, JobType
from app.models import Job


def submit_job(
    db: Session,
    *,
    user_id: int,
    job_type: JobType,
    payload: Mapping[str, Any],
) -> Job:
    job = Job(
        user_id=user_id,
        job_type=job_type.value,
        status=JobStatus.PENDING,
        payload=dict(payload),
        attempts=0,
    )

    db.add(job)
    db.commit()
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
