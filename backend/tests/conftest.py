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
os.environ["MPESA_CALLBACK_SECRET"] = "test-callback-secret"
os.environ["MPESA_PROVIDER"] = "fake"

# Stop Settings reading the developer's .env. Without this the suite inherits
# whatever is configured locally: a real MPESA_PROVIDER=daraja makes tests fire
# live Safaricom requests, and a populated .env masks the cases that assert a
# value is absent. Must happen before anything constructs Settings — importing
# app.database alone is enough to do that.
from app.config import Settings  # noqa: E402

Settings.model_config["env_file"] = None

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import (  # noqa: E402
    Addition,
    Booking,
    BookingAddition,
    LashSet,
    Payment,
    Tier,
)
from app.services.mpesa import fake_provider  # noqa: E402
from app.seed import seed_catalogue  # noqa: E402

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


@pytest.fixture(autouse=True)
def _reset_mpesa() -> Generator[None, None, None]:
    """The fake provider is a module singleton, so each test starts it clean."""
    fake_provider.reset()
    yield
    fake_provider.reset()


@pytest.fixture
def mpesa() -> object:
    """The fake provider, for asserting what was sent and forcing failures."""
    return fake_provider


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded(db: Session) -> Generator[None, None, None]:
    """
    Catalogue rows, removed afterwards so tests stay independent.

    Seeds through the real seed_catalogue rather than fixtures of its own, so a
    drift between the seed data and the schema fails a test here.
    """
    seed_catalogue(db)
    yield
    # Children before parents: bookings reference tiers and additions, and the
    # foreign keys are enforced on SQLite too, so the reverse order fails.
    for model in (Payment, BookingAddition, Booking, Tier, LashSet, Addition):
        db.query(model).delete()
    db.commit()
