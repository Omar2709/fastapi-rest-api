from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models
from app.config import settings
from app.database import Base, get_db
from app.main import app


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
        for table in reversed(
            Base.metadata.sorted_tables
        ):
            session.execute(table.delete())

        session.commit()

        yield session

        session.rollback()

        for table in reversed(
            Base.metadata.sorted_tables
        ):
            session.execute(table.delete())

        session.commit()


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

    app.dependency_overrides[get_db] = (
        override_get_db
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()