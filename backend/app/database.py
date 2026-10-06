from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread is a SQLite-only concern: FastAPI serves sync endpoints from
# a threadpool, and SQLite otherwise refuses connections across threads.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.is_sqlite else {},
    pool_pre_ping=True,
)

if settings.is_sqlite:

    @event.listens_for(engine, "connect")
    def _enforce_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        """
        SQLite ignores foreign keys unless asked, per connection.

        Without this, a dangling foreign key is accepted in development and
        rejected by Postgres in production — the schema would be enforced in
        one environment and not the other.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base all models inherit from. Alembic autogenerates off this."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
