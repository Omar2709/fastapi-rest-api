import hashlib
import hmac
import secrets
from dataclasses import dataclass

API_KEY_PREFIX = "fapi"
API_KEY_ID_BYTES = 12
API_KEY_SECRET_BYTES = 32


class InvalidAPIKeyFormatError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GeneratedAPIKey:
    key_id: str
    raw_key: str


def generate_api_key() -> GeneratedAPIKey:
    key_id = secrets.token_hex(API_KEY_ID_BYTES)
    secret = secrets.token_urlsafe(API_KEY_SECRET_BYTES)

    raw_key = f"{API_KEY_PREFIX}_{key_id}_{secret}"

    return GeneratedAPIKey(
        key_id=key_id,
        raw_key=raw_key,
    )


def extract_api_key_id(raw_key: str) -> str:
    parts = raw_key.split("_", 2)

    if len(parts) != 3:
        raise InvalidAPIKeyFormatError("Invalid API key format")

    prefix, key_id, secret = parts

    if prefix != API_KEY_PREFIX:
        raise InvalidAPIKeyFormatError("Invalid API key prefix")

    expected_key_id_length = API_KEY_ID_BYTES * 2

    if len(key_id) != expected_key_id_length or any(
        character not in "0123456789abcdef" for character in key_id
    ):
        raise InvalidAPIKeyFormatError("Invalid API key identifier")

    if not secret:
        raise InvalidAPIKeyFormatError("Invalid API key secret")

    return key_id


def create_api_key_digest(
    raw_key: str,
    pepper: str,
) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_api_key(
    raw_key: str,
    expected_digest: str,
    pepper: str,
) -> bool:
    actual_digest = create_api_key_digest(
        raw_key,
        pepper,
    )

    return hmac.compare_digest(
        actual_digest,
        expected_digest,
    )
