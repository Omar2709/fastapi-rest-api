import json
from collections.abc import Mapping
from hashlib import sha256
from typing import Any

from app.domain.jobs import JobType

IDEMPOTENCY_KEY_MAX_LENGTH = 128

IDEMPOTENCY_KEY_PATTERN = r"^[A-Za-z0-9._:-]+$"

JOB_SUBMISSION_FINGERPRINT_NAMESPACE = "jobs.submit.v1"


def create_job_submission_fingerprint(
    *,
    job_type: JobType,
    payload: Mapping[str, Any],
) -> str:
    canonical_request = json.dumps(
        {
            "job_type": job_type.value,
            "payload": dict(payload),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    fingerprint_input = (
        f"{JOB_SUBMISSION_FINGERPRINT_NAMESPACE}\n{canonical_request}"
    ).encode()

    return sha256(fingerprint_input).hexdigest()
