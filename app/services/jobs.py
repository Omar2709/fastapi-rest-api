from collections.abc import Mapping
from typing import Any

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
