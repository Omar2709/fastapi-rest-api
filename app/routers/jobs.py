from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_scopes
from app.api.errors import (
    APIError,
    ErrorCode,
    ErrorResponse,
)
from app.database import get_db
from app.domain.idempotency import (
    IDEMPOTENCY_KEY_MAX_LENGTH,
    IDEMPOTENCY_KEY_PATTERN,
)
from app.schemas import (
    JobAcceptedResponse,
    JobDetailResponse,
    JobSubmit,
    JobSummaryResponse,
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


JobsReader = Annotated[
    AuthenticatedAPIKey,
    Depends(require_scopes(APIKeyScope.JOBS_READ)),
]


JobId = Annotated[
    UUID,
    Path(
        description="Identificador UUID del Job",
    ),
]


JobListLimit = Annotated[
    int,
    Query(
        ge=1,
        le=100,
        description=("Número máximo de Jobs a devolver"),
    ),
]


JobListOffset = Annotated[
    int,
    Query(
        ge=0,
        description=("Número de Jobs a omitir"),
    ),
]


IdempotencyKeyHeader = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=IDEMPOTENCY_KEY_MAX_LENGTH,
        pattern=IDEMPOTENCY_KEY_PATTERN,
        description=("Identificador único y opaco de la operación de submit."),
    ),
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
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Idempotency key conflict",
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
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
) -> JobAcceptedResponse:
    try:
        submission = job_service.submit_job(
            db,
            user_id=current_api_key.user_id,
            idempotency_key=idempotency_key,
            job_type=job_data.job_type,
            payload=job_data.payload.model_dump(mode="json"),
        )

    except job_service.IdempotencyKeyConflictError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code=(ErrorCode.IDEMPOTENCY_KEY_CONFLICT),
            message=("La Idempotency-Key ya fue utilizada con una solicitud diferente"),
        ) from exc

    job = submission.job

    response.headers["Location"] = f"/api/v1/jobs/{job.id}"

    response.headers["Cache-Control"] = "no-store"

    response.headers["Idempotency-Replayed"] = (
        "true" if submission.replayed else "false"
    )

    return JobAcceptedResponse.model_validate(job)


@router.get(
    "",
    response_model=list[JobSummaryResponse],
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
        "Lista los Jobs pertenecientes al "
        "usuario autenticado. "
        "Requiere el scope `jobs:read`."
    ),
)
def get_jobs(
    current_api_key: JobsReader,
    db: DbSession,
    response: Response,
    limit: JobListLimit = 20,
    offset: JobListOffset = 0,
) -> list[JobSummaryResponse]:
    jobs = job_service.list_jobs(
        db,
        user_id=current_api_key.user_id,
        limit=limit,
        offset=offset,
    )

    response.headers["Cache-Control"] = "no-store"

    return [JobSummaryResponse.model_validate(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication error",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Insufficient scope",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Job not found",
        },
    },
    description=(
        "Obtiene el estado y detalle de un Job "
        "perteneciente al usuario autenticado. "
        "Requiere el scope `jobs:read`."
    ),
)
def get_job(
    job_id: JobId,
    current_api_key: JobsReader,
    db: DbSession,
    response: Response,
) -> JobDetailResponse:
    try:
        job = job_service.get_job(
            db,
            user_id=current_api_key.user_id,
            job_id=job_id,
        )

    except job_service.JobNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.JOB_NOT_FOUND,
            message="Job no encontrado",
        ) from exc

    response.headers["Cache-Control"] = "no-store"

    return JobDetailResponse.model_validate(job)
