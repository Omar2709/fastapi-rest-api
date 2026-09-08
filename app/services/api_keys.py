from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import ApiKey, User
from app.security.api_keys import (
    InvalidAPIKeyFormatError,
    create_api_key_digest,
    extract_api_key_id,
    generate_api_key,
    verify_api_key,
)

API_KEY_ID_UNIQUE_CONSTRAINT = "api_keys_key_id_key"
MAX_API_KEY_GENERATION_ATTEMPTS = 3
DUMMY_API_KEY_DIGEST = "0" * 64

LAST_USED_UPDATE_INTERVAL = timedelta(minutes=5)


class APIKeyOwnerNotFoundError(LookupError):
    pass


class InvalidAPIKeyNameError(ValueError):
    pass


class InvalidAPIKeyExpirationError(ValueError):
    pass


class APIKeyGenerationError(RuntimeError):
    pass


class APIKeyAuthenticationError(Exception):
    pass


class InvalidAPIKeyError(APIKeyAuthenticationError):
    pass


class RevokedAPIKeyError(APIKeyAuthenticationError):
    pass


class ExpiredAPIKeyError(APIKeyAuthenticationError):
    pass


class InactiveAPIKeyOwnerError(APIKeyAuthenticationError):
    pass


class APIKeyNotFoundError(LookupError):
    pass


class APIKeyAlreadyRevokedError(RuntimeError):
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


@dataclass(frozen=True, slots=True)
class AuthenticatedAPIKey:
    id: int
    key_id: str
    user_id: int
    name: str
    last_used_at: datetime | None


def authenticate_api_key(
    db: Session,
    *,
    raw_key: str,
    pepper: str,
) -> AuthenticatedAPIKey:
    try:
        key_id = extract_api_key_id(raw_key)

    except InvalidAPIKeyFormatError as exc:
        raise InvalidAPIKeyError("API Key inválida") from exc

    api_key = db.scalar(
        select(ApiKey).options(joinedload(ApiKey.user)).where(ApiKey.key_id == key_id)
    )

    expected_digest = (
        api_key.key_digest if api_key is not None else DUMMY_API_KEY_DIGEST
    )

    is_valid = verify_api_key(
        raw_key,
        expected_digest,
        pepper,
    )

    if api_key is None or not is_valid:
        raise InvalidAPIKeyError("API Key inválida")

    now = datetime.now(UTC)

    if api_key.revoked_at is not None:
        raise RevokedAPIKeyError("API Key revocada")

    if api_key.expires_at is not None and api_key.expires_at <= now:
        raise ExpiredAPIKeyError("API Key expirada")

    if not api_key.user.is_active:
        raise InactiveAPIKeyOwnerError("El propietario de la API Key está inactivo")

    if (
        api_key.last_used_at is None
        or api_key.last_used_at <= now - LAST_USED_UPDATE_INTERVAL
    ):
        api_key.last_used_at = now
        db.commit()

    return AuthenticatedAPIKey(
        id=api_key.id,
        key_id=api_key.key_id,
        user_id=api_key.user_id,
        name=api_key.name,
        last_used_at=api_key.last_used_at,
    )


def list_api_keys(
    db: Session,
    *,
    user_id: int,
) -> list[ApiKey]:
    statement = (
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(
            ApiKey.created_at.desc(),
            ApiKey.id.desc(),
        )
    )

    return list(db.scalars(statement).all())


def revoke_api_key(
    db: Session,
    *,
    user_id: int,
    key_id: str,
) -> ApiKey:
    now = datetime.now(UTC)

    api_key_id = db.scalar(
        update(ApiKey)
        .where(
            ApiKey.user_id == user_id,
            ApiKey.key_id == key_id,
            ApiKey.revoked_at.is_(None),
        )
        .values(
            revoked_at=now,
        )
        .returning(ApiKey.id)
    )

    if api_key_id is None:
        existing_api_key = db.scalar(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.key_id == key_id,
            )
        )

        if existing_api_key is None:
            raise APIKeyNotFoundError("API Key no encontrada")

        raise APIKeyAlreadyRevokedError("API Key ya revocada")

    db.commit()

    api_key = db.get(
        ApiKey,
        api_key_id,
    )

    if api_key is None:
        raise APIKeyNotFoundError("API Key no encontrada")

    return api_key
