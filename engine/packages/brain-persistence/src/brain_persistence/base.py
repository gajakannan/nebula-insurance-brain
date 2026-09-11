from __future__ import annotations

from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# `canonical_fact_version` uses `tstzrange` columns and a `gist` exclusion
# constraint that only compile against real Postgres — the constraint IS the
# thing F0001-S0005 proves, so it is deliberately excluded from the sqlite test
# fixture the rest of brain-persistence's tests share (see brain-temporal's own
# tests for the algorithmic proof, and the live-Postgres integration tests for
# the constraint itself). `canonical_fact_change` is excluded alongside it —
# its foreign keys reference `canonical_fact_version.id`.
_POSTGRES_ONLY_TABLES = {"canonical_fact_version", "canonical_fact_change"}


def sqlite_test_tables() -> list[Table]:
    return [t for name, t in Base.metadata.tables.items() if name not in _POSTGRES_ONLY_TABLES]
