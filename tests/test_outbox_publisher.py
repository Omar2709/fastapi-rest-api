from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.events import EventType
from app.domain.jobs import (
    InvalidJobTransitionError,
    JobStatus,
    JobType,
)
from app.models import OutboxEvent, User
from app.ports.message_broker import (
    MessageBrokerError,
    MessageEnvelope,
)
from app.services import jobs as job_service
from app.services import outbox as outbox_service


class RecordingMessageBroker:
    def __init__(
        self,
        *,
        failures_remaining: int = 0,
    ) -> None:
        self.messages: list[MessageEnvelope] = []
        self.failures_remaining = failures_remaining
        self._lock = Lock()

    def publish(
        self,
        message: MessageEnvelope,
    ) -> None:
        with self._lock:
            if self.failures_remaining > 0:
                self.failures_remaining -= 1

                raise MessageBrokerError("Broker unavailable")

            self.messages.append(message)


class BlockingMessageBroker:
    def __init__(self) -> None:
        self.messages: list[MessageEnvelope] = []

        self.publish_started = Event()
        self.allow_publish = Event()

    def publish(
        self,
        message: MessageEnvelope,
    ) -> None:
        self.publish_started.set()

        if not self.allow_publish.wait(timeout=5):
            raise RuntimeError("Timed out waiting for test synchronization")

        self.messages.append(message)


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


def test_publish_outbox_event_queues_job(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={
            "report_id": 42,
        },
    )

    broker = RecordingMessageBroker()

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True

    assert len(broker.messages) == 1

    message = broker.messages[0]

    assert message.event_type == (EventType.JOB_SUBMITTED.value)

    assert message.event_version == 1
    assert message.aggregate_type == "job"
    assert message.aggregate_id == job.id

    assert message.payload == {
        "job_type": "generate_report",
    }

    db_session.refresh(job)

    assert job.status == JobStatus.QUEUED
    assert job.queued_at is not None

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == job.id)
    )

    assert outbox_event is not None

    assert outbox_event.attempts == 1
    assert outbox_event.published_at is not None
    assert outbox_event.last_error is None


def test_broker_failure_keeps_job_pending(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

    broker = RecordingMessageBroker(
        failures_remaining=1,
    )

    with pytest.raises(outbox_service.OutboxPublishError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    db_session.refresh(job)

    assert job.status == JobStatus.PENDING
    assert job.queued_at is None

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == job.id)
    )

    assert outbox_event is not None

    assert outbox_event.attempts == 1
    assert outbox_event.published_at is None

    assert outbox_event.last_error == ("Broker unavailable")


def test_failed_outbox_event_can_be_retried(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

    broker = RecordingMessageBroker(
        failures_remaining=1,
    )

    with pytest.raises(outbox_service.OutboxPublishError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True
    assert len(broker.messages) == 1

    db_session.refresh(job)

    assert job.status == JobStatus.QUEUED

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == job.id)
    )

    assert outbox_event is not None

    assert outbox_event.attempts == 2
    assert outbox_event.published_at is not None
    assert outbox_event.last_error is None


def test_published_event_is_not_published_again(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

    broker = RecordingMessageBroker()

    first_result = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    second_result = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert first_result is True
    assert second_result is False

    assert len(broker.messages) == 1


def test_invalid_job_state_is_detected_before_publish(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job = job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

    job.status = JobStatus.RUNNING
    db_session.commit()

    broker = RecordingMessageBroker()

    with pytest.raises(InvalidJobTransitionError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    assert broker.messages == []


def test_concurrent_publishers_do_not_publish_same_event(
    db_session: Session,
    db_session_factory,
) -> None:
    user = create_user(db_session)

    job_service.submit_job(
        db_session,
        user_id=user.id,
        job_type=JobType.GENERATE_REPORT,
        payload={},
    )

    broker = BlockingMessageBroker()

    def publish() -> bool:
        with db_session_factory() as session:
            return outbox_service.publish_next_outbox_event(
                session,
                broker=broker,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(publish)

        assert broker.publish_started.wait(timeout=5)

        second_future = executor.submit(publish)

        second_result = second_future.result(timeout=5)

        broker.allow_publish.set()

        first_result = first_future.result(timeout=5)

    assert first_result is True
    assert second_result is False

    assert len(broker.messages) == 1
