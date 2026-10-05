"""Alembic environment.

Migrations run with a *synchronous* psycopg driver, derived from the app's
async ``DATABASE_URL`` by swapping the driver. Target metadata is the app's
declarative ``Base``, with all models imported so autogenerate sees them.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base

# Import models so their tables register on Base.metadata.
import app.models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url() -> str:
    """Return a synchronous SQLAlchemy URL for migrations."""
    url = get_settings().database_url
    return url.replace("+asyncpg", "+psycopg")


def include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN001
    """Ignore the DB-managed FTS generated column/index (not on the ORM model)."""
    if type_ == "column" and name == "content_tsv":
        return False
    if type_ == "index" and name == "ix_knowledge_chunks_tsv":
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _sync_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
