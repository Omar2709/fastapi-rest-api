from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_scopes
from app.api.errors import ErrorResponse
from app.database import get_db
from app.schemas import (
    JobAcceptedResponse,
    JobSubmit,
)
from app.security.scopes import APIKeyScope
from app.services import jobs as job_service
from app.services.api_keys import AuthenticatedAPIKey

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


JobsWriter = Annotated[
    AuthenticatedAPIKey,
    Depends(require_scopes(APIKeyScope.JOBS_WRITE)),
]


@router.post(
    "",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Insufficient scope",
        },
    },
    description=(
        "Acepta un Job para procesamiento asíncrono. Requiere el scope `jobs:write`."
    ),
)
def submit_job(
    job_data: JobSubmit,
    current_api_key: JobsWriter,
    db: DbSession,
) -> JobAcceptedResponse:
    job = job_service.submit_job(
        db,
        user_id=current_api_key.user_id,
        job_type=job_data.job_type,
        payload=job_data.payload,
    )

    return JobAcceptedResponse.model_validate(job)
