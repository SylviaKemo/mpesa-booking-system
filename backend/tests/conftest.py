import os
import shutil
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

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import create_app  # noqa: E402

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Generator[None, None, None]:
    """
    Build the schema by running the migrations, not metadata.create_all.

    create_all builds tables straight from the models, which would let a model
    change without a matching migration pass the whole suite and only fail at
    deploy time. Migrating here keeps models and migrations honest.
    """
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))

    command.upgrade(config, "head")
    try:
        yield
    finally:
        command.downgrade(config, "base")
        # The pool keeps the SQLite file open; without disposing it first the
        # removal fails silently on Windows and the directory leaks.
        engine.dispose()
        shutil.rmtree(_tmp_dir, ignore_errors=True)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client
