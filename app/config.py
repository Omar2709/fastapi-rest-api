from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: SecretStr
    db_echo: bool = False

    api_key_pepper: SecretStr

    aws_region: str | None = None
    sqs_jobs_queue_url: str | None = None

    aws_connect_timeout_seconds: float = Field(
        default=2.0,
        gt=0,
    )

    aws_read_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
    )

    aws_total_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    api_key_max_active_per_user: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
