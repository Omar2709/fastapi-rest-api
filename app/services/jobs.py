from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.contracts.jobs import normalize_job_payload
from app.domain.events import EventType
from app.domain.idempotency import (
    create_job_submission_fingerprint,
    validate_idempotency_key,
)
from app.domain.jobs import JobStatus, JobType
from app.models import Job, JobIdempotencyKey, OutboxEvent

JOB_AGGREGATE_TYPE = "job"
JOB_SUBMITTED_EVENT_VERSION = 1
IDEMPOTENCY_UNIQUE_CONSTRAINT = "uq_job_idempotency_keys_user_key"


@dataclass(
    frozen=True,
    slots=True,
)
class JobSubmissionResult:
    job: Job
    replayed: bool


class IdempotencyKeyConflictError(ValueError):
    pass


class IdempotencyInvariantError(RuntimeError):
    pass


def _is_idempotency_key_collision(
    exc: IntegrityError,
) -> bool:
    sqlstate = getattr(
        exc.orig,
        "sqlstate",
        None,
    )

    diag = getattr(
        exc.orig,
        "diag",
        None,
    )

    constraint_name = getattr(
        diag,
        "constraint_name",
        None,
    )

    return sqlstate == "23505" and constraint_name == IDEMPOTENCY_UNIQUE_CONSTRAINT


def _get_idempotency_record(
    db: Session,
    *,
    user_id: int,
    idempotency_key: str,
) -> JobIdempotencyKey | None:
    return db.scalar(
        select(JobIdempotencyKey).where(
            JobIdempotencyKey.user_id == user_id,
            JobIdempotencyKey.idempotency_key == idempotency_key,
        )
    )


def _resolve_existing_submission(
    db: Session,
    *,
    record: JobIdempotencyKey,
    user_id: int,
    request_fingerprint: str,
) -> JobSubmissionResult:
    if record.user_id != user_id:
        raise IdempotencyInvariantError(
            "El registro de idempotencia pertenece a otro usuario"
        )

    if record.request_fingerprint != request_fingerprint:
        raise IdempotencyKeyConflictError(
            "La Idempotency-Key ya fue utilizada con otra solicitud"
        )

    job = db.get(
        Job,
        record.job_id,
    )

    if job is None or job.user_id != user_id:
        raise IdempotencyInvariantError(
            "La Idempotency-Key referencia un Job con ownership inválido"
        )

    return JobSubmissionResult(
        job=job,
        replayed=True,
    )


def submit_job(
    db: Session,
    *,
    user_id: int,
    idempotency_key: str,
    job_type: JobType,
    payload: Mapping[str, Any],
) -> JobSubmissionResult:
    validated_idempotency_key = validate_idempotency_key(idempotency_key)

    validated_payload = normalize_job_payload(
        job_type=job_type,
        payload=payload,
    )

    request_fingerprint = create_job_submission_fingerprint(
        job_type=job_type,
        payload=validated_payload,
    )

    existing_record = _get_idempotency_record(
        db,
        user_id=user_id,
        idempotency_key=validated_idempotency_key,
    )

    if existing_record is not None:
        return _resolve_existing_submission(
            db,
            record=existing_record,
            user_id=user_id,
            request_fingerprint=request_fingerprint,
        )

    job = Job(
        id=uuid4(),
        user_id=user_id,
        job_type=job_type.value,
        status=JobStatus.PENDING,
        payload=validated_payload,
        attempts=0,
    )

    outbox_event = _build_job_submitted_event(
        job=job,
    )

    idempotency_record = JobIdempotencyKey(
        user_id=user_id,
        idempotency_key=validated_idempotency_key,
        request_fingerprint=request_fingerprint,
        job_id=job.id,
    )

    db.add_all(
        [
            job,
            outbox_event,
            idempotency_record,
        ]
    )

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if not _is_idempotency_key_collision(exc):
            raise

        existing_record = _get_idempotency_record(
            db,
            user_id=user_id,
            idempotency_key=validated_idempotency_key,
        )

        if existing_record is None:
            raise IdempotencyInvariantError(
                "No fue posible recuperar la Idempotency-Key después de una colisión"
            ) from exc

        return _resolve_existing_submission(
            db,
            record=existing_record,
            user_id=user_id,
            request_fingerprint=request_fingerprint,
        )

    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(job)

    return JobSubmissionResult(
        job=job,
        replayed=False,
    )


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
