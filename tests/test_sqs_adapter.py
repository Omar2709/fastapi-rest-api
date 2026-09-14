import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError

from app.adapters.aws.sqs import (
    MAX_SQS_MESSAGE_BYTES,
    InvalidMessageEnvelopeError,
    SQSMessageBroker,
    SQSMessageTooLargeError,
    serialize_message_envelope,
)
from app.ports.message_broker import (
    MessageBrokerError,
    MessageEnvelope,
)


class RecordingSQSClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def send_message(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.calls.append(kwargs)

        return {"MessageId": "test-message-id"}


class FailingSQSClient:
    def send_message(
        self,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        raise ClientError(
            {
                "Error": {
                    "Code": ("ServiceUnavailable"),
                    "Message": ("Temporary failure"),
                }
            },
            "SendMessage",
        )


def create_message() -> MessageEnvelope:
    return MessageEnvelope(
        event_id=uuid4(),
        event_type="job.submitted",
        event_version=1,
        aggregate_type="job",
        aggregate_id=uuid4(),
        occurred_at=datetime(
            2026,
            9,
            13,
            20,
            30,
            tzinfo=UTC,
        ),
        payload={
            "job_type": "generate_report",
        },
    )


def test_message_envelope_serializes_to_json() -> None:
    message = create_message()

    body = serialize_message_envelope(message)

    data = json.loads(body)

    assert data == {
        "event_id": str(message.event_id),
        "event_type": "job.submitted",
        "event_version": 1,
        "aggregate_type": "job",
        "aggregate_id": str(message.aggregate_id),
        "occurred_at": ("2026-09-13T20:30:00Z"),
        "payload": {
            "job_type": "generate_report",
        },
    }


def test_sqs_broker_sends_serialized_message() -> None:
    client = RecordingSQSClient()

    broker = SQSMessageBroker(
        client=client,
        queue_url=("https://example.invalid/test-queue"),
    )

    message = create_message()

    broker.publish(message)

    assert len(client.calls) == 1

    call = client.calls[0]

    assert call["QueueUrl"] == ("https://example.invalid/test-queue")

    body = json.loads(call["MessageBody"])

    assert body["event_id"] == str(message.event_id)

    assert body["aggregate_id"] == str(message.aggregate_id)


def test_sqs_error_becomes_message_broker_error() -> None:
    broker = SQSMessageBroker(
        client=FailingSQSClient(),
        queue_url=("https://example.invalid/test-queue"),
    )

    with pytest.raises(MessageBrokerError) as exc_info:
        broker.publish(create_message())

    assert str(exc_info.value) == ("Amazon SQS no pudo aceptar el mensaje")


def test_sqs_broker_rejects_oversized_message() -> None:
    message = create_message()

    oversized_message = MessageEnvelope(
        event_id=message.event_id,
        event_type=message.event_type,
        event_version=message.event_version,
        aggregate_type=message.aggregate_type,
        aggregate_id=message.aggregate_id,
        occurred_at=message.occurred_at,
        payload={
            "data": ("x" * MAX_SQS_MESSAGE_BYTES),
        },
    )

    with pytest.raises(SQSMessageTooLargeError):
        serialize_message_envelope(oversized_message)


def test_message_requires_timezone_aware_timestamp() -> None:
    message = create_message()

    invalid_message = MessageEnvelope(
        event_id=message.event_id,
        event_type=message.event_type,
        event_version=message.event_version,
        aggregate_type=message.aggregate_type,
        aggregate_id=message.aggregate_id,
        occurred_at=datetime(
            2026,
            9,
            13,
            20,
            30,
        ),
        payload=message.payload,
    )

    with pytest.raises(InvalidMessageEnvelopeError):
        serialize_message_envelope(invalid_message)
