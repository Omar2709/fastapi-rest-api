from fastapi import APIRouter, status

from app.api.dependencies.auth import CurrentAPIKey
from app.api.errors import ErrorResponse
from app.schemas import AuthContextResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        }
    },
)


@router.get(
    "/me",
    response_model=AuthContextResponse,
)
def get_auth_context(
    current_api_key: CurrentAPIKey,
) -> AuthContextResponse:
    return AuthContextResponse(
        user_id=current_api_key.user_id,
        key_id=current_api_key.key_id,
        api_key_name=current_api_key.name,
        scopes=sorted(current_api_key.scopes),
    )
