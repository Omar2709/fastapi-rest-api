from collections.abc import Callable, Generator
from datetime import datetime
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models
from app.config import settings
from app.database import Base, get_db
from app.domain.jobs import JobType
from app.main import app
from app.models import Job
from app.services.api_keys import (
    ProvisionedAPIKey,
    provision_api_key,
)
from app.services.jobs import submit_job

TEST_DB_NAME = f"{settings.db_name}_test"

test_database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password.get_secret_value(),
    host=settings.db_host,
    port=settings.db_port,
    database=TEST_DB_NAME,
)


test_engine = create_engine(
    test_database_url,
    echo=False,
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(
    scope="session",
    autouse=True,
)
def prepare_test_database() -> Generator[None, None, None]:
    Base.metadata.create_all(
        bind=test_engine,
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine,
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())

        session.commit()

        yield session

        session.rollback()

        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())

        session.commit()


@pytest.fixture
def db_session_factory():
    return TestingSessionLocal


@pytest.fixture
def client(
    db_session: Session,
) -> Generator[TestClient, None, None]:

    def override_get_db() -> Generator[
        Session,
        None,
        None,
    ]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(
    client: TestClient,
) -> Callable[..., dict]:
    def create_user(
        name: str = "Ana",
        email: str = "ana@example.com",
    ) -> dict:
        response = client.post(
            "/api/v1/users",
            json={
                "name": name,
                "email": email,
            },
        )

        assert response.status_code == (status.HTTP_201_CREATED)

        return response.json()

    return create_user


@pytest.fixture
def task_factory(
    client: TestClient,
) -> Callable[..., dict]:
    def create_task(
        user_id: int,
        title: str = "Tarea de prueba",
        description: str | None = None,
    ) -> dict:
        response = client.post(
            f"/api/v1/users/{user_id}/tasks",
            json={
                "title": title,
                "description": description,
            },
        )

        assert response.status_code == (status.HTTP_201_CREATED)

        return response.json()

    return create_task


@pytest.fixture
def api_key_factory(
    db_session: Session,
) -> Callable[..., ProvisionedAPIKey]:
    def create_api_key(
        user_id: int,
        name: str = "Test API Key",
        expires_at: datetime | None = None,
        scopes: tuple[str, ...] = (),
    ) -> ProvisionedAPIKey:
        return provision_api_key(
            db_session,
            user_id=user_id,
            name=name,
            pepper=settings.api_key_pepper.get_secret_value(),
            max_active_keys=(settings.api_key_max_active_per_user),
            expires_at=expires_at,
            scopes=scopes,
        )

    return create_api_key


@pytest.fixture
def job_factory(
    db_session: Session,
) -> Callable[..., Job]:
    def create_job(
        *,
        user_id: int,
        job_type: JobType = JobType.GENERATE_REPORT,
        payload: dict[str, Any] | None = None,
    ) -> Job:
        job_payload = (
            payload
            if payload is not None
            else {
                "title": "Test report",
                "content": "Test report content",
                "format": "pdf",
            }
        )

        return submit_job(
            db_session,
            user_id=user_id,
            job_type=job_type,
            payload=job_payload,
        )

    return create_job
