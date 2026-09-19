from __future__ import annotations

import json
from datetime import UTC
from typing import Any, Protocol, cast

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.ports.message_broker import (
    MessageEnvelope,
    PermanentMessageBrokerError,
    RetryableMessageBrokerError,
)

MAX_SQS_MESSAGE_BYTES = 1_048_576


class SQSClient(Protocol):
    def send_message(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


class InvalidMessageEnvelopeError(PermanentMessageBrokerError):
    pass


class SQSMessageTooLargeError(PermanentMessageBrokerError):
    pass


def serialize_message_envelope(
    message: MessageEnvelope,
) -> str:
    if message.occurred_at.tzinfo is None or message.occurred_at.utcoffset() is None:
        raise InvalidMessageEnvelopeError("occurred_at debe incluir zona horaria")

    occurred_at = message.occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z")

    data = {
        "event_id": str(message.event_id),
        "event_type": message.event_type,
        "event_version": message.event_version,
        "aggregate_type": message.aggregate_type,
        "aggregate_id": str(message.aggregate_id),
        "occurred_at": occurred_at,
        "payload": message.payload,
    }

    try:
        body = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    except (TypeError, ValueError) as exc:
        raise InvalidMessageEnvelopeError(
            "El MessageEnvelope no puede serializarse como JSON"
        ) from exc

    body_size = len(body.encode("utf-8"))

    if body_size > MAX_SQS_MESSAGE_BYTES:
        raise SQSMessageTooLargeError(
            "El mensaje supera el tamaño máximo permitido por Amazon SQS"
        )

    return body


class SQSMessageBroker:
    def __init__(
        self,
        *,
        client: SQSClient,
        queue_url: str,
    ) -> None:
        normalized_queue_url = queue_url.strip()

        if not normalized_queue_url:
            raise ValueError("queue_url no puede estar vacío")

        self._client = client
        self._queue_url = normalized_queue_url

    def publish(
        self,
        message: MessageEnvelope,
    ) -> None:
        body = serialize_message_envelope(message)

        try:
            self._client.send_message(
                QueueUrl=self._queue_url,
                MessageBody=body,
            )

        except (
            BotoCoreError,
            ClientError,
        ) as exc:
            raise RetryableMessageBrokerError(
                "Amazon SQS no pudo aceptar el mensaje"
            ) from exc


def create_sqs_message_broker(
    *,
    region_name: str,
    queue_url: str,
    connect_timeout_seconds: float,
    read_timeout_seconds: float,
    total_max_attempts: int,
) -> SQSMessageBroker:
    normalized_region = region_name.strip()

    if not normalized_region:
        raise ValueError("region_name no puede estar vacío")

    if total_max_attempts < 1:
        raise ValueError("total_max_attempts debe ser mayor que cero")

    config = Config(
        region_name=normalized_region,
        connect_timeout=connect_timeout_seconds,
        read_timeout=read_timeout_seconds,
        retries={
            "mode": "standard",
            "total_max_attempts": (total_max_attempts),
        },
    )

    client = cast(
        SQSClient,
        boto3.client(
            "sqs",
            config=config,
        ),
    )

    return SQSMessageBroker(
        client=client,
        queue_url=queue_url,
    )
