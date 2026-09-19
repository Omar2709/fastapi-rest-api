from datetime import (
    UTC,
    datetime,
    timedelta,
)
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.domain.jobs import (
    InvalidJobTransitionError,
    JobStatus,
    ensure_job_transition,
)
from app.models import Job, OutboxEvent
from app.ports.message_broker import (
    MessageBroker,
    MessageBrokerError,
    MessageEnvelope,
    PermanentMessageBrokerError,
)

MAX_STORED_BROKER_ERROR_LENGTH = 1000


class OutboxPublishError(RuntimeError):
    def __init__(
        self,
        event_id: UUID,
        message: str,
    ) -> None:
        self.event_id = event_id

        super().__init__(message)


class OutboxRetryScheduledError(OutboxPublishError):
    def __init__(
        self,
        event_id: UUID,
        next_attempt_at: datetime,
    ) -> None:
        self.next_attempt_at = next_attempt_at

        super().__init__(
            event_id,
            (f"La publicación del evento {event_id} falló y será reintentada"),
        )


class OutboxPermanentFailureError(OutboxPublishError):
    def __init__(
        self,
        event_id: UUID,
    ) -> None:
        super().__init__(
            event_id,
            (f"El evento {event_id} quedó en estado de fallo terminal"),
        )


class UnsupportedOutboxEventError(RuntimeError):
    pass


class OutboxInvariantError(RuntimeError):
    pass


def calculate_retry_delay_seconds(
    *,
    attempt: int,
    base_seconds: int,
    max_seconds: int,
) -> int:
    if attempt < 1:
        raise ValueError("attempt debe ser mayor que cero")

    if base_seconds < 1:
        raise ValueError("base_seconds debe ser mayor que cero")

    if max_seconds < 1:
        raise ValueError("max_seconds debe ser mayor que cero")

    delay = base_seconds * (2 ** (attempt - 1))

    return min(
        delay,
        max_seconds,
    )


def _get_next_publishable_event(
    db: Session,
) -> OutboxEvent | None:
    return db.scalar(
        select(OutboxEvent)
        .where(
            OutboxEvent.published_at.is_(None),
            OutboxEvent.failed_at.is_(None),
            (OutboxEvent.available_at <= func.now()),
        )
        .order_by(
            OutboxEvent.available_at,
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
        event_version=(event.event_version),
        aggregate_type=(event.aggregate_type),
        aggregate_id=(event.aggregate_id),
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


def _format_outbox_error(
    exc: Exception,
) -> str:
    message = str(exc).strip()

    if not message:
        message = exc.__class__.__name__

    return message[:MAX_STORED_BROKER_ERROR_LENGTH]


def _commit(
    db: Session,
) -> None:
    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise


def _record_permanent_failure(
    db: Session,
    *,
    event: OutboxEvent,
    exc: Exception,
    now: datetime,
) -> None:
    event.attempts += 1

    event.last_error = _format_outbox_error(exc)

    event.failed_at = now

    _commit(db)


def _record_retryable_failure(
    db: Session,
    *,
    event: OutboxEvent,
    exc: Exception,
    now: datetime,
    max_attempts: int,
    retry_base_seconds: int,
    retry_max_seconds: int,
) -> datetime | None:
    event.attempts += 1

    event.last_error = _format_outbox_error(exc)

    if event.attempts >= max_attempts:
        event.failed_at = now

        _commit(db)

        return None

    retry_delay = calculate_retry_delay_seconds(
        attempt=event.attempts,
        base_seconds=(retry_base_seconds),
        max_seconds=(retry_max_seconds),
    )

    event.available_at = now + timedelta(seconds=retry_delay)

    _commit(db)

    return event.available_at


def publish_next_outbox_event(
    db: Session,
    *,
    broker: MessageBroker,
    max_attempts: int = 5,
    retry_base_seconds: int = 5,
    retry_max_seconds: int = 300,
) -> bool:
    if max_attempts < 1:
        raise ValueError("max_attempts debe ser mayor que cero")

    event = _get_next_publishable_event(db)

    if event is None:
        db.rollback()
        return False

    try:
        job = _get_job_for_submitted_event(
            db,
            event=event,
        )

        message = _build_message_envelope(event)

        broker.publish(message)

    except (
        PermanentMessageBrokerError,
        UnsupportedOutboxEventError,
        OutboxInvariantError,
        InvalidJobTransitionError,
    ) as exc:
        now = datetime.now(UTC)

        _record_permanent_failure(
            db,
            event=event,
            exc=exc,
            now=now,
        )

        raise (OutboxPermanentFailureError(event.id)) from exc

    except MessageBrokerError as exc:
        now = datetime.now(UTC)

        next_attempt_at = _record_retryable_failure(
            db,
            event=event,
            exc=exc,
            now=now,
            max_attempts=(max_attempts),
            retry_base_seconds=(retry_base_seconds),
            retry_max_seconds=(retry_max_seconds),
        )

        if next_attempt_at is None:
            raise (OutboxPermanentFailureError(event.id)) from exc

        raise OutboxRetryScheduledError(
            event.id,
            next_attempt_at,
        ) from exc

    except Exception:
        db.rollback()
        raise

    now = datetime.now(UTC)

    event.attempts += 1
    event.last_error = None
    event.published_at = now

    job.status = JobStatus.QUEUED
    job.queued_at = now

    _commit(db)

    return True
