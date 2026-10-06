import enum
from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, TypeDecorator, create_engine, event
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


class UtcDateTime(TypeDecorator):
    """
    A timestamp that is always UTC and always timezone-aware in Python.

    SQLite has no timezone-aware type, so it hands back naive values while
    Postgres hands back aware ones. Comparing a naive value against an aware
    one raises TypeError, which would make the same code work in production and
    fail in development. This normalises both ends: values are converted to UTC
    on the way in and given UTC tzinfo on the way out.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: object
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Refusing to store a naive datetime; pass an aware one.")
        return value.astimezone(timezone.utc)

    def process_result_value(
        self, value: datetime | None, dialect: object
    ) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class EnumValue(TypeDecorator):
    """
    Stores an enum by its value and gives the enum back on load.

    A plain String column annotated Mapped[SomeEnum] is a lie: the value round
    trips as str, so attribute access the annotation promises — .value, say —
    raises at runtime while a type checker waves it through. Equality survives
    only when the enum subclasses str, which hides it in tests.

    The stored text stays the member's value, so no data changes and SQL that
    matches on it, such as the partial slot index, keeps working.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class: type[enum.Enum], length: int) -> None:
        self.enum_class = enum_class
        super().__init__(length=length)

    def process_bind_param(
        self, value: enum.Enum | str | None, dialect: object
    ) -> str | None:
        if value is None:
            return None
        return self.enum_class(value).value

    def process_result_value(
        self, value: str | None, dialect: object
    ) -> enum.Enum | None:
        if value is None:
            return None
        return self.enum_class(value)


class Base(DeclarativeBase):
    """Declarative base all models inherit from. Alembic autogenerates off this."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
