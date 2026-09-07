from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ApiKey, User
from app.security.api_keys import (
    create_api_key_digest,
    generate_api_key,
)

API_KEY_ID_UNIQUE_CONSTRAINT = "api_keys_key_id_key"
MAX_API_KEY_GENERATION_ATTEMPTS = 3


class APIKeyOwnerNotFoundError(LookupError):
    pass


class InvalidAPIKeyNameError(ValueError):
    pass


class InvalidAPIKeyExpirationError(ValueError):
    pass


class APIKeyGenerationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProvisionedAPIKey:
    api_key: ApiKey
    raw_key: str = field(repr=False)


def _normalize_name(name: str) -> str:
    normalized_name = name.strip()

    if not normalized_name:
        raise InvalidAPIKeyNameError("El nombre de la API Key no puede estar vacío")

    if len(normalized_name) > 100:
        raise InvalidAPIKeyNameError(
            "El nombre de la API Key no puede superar los 100 caracteres"
        )

    return normalized_name


def _validate_expiration(
    expires_at: datetime | None,
) -> None:
    if expires_at is None:
        return

    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise InvalidAPIKeyExpirationError("expires_at debe incluir zona horaria")

    if expires_at <= datetime.now(UTC):
        raise InvalidAPIKeyExpirationError("expires_at debe estar en el futuro")


def _is_key_id_collision(
    exc: IntegrityError,
) -> bool:
    diag = getattr(exc.orig, "diag", None)

    return (
        getattr(exc.orig, "sqlstate", None) == "23505"
        and getattr(
            diag,
            "constraint_name",
            None,
        )
        == API_KEY_ID_UNIQUE_CONSTRAINT
    )


def provision_api_key(
    db: Session,
    *,
    user_id: int,
    name: str,
    pepper: str,
    expires_at: datetime | None = None,
) -> ProvisionedAPIKey:
    user = db.get(User, user_id)

    if user is None:
        raise APIKeyOwnerNotFoundError("Usuario no encontrado")

    normalized_name = _normalize_name(name)

    _validate_expiration(expires_at)

    for _ in range(MAX_API_KEY_GENERATION_ATTEMPTS):
        generated = generate_api_key()

        key_digest = create_api_key_digest(
            generated.raw_key,
            pepper,
        )

        api_key = ApiKey(
            user_id=user_id,
            name=normalized_name,
            key_id=generated.key_id,
            key_digest=key_digest,
            expires_at=expires_at,
        )

        db.add(api_key)

        try:
            db.commit()

        except IntegrityError as exc:
            db.rollback()

            if _is_key_id_collision(exc):
                continue

            raise

        db.refresh(api_key)

        return ProvisionedAPIKey(
            api_key=api_key,
            raw_key=generated.raw_key,
        )

    raise APIKeyGenerationError("No fue posible generar un key_id único")
