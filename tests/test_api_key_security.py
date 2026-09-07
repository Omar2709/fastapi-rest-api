import pytest

from app.security.api_keys import (
    API_KEY_PREFIX,
    InvalidAPIKeyFormatError,
    create_api_key_digest,
    extract_api_key_id,
    generate_api_key,
    verify_api_key,
)

TEST_PEPPER = "unit-test-pepper-not-a-real-production-secret"


def test_generate_api_key_uses_expected_format() -> None:
    generated = generate_api_key()

    assert generated.raw_key.startswith(f"{API_KEY_PREFIX}_{generated.key_id}_")

    assert extract_api_key_id(generated.raw_key) == generated.key_id


def test_generate_api_key_produces_unique_values() -> None:
    first = generate_api_key()
    second = generate_api_key()

    assert first.key_id != second.key_id
    assert first.raw_key != second.raw_key


def test_create_api_key_digest_does_not_store_raw_key() -> None:
    generated = generate_api_key()

    digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    assert digest != generated.raw_key
    assert len(digest) == 64


def test_api_key_digest_is_deterministic() -> None:
    generated = generate_api_key()

    first_digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    second_digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    assert first_digest == second_digest


def test_verify_api_key_accepts_valid_key() -> None:
    generated = generate_api_key()

    digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    assert verify_api_key(
        generated.raw_key,
        digest,
        TEST_PEPPER,
    )


def test_verify_api_key_rejects_modified_key() -> None:
    generated = generate_api_key()

    digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    assert not verify_api_key(
        f"{generated.raw_key}modified",
        digest,
        TEST_PEPPER,
    )


def test_verify_api_key_rejects_wrong_pepper() -> None:
    generated = generate_api_key()

    digest = create_api_key_digest(
        generated.raw_key,
        TEST_PEPPER,
    )

    assert not verify_api_key(
        generated.raw_key,
        digest,
        "different-test-pepper",
    )


@pytest.mark.parametrize(
    "raw_key",
    [
        "",
        "invalid",
        "fapi_only-two-parts",
        "wrong_123456789012345678901234_secret",
        "fapi_invalid-key-id_________secret",
        "fapi_123456789012345678901234_",
    ],
)
def test_extract_api_key_id_rejects_invalid_format(
    raw_key: str,
) -> None:
    with pytest.raises(InvalidAPIKeyFormatError):
        extract_api_key_id(raw_key)
