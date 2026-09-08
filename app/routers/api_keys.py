from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_scopes
from app.api.errors import (
    APIError,
    ErrorCode,
    ErrorResponse,
)
from app.config import settings
from app.database import get_db
from app.schemas import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyResponse,
)
from app.security.scopes import APIKeyScope
from app.services import api_keys as api_key_service
from app.services.api_keys import AuthenticatedAPIKey

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


APIKeysReader = Annotated[
    AuthenticatedAPIKey,
    Depends(
        require_scopes(
            APIKeyScope.API_KEYS_READ,
        )
    ),
]

APIKeysWriter = Annotated[
    AuthenticatedAPIKey,
    Depends(
        require_scopes(
            APIKeyScope.API_KEYS_WRITE,
        )
    ),
]


APIKeyId = Annotated[
    str,
    Path(
        min_length=24,
        max_length=24,
        pattern=r"^[0-9a-f]{24}$",
    ),
]


@router.post(
    "",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    description=(
        "Crea una API Key para el usuario autenticado. "
        "Requiere el scope `api-keys:write`."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "API Key creation error",
        },
    },
)
def create_api_key(
    api_key_data: APIKeyCreate,
    current_api_key: APIKeysWriter,
    db: DbSession,
) -> APIKeyCreatedResponse:
    requested_scopes = {scope.value for scope in api_key_data.scopes}

    missing_scopes = sorted(requested_scopes - current_api_key.scopes)

    if missing_scopes:
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.INSUFFICIENT_SCOPE,
            message="La API Key no puede delegar scopes que no posee",
            details=[
                {
                    "missing_scopes": missing_scopes,
                }
            ],
        )

    try:
        result = api_key_service.provision_api_key(
            db,
            user_id=current_api_key.user_id,
            name=api_key_data.name,
            pepper=settings.api_key_pepper.get_secret_value(),
            expires_at=api_key_data.expires_at,
            scopes=api_key_data.scopes,
        )

    except (
        api_key_service.InvalidAPIKeyNameError,
        api_key_service.InvalidAPIKeyExpirationError,
    ) as exc:
        raise APIError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ErrorCode.VALIDATION_ERROR,
            message="Los datos enviados no son válidos",
            details=[
                {
                    "field": "body",
                    "message": str(exc),
                    "type": "value_error",
                }
            ],
        ) from exc

    except api_key_service.APIKeyGenerationError as exc:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.API_KEY_CREATION_FAILED,
            message="No fue posible crear la API Key",
        ) from exc

    return APIKeyCreatedResponse(
        key_id=result.api_key.key_id,
        name=result.api_key.name,
        scopes=[APIKeyScope(scope) for scope in result.api_key.scopes],
        created_at=result.api_key.created_at,
        expires_at=result.api_key.expires_at,
        revoked_at=result.api_key.revoked_at,
        last_used_at=result.api_key.last_used_at,
        api_key=result.raw_key,
    )


@router.get(
    "",
    response_model=list[APIKeyResponse],
    description=(
        "Lista las API Keys del usuario autenticado. Requiere el scope `api-keys:read`."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        }
    },
)
def get_api_keys(
    current_api_key: APIKeysReader,
    db: DbSession,
) -> list[APIKeyResponse]:
    return [
        APIKeyResponse.model_validate(api_key)
        for api_key in api_key_service.list_api_keys(
            db,
            user_id=current_api_key.user_id,
        )
    ]


@router.post(
    "/{key_id}/revoke",
    response_model=APIKeyResponse,
    description=(
        "Revoca una API Key del usuario autenticado. "
        "Requiere el scope `api-keys:write`."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "API Key not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "API Key already revoked",
        },
    },
)
def revoke_api_key(
    key_id: APIKeyId,
    current_api_key: APIKeysWriter,
    db: DbSession,
) -> APIKeyResponse:
    try:
        api_key = api_key_service.revoke_api_key(
            db,
            user_id=current_api_key.user_id,
            key_id=key_id,
        )

    except api_key_service.APIKeyNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.API_KEY_NOT_FOUND,
            message="API Key no encontrada",
        ) from exc

    except api_key_service.APIKeyAlreadyRevokedError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.API_KEY_ALREADY_REVOKED,
            message="API Key ya revocada",
        ) from exc

    return APIKeyResponse.model_validate(api_key)
