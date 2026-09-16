import pytest
from pydantic import ValidationError

from app.contracts.jobs import (
    MAX_REPORT_CONTENT_LENGTH,
    GenerateReportPayload,
    normalize_job_payload,
)
from app.domain.jobs import (
    JobType,
    ReportFormat,
)


def test_generate_report_payload_is_valid() -> None:
    payload = GenerateReportPayload(
        title=" Monthly sales ",
        content=" Report content ",
        format=ReportFormat.PDF,
    )

    assert payload.title == "Monthly sales"
    assert payload.content == "Report content"
    assert payload.format == ReportFormat.PDF


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "content",
    ],
)
def test_generate_report_payload_rejects_blank_text(
    field: str,
) -> None:
    data = {
        "title": "Monthly sales",
        "content": "Report content",
        "format": "pdf",
    }

    data[field] = "   "

    with pytest.raises(ValidationError):
        GenerateReportPayload.model_validate(data)


def test_generate_report_payload_rejects_unknown_format() -> None:
    with pytest.raises(ValidationError):
        GenerateReportPayload.model_validate(
            {
                "title": "Monthly sales",
                "content": "Report content",
                "format": "docx",
            }
        )


def test_generate_report_payload_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        GenerateReportPayload.model_validate(
            {
                "title": "Monthly sales",
                "content": "Report content",
                "format": "pdf",
                "unexpected": True,
            }
        )


def test_generate_report_payload_enforces_content_limit() -> None:
    with pytest.raises(ValidationError):
        GenerateReportPayload(
            title="Monthly sales",
            content="x" * (MAX_REPORT_CONTENT_LENGTH + 1),
            format=ReportFormat.PDF,
        )


def test_job_payload_normalizes_for_persistence() -> None:
    payload = normalize_job_payload(
        job_type=JobType.GENERATE_REPORT,
        payload={
            "title": " Monthly sales ",
            "content": " Report content ",
            "format": "pdf",
        },
    )

    assert payload == {
        "title": "Monthly sales",
        "content": "Report content",
        "format": "pdf",
    }
