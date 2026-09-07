from typing import Annotated

from fastapi import Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.api.errors import APIError, ErrorCode
from app.config import settings
from app.database import get_db
from app.services import api_keys as api_key_service

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description=("API Key utilizada para autenticar requests machine-to-machine."),
    auto_error=False,
)


def get_current_api_key(
    raw_key: Annotated[
        str | None,
        Depends(api_key_header),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> api_key_service.AuthenticatedAPIKey:
    authentication_headers = {"WWW-Authenticate": "APIKey"}

    if raw_key is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.API_KEY_MISSING,
            message="Se requiere una API Key",
            headers=authentication_headers,
        )

    try:
        return api_key_service.authenticate_api_key(
            db,
            raw_key=raw_key,
            pepper=(settings.api_key_pepper.get_secret_value()),
        )

    except api_key_service.InvalidAPIKeyError as exc:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.API_KEY_INVALID,
            message="API Key inválida",
            headers=authentication_headers,
        ) from exc

    except api_key_service.RevokedAPIKeyError as exc:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.API_KEY_REVOKED,
            message="API Key revocada",
            headers=authentication_headers,
        ) from exc

    except api_key_service.ExpiredAPIKeyError as exc:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.API_KEY_EXPIRED,
            message="API Key expirada",
            headers=authentication_headers,
        ) from exc

    except api_key_service.InactiveAPIKeyOwnerError as exc:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.API_KEY_OWNER_INACTIVE,
            message=("El propietario de la API Key está inactivo"),
            headers=authentication_headers,
        ) from exc


CurrentAPIKey = Annotated[
    api_key_service.AuthenticatedAPIKey,
    Depends(get_current_api_key),
]
