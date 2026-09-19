from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.models import OutboxEvent


def test_outbox_event_can_be_persisted(
    db_session: Session,
) -> None:
    aggregate_id = uuid4()

    event = OutboxEvent(
        event_type=EventType.JOB_SUBMITTED.value,
        event_version=1,
        aggregate_type="job",
        aggregate_id=aggregate_id,
        payload={
            "job_type": "generate_report",
        },
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.event_type == "job.submitted"
    assert event.event_version == 1
    assert event.aggregate_type == "job"
    assert event.aggregate_id == aggregate_id

    assert event.payload == {
        "job_type": "generate_report",
    }

    assert event.attempts == 0
    assert event.last_error is None
    assert event.created_at is not None
    assert event.available_at is not None
    assert event.failed_at is None
    assert event.published_at is None


@pytest.mark.parametrize(
    ("event_version", "attempts"),
    [
        (0, 0),
        (1, -1),
    ],
)
def test_outbox_event_rejects_invalid_counters(
    db_session: Session,
    event_version: int,
    attempts: int,
) -> None:
    event = OutboxEvent(
        event_type="job.submitted",
        event_version=event_version,
        aggregate_type="job",
        aggregate_id=uuid4(),
        payload={},
        attempts=attempts,
    )

    db_session.add(event)

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


@pytest.mark.parametrize(
    ("event_type", "aggregate_type"),
    [
        ("   ", "job"),
        ("job.submitted", "   "),
    ],
)
def test_outbox_event_rejects_blank_types(
    db_session: Session,
    event_type: str,
    aggregate_type: str,
) -> None:
    event = OutboxEvent(
        event_type=event_type,
        event_version=1,
        aggregate_type=aggregate_type,
        aggregate_id=uuid4(),
        payload={},
    )

    db_session.add(event)

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


def test_outbox_event_cannot_be_published_and_failed(
    db_session: Session,
) -> None:
    now = datetime.now(UTC)

    event = OutboxEvent(
        event_type="job.submitted",
        event_version=1,
        aggregate_type="job",
        aggregate_id=uuid4(),
        payload={},
        published_at=now,
        failed_at=now,
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
