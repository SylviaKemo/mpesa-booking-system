from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base, EnumValue, UtcDateTime

# Importing the models package registers every model on Base.metadata, which is
# what autogenerate compares against. Models arrive in the next slice.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Single source of truth: the URL comes from settings, never from alembic.ini.
# The value passes through ConfigParser interpolation, so a literal % — which a
# percent-encoded password contains, e.g. %40 for @ — must be escaped or every
# Alembic command raises ValueError.
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

target_metadata = Base.metadata


def render_item(type_: str, obj: object, autogen_context: object) -> str | bool:
    """
    Render custom column types as the database type they actually create.

    Autogenerate otherwise emits `app.database.EnumValue(length=12)` — which
    neither imports app.database nor passes the enum class the constructor
    requires, so the migration fails to import. A migration describes the
    schema, and in the database these are plain VARCHAR and DATETIME.
    """
    if type_ == "type":
        if isinstance(obj, UtcDateTime):
            return "sa.DateTime()"
        if isinstance(obj, EnumValue):
            return f"sa.String(length={obj.impl.length})"
    return False


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        render_item=render_item,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and run migrations against the live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            # SQLite cannot ALTER most things in place; batch mode rewrites the
            # table instead, so the same migrations run on SQLite and Postgres.
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
