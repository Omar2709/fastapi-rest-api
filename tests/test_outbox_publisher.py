import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event, Lock
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.aws.sqs import (
    SQSMessageBroker,
)
from app.domain.events import EventType
from app.domain.jobs import (
    JobStatus,
    JobType,
)
from app.models import OutboxEvent, User
from app.ports.message_broker import (
    MessageEnvelope,
    PermanentMessageBrokerError,
    RetryableMessageBrokerError,
)
from app.services import jobs as job_service
from app.services import outbox as outbox_service


class RecordingSQSClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def send_message(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.calls.append(kwargs)

        return {"MessageId": "test-message-id"}


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

                raise RetryableMessageBrokerError("Broker unavailable")

            self.messages.append(message)


class PermanentFailingMessageBroker:
    def publish(
        self,
        message: MessageEnvelope,
    ) -> None:
        del message

        raise PermanentMessageBrokerError("Invalid broker message")


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

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

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

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    broker = RecordingMessageBroker(
        failures_remaining=1,
    )

    with pytest.raises(outbox_service.OutboxRetryScheduledError):
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
    assert outbox_event.failed_at is None

    assert outbox_event.available_at > outbox_event.created_at

    assert outbox_event.last_error == ("Broker unavailable")


def test_failed_outbox_event_can_be_retried(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    broker = RecordingMessageBroker(
        failures_remaining=1,
    )

    with pytest.raises(outbox_service.OutboxRetryScheduledError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    outbox_event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == job.id)
    )

    assert outbox_event is not None

    outbox_event.available_at = datetime.now(UTC) - timedelta(seconds=1)

    db_session.commit()

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True
    assert len(broker.messages) == 1

    db_session.refresh(job)
    db_session.refresh(outbox_event)

    assert job.status == JobStatus.QUEUED

    assert outbox_event.attempts == 2
    assert outbox_event.published_at is not None
    assert outbox_event.failed_at is None
    assert outbox_event.last_error is None


def test_published_event_is_not_published_again(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
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

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    job.status = JobStatus.RUNNING
    db_session.commit()

    broker = RecordingMessageBroker()

    with pytest.raises(outbox_service.OutboxPermanentFailureError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == job.id)
    )

    assert event is not None
    assert event.failed_at is not None
    assert event.published_at is None
    assert broker.messages == []


def test_concurrent_publishers_do_not_publish_same_event(
    db_session: Session,
    db_session_factory,
) -> None:
    user = create_user(db_session)

    job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
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


def test_outbox_publisher_can_use_sqs_adapter(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    job = submission.job

    sqs_client = RecordingSQSClient()

    broker = SQSMessageBroker(
        client=sqs_client,
        queue_url=("https://example.invalid/jobs"),
    )

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True

    assert len(sqs_client.calls) == 1

    message = json.loads(sqs_client.calls[0]["MessageBody"])

    assert message["aggregate_id"] == str(job.id)

    assert message["event_type"] == ("job.submitted")

    db_session.refresh(job)

    assert job.status == JobStatus.QUEUED


@pytest.mark.parametrize(
    (
        "attempt",
        "expected_delay",
    ),
    [
        (1, 5),
        (2, 10),
        (3, 20),
        (4, 40),
        (7, 300),
    ],
)
def test_outbox_retry_delay_is_exponential_and_capped(
    attempt: int,
    expected_delay: int,
) -> None:
    delay = outbox_service.calculate_retry_delay_seconds(
        attempt=attempt,
        base_seconds=5,
        max_seconds=300,
    )

    assert delay == expected_delay


def test_retryable_failure_becomes_terminal_after_max_attempts(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    broker = RecordingMessageBroker(
        failures_remaining=2,
    )

    with pytest.raises(outbox_service.OutboxRetryScheduledError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
            max_attempts=2,
            retry_base_seconds=1,
            retry_max_seconds=1,
        )

    event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == submission.job.id)
    )

    assert event is not None

    event.available_at = datetime.now(UTC) - timedelta(seconds=1)

    db_session.commit()

    with pytest.raises(outbox_service.OutboxPermanentFailureError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
            max_attempts=2,
            retry_base_seconds=1,
            retry_max_seconds=1,
        )

    db_session.refresh(event)

    assert event.attempts == 2
    assert event.failed_at is not None
    assert event.published_at is None

    result = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert result is False


def test_permanent_broker_error_marks_event_failed(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    with pytest.raises(outbox_service.OutboxPermanentFailureError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=PermanentFailingMessageBroker(),
        )

    event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == submission.job.id)
    )

    assert event is not None
    assert event.attempts == 1
    assert event.failed_at is not None
    assert event.published_at is None

    assert event.last_error == ("Invalid broker message")


def test_poison_event_does_not_block_later_events(
    db_session: Session,
) -> None:
    poison_event = OutboxEvent(
        event_type="unsupported.event",
        event_version=1,
        aggregate_type="unknown",
        aggregate_id=uuid4(),
        payload={},
    )

    db_session.add(poison_event)
    db_session.commit()
    db_session.refresh(poison_event)

    user = create_user(db_session)

    submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Test report",
            "content": "Test report content",
            "format": "pdf",
        },
    )

    broker = RecordingMessageBroker()

    with pytest.raises(outbox_service.OutboxPermanentFailureError):
        outbox_service.publish_next_outbox_event(
            db_session,
            broker=broker,
        )

    db_session.refresh(poison_event)

    assert poison_event.failed_at is not None

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True

    assert len(broker.messages) == 1

    assert broker.messages[0].aggregate_id == submission.job.id


def test_scheduled_retry_does_not_block_ready_event(
    db_session: Session,
) -> None:
    user = create_user(db_session)

    first_submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "First report",
            "content": "First content",
            "format": "pdf",
        },
    )

    second_submission = job_service.submit_job(
        db_session,
        user_id=user.id,
        idempotency_key=f"test-{uuid4().hex}",
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": "Second report",
            "content": "Second content",
            "format": "pdf",
        },
    )

    first_event = db_session.scalar(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == first_submission.job.id)
    )

    assert first_event is not None

    first_event.available_at = datetime.now(UTC) + timedelta(hours=1)

    db_session.commit()

    broker = RecordingMessageBroker()

    published = outbox_service.publish_next_outbox_event(
        db_session,
        broker=broker,
    )

    assert published is True

    assert broker.messages[0].aggregate_id == second_submission.job.id
