from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


TERMINAL_JOB_STATUSES = frozenset(
    {
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
    }
)


ALLOWED_JOB_TRANSITIONS = {
    JobStatus.PENDING: frozenset(
        {
            JobStatus.QUEUED,
        }
    ),
    JobStatus.QUEUED: frozenset(
        {
            JobStatus.RUNNING,
        }
    ),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
        }
    ),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
}


class InvalidJobTransitionError(ValueError):
    def __init__(
        self,
        current_status: JobStatus,
        target_status: JobStatus,
    ) -> None:
        self.current_status = current_status
        self.target_status = target_status

        super().__init__(
            "Transición de Job no permitida: "
            f"{current_status.value} -> "
            f"{target_status.value}"
        )


def can_transition_job(
    current_status: JobStatus,
    target_status: JobStatus,
) -> bool:
    return target_status in ALLOWED_JOB_TRANSITIONS[current_status]


def ensure_job_transition(
    current_status: JobStatus,
    target_status: JobStatus,
) -> None:
    if not can_transition_job(
        current_status,
        target_status,
    ):
        raise InvalidJobTransitionError(
            current_status,
            target_status,
        )


def is_terminal_job_status(
    status: JobStatus,
) -> bool:
    return status in TERMINAL_JOB_STATUSES
