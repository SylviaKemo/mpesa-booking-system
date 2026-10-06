import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Point the app at a throwaway SQLite file before anything imports settings,
# so tests never touch a developer's real database.
_tmp_dir = tempfile.mkdtemp(prefix="shamim-test-")
_db_path = Path(_tmp_dir) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["ENVIRONMENT"] = "development"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Generator[None, None, None]:
    """Build the schema once for the test session, then tear it down."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client
