"""Serialize trusted submissions without changing queue publication lock order."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from brain_content.validation import sha256
from sqlalchemy import text
from sqlalchemy.engine import Engine


@contextmanager
def source_submission(
    engine: Engine, tenant_id: UUID, knowledge_base_id: UUID, source_sha256: str
) -> Iterator[None]:
    # This namespace is used only by submitters. Publishers never wait on it,
    # so enqueue may wait for an artifact lease without reversing the existing
    # publication order (job -> authority -> source/version -> artifact).
    identity = f"submission:{tenant_id}:{knowledge_base_id}:{source_sha256}"
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            lock_id = int.from_bytes(bytes.fromhex(sha256(identity.encode()))[:8], signed=True)
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})
        yield
