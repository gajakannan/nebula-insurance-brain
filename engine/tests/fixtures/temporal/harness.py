"""F0008 PostgreSQL harness: owned database per test, migrated to head.

Builds on the F0007 FactSlot world. It adds evidence documents whose dates come
from F0004 date selections (seeded as rows; the F0022 producer does not exist
yet) and `fact-temporal/v1` commit and read helpers. It never touches the
shared development database. Requires `BRAIN_MIGRATION_ADMIN_URL`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic import command
from brain_testing import fixtures
from brain_testing.factslots import AGGREGATE_LIMIT
from engine.tests.fixtures.factslots import harness as f0007
from sqlalchemy.orm import Session

_clean_fact_tables = f0007._clean_fact_tables
database = f0007.database
configuration = f0007.configuration

ENVELOPE = "fact-answer/v1"
CHICAGO = "America/Chicago"


def money(amount: str) -> dict[str, Any]:
    return {
        "answer_contract": ENVELOPE,
        "state": "PRESENT",
        "value": {"type": "money", "amount": amount, "currency": "USD"},
    }


def bound(instant: str, granularity: str = "DAY", zone: str = CHICAGO) -> dict[str, str]:
    return {"instant": instant, "granularity": granularity, "zone": zone}


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TemporalWorld(f0007.FactSlotWorld):
    def __init__(self, url: str) -> None:
        super().__init__(url)
        with Session(self.sync_engine) as session, session.begin():
            self.dater = fixtures.seed_principal(
                session, issuer="urn:f0008:test", subject=f"dater-{uuid4()}"
            )

    async def slot(self, predicate=AGGREGATE_LIMIT, owner=None, **kwargs: Any) -> UUID:  # type: ignore[no-untyped-def]
        owner = owner or self.a
        result = await self.resolve(
            self.key(owner, predicate, subject=self.entity(owner), **kwargs), owner=owner
        )
        assert result.outcome == "CREATED", result
        return result.slot_id

    # --- evidence documents and F0004 date selections ----------------------

    def evidence(
        self,
        date: tuple[str, str] | None = None,
        *,
        owner: f0007.Owner | None = None,
        **restrictions: object,
    ) -> UUID:
        """A legacy assertion evidence row on its own document. `date` is
        `(value, precision)` and becomes the document's current selection."""
        owner = owner or self.a
        artifact = self.artifact(owner, **restrictions)
        evidence_id, assertion_id = uuid4(), uuid4()
        with self._sql() as connection:
            connection.execute(
                "INSERT INTO assertion (id, origin, version, subject_type, slot_type, value, "
                "interpretation_basis, tenant_id, knowledge_base_id, semantic_contract_version) "
                "VALUES (%s, 'MACHINE_EXTRACTION', 1, 'Policy', 'each_occurrence_limit', "
                "'{}'::jsonb, 'EXPLICIT', %s, %s, 1)",
                (assertion_id, owner.tenant_id, owner.knowledge_base_id),
            )
            connection.execute(
                "INSERT INTO assertion_evidence (id, assertion_id, artifact_id, precision, "
                "tenant_id, knowledge_base_id) VALUES (%s, %s, %s, 'block', %s, %s)",
                (evidence_id, assertion_id, artifact, owner.tenant_id, owner.knowledge_base_id),
            )
        self._artifacts = getattr(self, "_artifacts", {})
        self._artifacts[evidence_id] = (artifact, owner)
        if date is not None:
            self.select_date(evidence_id, date)
        return evidence_id

    def artifact_of(self, evidence_id: UUID) -> UUID:
        return self._artifacts[evidence_id][0]

    def select_date(self, evidence_id: UUID, date: tuple[str, str] | None) -> None:
        """Append a selection for the evidence's document version: a date, or a
        clear when `date` is None (F0004 semantics: the latest sequence wins)."""
        artifact, owner = self._artifacts[evidence_id]
        scope = (owner.tenant_id, owner.knowledge_base_id)
        with self._sql() as connection:
            version = connection.execute(
                "SELECT document_version_id FROM content_artifact WHERE id = %s", (artifact,)
            ).fetchone()[0]
            audit = uuid4()
            connection.execute(
                "INSERT INTO audit_event (id, actor_principal_id, resource_type, resource_id, "
                "action, decision, reason_code, policy_hash, grant_revision, trace_id) "
                "VALUES (%s, %s, 'content_artifact', %s, 'interpret', true, 'ALLOWED', "
                "'f0008-fixture', 1, 'f0008-fixture')",
                (audit, self.dater.id, artifact),
            )
            candidate = None
            if date is not None:
                candidate = uuid4()
                basis = {"kind": "HUMAN", "fixture": "f0008"}
                connection.execute(
                    "INSERT INTO document_date_candidate (id, document_version_id, tenant_id, "
                    "knowledge_base_id, date_value, date_precision, basis_kind, basis, "
                    "idempotency_key, request_sha256, actor_principal_id, "
                    "authorization_decision_id, authorization_audit_event_id) VALUES "
                    "(%s, %s, %s, %s, %s, %s, 'HUMAN', %s::jsonb, %s, %s, %s, %s, %s)",
                    (
                        candidate,
                        version,
                        *scope,
                        date[0],
                        date[1],
                        json.dumps(basis),
                        f"f0008-{candidate}",
                        _sha(candidate),
                        self.dater.id,
                        uuid4(),
                        audit,
                    ),
                )
            previous = connection.execute(
                "SELECT id, sequence FROM document_date_selection WHERE document_version_id = %s "
                "ORDER BY sequence DESC LIMIT 1",
                (version,),
            ).fetchone()
            selection = uuid4()
            connection.execute(
                "INSERT INTO document_date_selection (id, document_version_id, tenant_id, "
                "knowledge_base_id, candidate_id, previous_selection_id, human_decision_id, "
                "human_actor_principal_id, human_authorization_decision_id, human_decided_at, "
                "human_receipt_sha256, sequence, reason, idempotency_key, request_sha256, "
                "actor_principal_id, authorization_decision_id, authorization_audit_event_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s, 'f0008 fixture', "
                "%s, %s, %s, %s, %s)",
                (
                    selection,
                    version,
                    *scope,
                    candidate,
                    previous[0] if previous else None,
                    uuid4(),
                    self.dater.id,
                    uuid4(),
                    _sha(selection),
                    (previous[1] + 1) if previous else 1,
                    f"f0008-{selection}",
                    _sha(selection),
                    self.dater.id,
                    uuid4(),
                    audit,
                ),
            )

    def _sql(self):  # type: ignore[no-untyped-def]
        import psycopg

        return psycopg.connect(self.url)

    # --- fact-temporal/v1 commit and read ----------------------------------

    def body(
        self,
        value: dict[str, Any],
        *,
        start: dict[str, str] | None = None,
        basis: str | None = "TEMPLATE_FIELD",
        end_state: str = "OPEN",
        end: dict[str, str] | None = None,
        attestation_zone: str | None = None,
        evidence: list[UUID] | tuple[UUID, ...] = (),
        ending: list[UUID] | tuple[UUID, ...] = (),
        expected: dict[str, Any] | None = None,
        received: str = "2026-06-12T14:00:00Z",
        expected_current: UUID | None = None,
        temporal: dict[str, Any] | None = None,
        change_reason: str | None = None,
    ) -> dict[str, Any]:
        block: dict[str, Any] = {"contract": "fact-temporal/v1", "valid_to_state": end_state}
        if start is not None:
            block["valid_from"] = start
            if basis is not None:
                block["valid_from_basis"] = basis
        if end is not None:
            block["valid_to"] = end
        if attestation_zone is not None:
            block["attestation_zone"] = attestation_zone
        if ending:
            block["ending_evidence_refs"] = [str(e) for e in ending]
        if expected is not None:
            block["expected_attestation"] = expected
        return {
            "value": value,
            "temporal": temporal if temporal is not None else block,
            "change_reason": change_reason,
            "evidence_refs": [str(e) for e in evidence],
            "review_decision_id": None,
            "source_received_at": received,
            "artifact_created_at": received,
            "assertion_created_at": received,
            "expected_current_version_id": str(expected_current) if expected_current else None,
            "idempotency_key": f"f0008-{uuid4()}",
        }

    async def post(self, slot_id: UUID, body: dict[str, Any], *, principal=None):  # type: ignore[no-untyped-def]
        async with self.client(principal or self.service) as client:
            return await client.post(f"/facts/{slot_id}/commits", json=body)

    async def commit_v1(self, slot_id: UUID, value: dict[str, Any], *, principal=None, **kw: Any):  # type: ignore[no-untyped-def]
        return await self.post(slot_id, self.body(value, **kw), principal=principal)

    async def read(  # type: ignore[no-untyped-def]
        self, slot_id: UUID, valid: str | None = None, known: str | None = None, *, principal=None
    ):
        params = {}
        if valid is not None:
            params["validAsOf"] = valid
        if known is not None:
            params["knownAsOf"] = known
        async with self.client(principal or self.service) as client:
            return await client.get(f"/facts/{slot_id}", params=params)

    async def commit_at(self, slot_id: UUID, body: dict[str, Any], accepted: str, *, repo=None):  # type: ignore[no-untyped-def]
        """Run the commit service directly with a fixed acceptance clock, inside
        one unit of work, as `test_bitemporal_commit` does. Authorization is the
        API's job and is proven through `post`; this proves recorded time."""
        from brain_domain.facts import ChangeReason, CommitProposal
        from brain_factslots.answers import FactAnswerPolicy
        from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
        from brain_persistence.repositories import SqlAlchemyFactCommitRepository
        from brain_temporal.commit import CanonicalCommitService
        from sqlalchemy.ext.asyncio import AsyncSession

        proposal = CommitProposal(
            slot_id=slot_id,
            value=body["value"],
            valid_from=None,
            valid_to=None,
            change_reason=ChangeReason(body["change_reason"]) if body["change_reason"] else None,
            evidence_refs=tuple(UUID(e) for e in body["evidence_refs"]),
            review_decision_id=None,
            source_received_at=at(body["source_received_at"]),
            artifact_created_at=at(body["artifact_created_at"]),
            assertion_created_at=at(body["assertion_created_at"]),
            expected_current_version_id=(
                UUID(body["expected_current_version_id"])
                if body["expected_current_version_id"]
                else None
            ),
            idempotency_key=body["idempotency_key"],
            temporal=body["temporal"],
        )
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            repository = repo(session) if repo else SqlAlchemyFactCommitRepository(session)
            service = CanonicalCommitService(
                repository,
                clock=lambda: at(accepted),
                answer_policy=FactAnswerPolicy(self.registry, SqlAlchemyFactSlotStore(session)),
            )
            try:
                result = await service.commit(
                    proposal, authorized_scope=self.a.scope, authorization_decision_id=None
                )
                await session.commit()
            except BaseException:
                await session.rollback()
                raise
            return result

    def versions(self, slot_id: UUID) -> list[dict[str, Any]]:
        rows = self.rows(
            "SELECT to_jsonb(v) FROM canonical_fact_version v WHERE slot_id = %s "
            "ORDER BY lower(valid), lower(recorded)",
            slot_id,
        )
        return [row[0] for row in rows]

    def changes(self, slot_id: UUID) -> list[tuple[Any, ...]]:
        return self.rows(
            "SELECT c.reason, c.from_version_id, c.to_version_id FROM canonical_fact_change c "
            "JOIN canonical_fact_version v ON v.id = c.to_version_id WHERE v.slot_id = %s "
            "ORDER BY c.created_at, c.reason",
            slot_id,
        )


def _sha(value: object) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()


def now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
async def world(database):  # type: ignore[no-untyped-def]
    command.upgrade(configuration(), "head")
    w = TemporalWorld(database)
    try:
        yield w
    finally:
        await w.close()
