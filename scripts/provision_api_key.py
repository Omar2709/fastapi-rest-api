import argparse
import sys
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.database import SessionLocal
from app.services.api_keys import (
    APIKeyGenerationError,
    APIKeyOwnerNotFoundError,
    InvalidAPIKeyExpirationError,
    InvalidAPIKeyNameError,
    provision_api_key,
)


def positive_integer(value: str) -> int:
    parsed_value = int(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("El valor debe ser mayor que cero")

    return parsed_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision an API Key for an existing user"
    )

    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--name",
        required=True,
    )

    parser.add_argument(
        "--expires-in-days",
        type=positive_integer,
        default=None,
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    expires_at = None

    if args.expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=args.expires_in_days)

    with SessionLocal() as db:
        try:
            result = provision_api_key(
                db,
                user_id=args.user_id,
                name=args.name,
                pepper=(settings.api_key_pepper.get_secret_value()),
                expires_at=expires_at,
            )

        except (
            APIKeyGenerationError,
            APIKeyOwnerNotFoundError,
            InvalidAPIKeyExpirationError,
            InvalidAPIKeyNameError,
        ) as exc:
            print(
                f"Error: {exc}",
                file=sys.stderr,
            )

            return 1

    print("API Key creada correctamente.")
    print(f"Key ID: {result.api_key.key_id}")
    print()
    print("API Key (se mostrará una sola vez):")
    print(result.raw_key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
