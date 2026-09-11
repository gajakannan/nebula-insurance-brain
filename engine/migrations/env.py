from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context

# Import every model module so its table lands on Base.metadata before autogenerate
# or a bare `context.configure(target_metadata=...)` runs.
from brain_persistence import models  # noqa: F401
from brain_persistence.base import Base
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):  # noqa: ANN001, A002
    """Exclude Apache AGE's own catalog tables (`ag_graph`, `ag_label`, ...) from
    autogenerate diffing — they live in `ag_catalog`, which `search_path` (ADR-0054
    init SQL) puts ahead of `public`, so plain reflection sees them as unmanaged
    tables in the default schema and proposes dropping them without this filter."""
    if type_ == "table" and getattr(object, "schema", None) == "ag_catalog":
        return False
    return not (type_ == "table" and name in {"ag_graph", "ag_label"})


def get_url() -> str:
    return os.environ.get(
        "BRAIN_DATABASE_URL",
        "postgresql+psycopg://brain:brain@localhost:5432/brain",
    )


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, include_object=include_object
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
