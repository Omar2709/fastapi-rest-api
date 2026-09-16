from collections.abc import Mapping
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from app.domain.jobs import (
    JobType,
    ReportFormat,
)

MAX_REPORT_CONTENT_LENGTH = 50_000


class InvalidJobPayloadError(ValueError):
    pass


class UnsupportedJobTypeError(ValueError):
    pass


class GenerateReportPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        min_length=1,
        max_length=MAX_REPORT_CONTENT_LENGTH,
    )

    format: ReportFormat

    @field_validator("title")
    @classmethod
    def normalize_title(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError("title no puede estar vacío")

        return value

    @field_validator("content")
    @classmethod
    def normalize_content(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError("content no puede estar vacío")

        return value


JOB_PAYLOAD_MODELS: dict[
    JobType,
    type[BaseModel],
] = {
    JobType.GENERATE_REPORT: GenerateReportPayload,
}


def normalize_job_payload(
    *,
    job_type: JobType,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload_model = JOB_PAYLOAD_MODELS.get(job_type)

    if payload_model is None:
        raise UnsupportedJobTypeError(
            f"No existe un contrato de payload para {job_type.value}"
        )

    try:
        validated_payload = payload_model.model_validate(dict(payload))

    except ValidationError as exc:
        raise InvalidJobPayloadError("El payload del Job no es válido") from exc

    return validated_payload.model_dump(mode="json")
