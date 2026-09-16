import pytest

from app.domain.jobs import (
    InvalidJobTransitionError,
    JobStatus,
    JobType,
    ReportFormat,
    can_transition_job,
    ensure_job_transition,
    is_terminal_job_status,
)


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        (
            JobStatus.PENDING,
            JobStatus.QUEUED,
        ),
        (
            JobStatus.QUEUED,
            JobStatus.RUNNING,
        ),
        (
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
        ),
        (
            JobStatus.RUNNING,
            JobStatus.FAILED,
        ),
    ],
)
def test_valid_job_transitions_are_allowed(
    current_status: JobStatus,
    target_status: JobStatus,
) -> None:
    assert can_transition_job(
        current_status,
        target_status,
    )

    ensure_job_transition(
        current_status,
        target_status,
    )


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        (
            JobStatus.PENDING,
            JobStatus.RUNNING,
        ),
        (
            JobStatus.PENDING,
            JobStatus.SUCCEEDED,
        ),
        (
            JobStatus.QUEUED,
            JobStatus.SUCCEEDED,
        ),
        (
            JobStatus.QUEUED,
            JobStatus.FAILED,
        ),
        (
            JobStatus.SUCCEEDED,
            JobStatus.RUNNING,
        ),
        (
            JobStatus.FAILED,
            JobStatus.QUEUED,
        ),
    ],
)
def test_invalid_job_transitions_are_rejected(
    current_status: JobStatus,
    target_status: JobStatus,
) -> None:
    assert not can_transition_job(
        current_status,
        target_status,
    )

    with pytest.raises(InvalidJobTransitionError) as exc_info:
        ensure_job_transition(
            current_status,
            target_status,
        )

    assert exc_info.value.current_status == current_status

    assert exc_info.value.target_status == target_status


@pytest.mark.parametrize(
    "status",
    list(JobStatus),
)
def test_job_cannot_transition_to_same_status(
    status: JobStatus,
) -> None:
    assert not can_transition_job(
        status,
        status,
    )

    with pytest.raises(InvalidJobTransitionError):
        ensure_job_transition(
            status,
            status,
        )


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
    ],
)
def test_completed_job_statuses_are_terminal(
    status: JobStatus,
) -> None:
    assert is_terminal_job_status(status)


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.PENDING,
        JobStatus.QUEUED,
        JobStatus.RUNNING,
    ],
)
def test_active_job_statuses_are_not_terminal(
    status: JobStatus,
) -> None:
    assert not is_terminal_job_status(status)


def test_job_status_values_are_stable() -> None:
    assert {status.value for status in JobStatus} == {
        "pending",
        "queued",
        "running",
        "succeeded",
        "failed",
    }


def test_job_type_values_are_stable() -> None:
    assert {job_type.value for job_type in JobType} == {
        "generate_report",
    }


def test_report_format_values_are_stable() -> None:
    assert {report_format.value for report_format in ReportFormat} == {
        "pdf",
    }
