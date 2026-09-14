from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.domain.jobs import (
    JobStatus,
    ensure_job_transition,
)
from app.models import Job, OutboxEvent
from app.ports.message_broker import (
    MessageBroker,
    MessageBrokerError,
    MessageEnvelope,
)

MAX_STORED_BROKER_ERROR_LENGTH = 1000


class OutboxPublishError(RuntimeError):
    def __init__(
        self,
        event_id: UUID,
    ) -> None:
        self.event_id = event_id

        super().__init__(f"No fue posible publicar el evento {event_id}")


class UnsupportedOutboxEventError(RuntimeError):
    pass


class OutboxInvariantError(RuntimeError):
    pass


def _get_next_unpublished_event(
    db: Session,
) -> OutboxEvent | None:
    return db.scalar(
        select(OutboxEvent)
        .where(OutboxEvent.published_at.is_(None))
        .order_by(
            OutboxEvent.created_at,
            OutboxEvent.id,
        )
        .with_for_update(skip_locked=True)
        .limit(1)
    )


def _build_message_envelope(
    event: OutboxEvent,
) -> MessageEnvelope:
    return MessageEnvelope(
        event_id=event.id,
        event_type=event.event_type,
        event_version=event.event_version,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        occurred_at=event.created_at,
        payload=dict(event.payload),
    )


def _get_job_for_submitted_event(
    db: Session,
    *,
    event: OutboxEvent,
) -> Job:
    if (
        event.event_type != EventType.JOB_SUBMITTED.value
        or event.aggregate_type != "job"
    ):
        raise UnsupportedOutboxEventError(
            "Tipo de evento no soportado por el publisher"
        )

    job = db.scalar(select(Job).where(Job.id == event.aggregate_id).with_for_update())

    if job is None:
        raise OutboxInvariantError("El OutboxEvent referencia un Job inexistente")

    ensure_job_transition(
        job.status,
        JobStatus.QUEUED,
    )

    return job


def _format_broker_error(
    exc: MessageBrokerError,
) -> str:
    message = str(exc).strip()

    if not message:
        message = exc.__class__.__name__

    return message[:MAX_STORED_BROKER_ERROR_LENGTH]


def publish_next_outbox_event(
    db: Session,
    *,
    broker: MessageBroker,
) -> bool:
    event = _get_next_unpublished_event(db)

    if event is None:
        db.rollback()
        return False

    job = _get_job_for_submitted_event(
        db,
        event=event,
    )

    message = _build_message_envelope(event)

    try:
        broker.publish(message)

    except MessageBrokerError as exc:
        event.attempts += 1
        event.last_error = _format_broker_error(exc)

        db.commit()

        raise OutboxPublishError(event.id) from exc

    now = datetime.now(UTC)

    event.attempts += 1
    event.last_error = None
    event.published_at = now

    job.status = JobStatus.QUEUED
    job.queued_at = now

    db.commit()

    return True
