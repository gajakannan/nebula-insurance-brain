"""F0003-S0003: PostgreSQL itself rejects ambiguous bitemporal state.

The write below goes straight through SQLAlchemy to the table. It does not call
CanonicalCommitService, so a passing assertion proves the exclusion constraint
is the database boundary rather than an application-only check.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from brain_persistence.models import CanonicalCommitRow, CanonicalFactVersionRow
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _range(start: str, end: str | None) -> Range[datetime]:
    lower = datetime.fromisoformat(start).replace(tzinfo=UTC)
    upper = datetime.fromisoformat(end).replace(tzinfo=UTC) if end else None
    return Range(lower, upper, bounds="[)")


def _version(
    *,
    version_id: UUID,
    slot_id: UUID,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    commit_id: UUID,
) -> CanonicalFactVersionRow:
    accepted_at = datetime(2026, 3, 1, tzinfo=UTC)
    return CanonicalFactVersionRow(
        id=version_id,
        slot_id=slot_id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        value={"amount": "1000000.00"},
        valid=_range("2026-01-01", "2026-02-01"),
        recorded=_range("2026-03-01", None),
        change_reason=None,
        evidence={"refs": []},
        review_decision_id=None,
        commit_id=commit_id,
        source_received_at=accepted_at,
        artifact_created_at=accepted_at,
        assertion_created_at=accepted_at,
        canonical_accepted_at=accepted_at,
    )


async def test_database_exclusion_rejects_overlapping_valid_and_recorded_ranges(
    pg_session_factory: async_sessionmaker[AsyncSession],
    owner: tuple[UUID, UUID],
    slot_id: UUID,
) -> None:
    tenant_id, knowledge_base_id = owner
    first_commit_id, second_commit_id = uuid4(), uuid4()

    async with pg_session_factory() as session:
        async with session.begin():
            session.add(
                CanonicalCommitRow(
                    id=first_commit_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    authorization_decision_id=None,
                    created_at=datetime(2026, 3, 1, tzinfo=UTC),
                )
            )
            await session.flush()
            session.add(
                _version(
                    version_id=uuid4(),
                    slot_id=slot_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    commit_id=first_commit_id,
                )
            )

    with pytest.raises(IntegrityError) as raised:
        async with pg_session_factory() as session:
            async with session.begin():
                session.add(
                    CanonicalCommitRow(
                        id=second_commit_id,
                        tenant_id=tenant_id,
                        knowledge_base_id=knowledge_base_id,
                        authorization_decision_id=None,
                        created_at=datetime(2026, 3, 2, tzinfo=UTC),
                    )
                )
                await session.flush()
                session.add(
                    _version(
                        version_id=uuid4(),
                        slot_id=slot_id,
                        tenant_id=tenant_id,
                        knowledge_base_id=knowledge_base_id,
                        commit_id=second_commit_id,
                    )
                )
                await session.flush()

    assert getattr(raised.value.orig, "sqlstate", None) == "23P01"

    async with pg_session_factory() as session:
        assert await session.get(CanonicalCommitRow, second_commit_id) is None
