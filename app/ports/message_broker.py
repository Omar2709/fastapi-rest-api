from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(
    frozen=True,
    slots=True,
)
class MessageEnvelope:
    event_id: UUID
    event_type: str
    event_version: int

    aggregate_type: str
    aggregate_id: UUID

    occurred_at: datetime

    payload: dict[str, Any]


class MessageBrokerError(RuntimeError):
    pass


class RetryableMessageBrokerError(MessageBrokerError):
    pass


class PermanentMessageBrokerError(MessageBrokerError):
    pass


class MessageBroker(Protocol):
    def publish(
        self,
        message: MessageEnvelope,
    ) -> None: ...
