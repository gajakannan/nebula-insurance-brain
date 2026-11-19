from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.facts import ChangeReason, FactVersion
from brain_domain.temporal import DocumentDate, VersionTemporal
from brain_temporal.ranges import TimeRange


class FakeFactCommitRepository:
    """In-memory `FactCommitRepository` for testing `CanonicalCommitService`."""

    def __init__(self, *, tenant_id: UUID, knowledge_base_id: UUID) -> None:
        self.tenant_id = tenant_id
        self.knowledge_base_id = knowledge_base_id
        self.slots: set[UUID] = set()
        self.versions: dict[UUID, FactVersion] = {}
        self.changes: list[dict] = []
        self.outbox: list[tuple[UUID, dict]] = []
        self.commits: list[tuple[UUID, tuple[UUID, UUID], UUID | None]] = []
        self.lock_calls = 0
        self.source_checks: list[dict] = []
        self.source_error: Exception | None = None
        # F0008: identity-v1 slots and evidence document dates (ADR-0078 D1/D4).
        self.v1_slots: set[UUID] = set()
        self.document_dates: dict[UUID, DocumentDate | None] = {}
        self.split_of: dict[UUID, UUID | None] = {}

    async def require_commit_sources(self, **kwargs) -> None:
        self.source_checks.append(kwargs)
        if self.source_error is not None:
            raise self.source_error

    def seed_slot(self, slot_id: UUID, *, identity_v1: bool = False) -> None:
        self.slots.add(slot_id)
        if identity_v1:
            self.v1_slots.add(slot_id)

    async def slot_identity_version(self, slot_id: UUID) -> int | None:
        return 1 if slot_id in self.v1_slots else None

    async def evidence_document_dates(self, refs, *, authorized_scope):  # type: ignore[no-untyped-def]
        return {ref: self.document_dates.get(ref) for ref in refs}

    def seed_version(self, version: FactVersion) -> None:
        self.versions[version.id] = version

    async def lock_slot(self, slot_id: UUID) -> tuple[UUID, UUID] | None:
        self.lock_calls += 1
        if slot_id not in self.slots:
            return None
        return (self.tenant_id, self.knowledge_base_id)

    async def current_versions(self, slot_id: UUID) -> tuple[FactVersion, ...]:
        return tuple(
            v
            for v in self.versions.values()
            if v.fact_slot_id == slot_id and v.recorded_end is None
        )

    async def close_recorded(self, version_id: UUID, at: datetime) -> None:
        self.versions[version_id] = replace(self.versions[version_id], recorded_end=at)

    async def insert_version(
        self,
        *,
        version_id: UUID,
        slot_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        value: dict,
        valid: TimeRange,
        recorded: TimeRange,
        change_reason: ChangeReason | None,
        evidence_refs: tuple[UUID, ...],
        review_decision_id: UUID | None,
        commit_id: UUID,
        source_received_at: datetime,
        artifact_created_at: datetime,
        assertion_created_at: datetime,
        canonical_accepted_at: datetime,
        temporal: VersionTemporal | None = None,
        split_of_version_id: UUID | None = None,
        ending_evidence_refs: tuple[UUID, ...] = (),
    ) -> None:
        self.versions[version_id] = FactVersion(
            id=version_id,
            fact_slot_id=slot_id,
            value=value,
            valid_start=valid.start,
            valid_end=valid.end,
            recorded_start=recorded.start,
            recorded_end=recorded.end,
            change_reason=change_reason,
            evidence_refs=evidence_refs,
            commit_id=commit_id,
            canonical_accepted_at=canonical_accepted_at,
            review_decision_id=review_decision_id,
            source_received_at=source_received_at,
            artifact_created_at=artifact_created_at,
            assertion_created_at=assertion_created_at,
            temporal=temporal,
            ending_evidence_refs=ending_evidence_refs,
        )
        self.split_of[version_id] = split_of_version_id

    @property
    def scope(self) -> tuple[UUID, UUID]:
        return (self.tenant_id, self.knowledge_base_id)

    async def insert_change(
        self,
        *,
        reason: ChangeReason,
        from_version_id: UUID | None,
        to_version_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> None:
        self.changes.append(
            {
                "reason": reason,
                "from_version_id": from_version_id,
                "to_version_id": to_version_id,
                "scope": (tenant_id, knowledge_base_id),
            }
        )

    async def register_commit(
        self,
        *,
        commit_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        authorization_decision_id: UUID | None,
        at: datetime,
    ) -> None:
        self.commits.append((commit_id, (tenant_id, knowledge_base_id), authorization_decision_id))

    async def write_outbox(self, commit_id: UUID, payload: dict) -> None:
        self.outbox.append((commit_id, payload))


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def knowledge_base_id() -> UUID:
    return uuid4()


@pytest.fixture
def repository(tenant_id: UUID, knowledge_base_id: UUID) -> FakeFactCommitRepository:
    return FakeFactCommitRepository(tenant_id=tenant_id, knowledge_base_id=knowledge_base_id)
