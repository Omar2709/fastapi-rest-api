import argparse
import sys

from app.adapters.aws.sqs import (
    create_sqs_message_broker,
)
from app.config import settings
from app.database import SessionLocal
from app.services.outbox import (
    OutboxPermanentFailureError,
    OutboxRetryScheduledError,
    publish_next_outbox_event,
)


def positive_integer(
    value: str,
) -> int:
    parsed_value = int(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("El valor debe ser mayor que cero")

    return parsed_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Publish pending Outbox events to Amazon SQS")
    )

    parser.add_argument(
        "--max-events",
        type=positive_integer,
        default=100,
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not settings.aws_region:
        print(
            "Error: AWS_REGION no está configurado",
            file=sys.stderr,
        )

        return 1

    if not settings.sqs_jobs_queue_url:
        print(
            "Error: SQS_JOBS_QUEUE_URL no está configurado",
            file=sys.stderr,
        )

        return 1

    broker = create_sqs_message_broker(
        region_name=settings.aws_region,
        queue_url=settings.sqs_jobs_queue_url,
        connect_timeout_seconds=(settings.aws_connect_timeout_seconds),
        read_timeout_seconds=(settings.aws_read_timeout_seconds),
        total_max_attempts=(settings.aws_total_max_attempts),
    )

    published_count = 0
    retry_count = 0
    failed_count = 0

    with SessionLocal() as db:
        for _ in range(args.max_events):
            try:
                published = publish_next_outbox_event(
                    db,
                    broker=broker,
                    max_attempts=(settings.outbox_max_publish_attempts),
                    retry_base_seconds=(settings.outbox_retry_base_seconds),
                    retry_max_seconds=(settings.outbox_retry_max_seconds),
                )

            except OutboxRetryScheduledError as exc:
                retry_count += 1

                print(
                    f"Retry scheduled: {exc}",
                    file=sys.stderr,
                )

                continue

            except OutboxPermanentFailureError as exc:
                failed_count += 1

                print(
                    f"Permanent failure: {exc}",
                    file=sys.stderr,
                )

                continue

            if not published:
                break

            published_count += 1

    print(
        "Outbox publishing completed. "
        f"Published: {published_count}. "
        f"Retries scheduled: "
        f"{retry_count}. "
        f"Permanent failures: "
        f"{failed_count}."
    )

    if retry_count > 0 or failed_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
