from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.facts import ChangeReason, FactVersion
from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus
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
        self.lock_calls = 0

    def seed_slot(self, slot_id: UUID) -> None:
        self.slots.add(slot_id)

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
        old = self.versions[version_id]
        self.versions[version_id] = FactVersion(
            id=old.id,
            fact_slot_id=old.fact_slot_id,
            value=old.value,
            valid_start=old.valid_start,
            valid_end=old.valid_end,
            recorded_start=old.recorded_start,
            recorded_end=at,
            change_reason=old.change_reason,
            evidence_refs=old.evidence_refs,
            commit_id=old.commit_id,
            canonical_accepted_at=old.canonical_accepted_at,
        )

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
        )

    async def insert_change(
        self, *, reason: ChangeReason, from_version_id: UUID | None, to_version_id: UUID
    ) -> None:
        self.changes.append(
            {"reason": reason, "from_version_id": from_version_id, "to_version_id": to_version_id}
        )

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


@pytest.fixture
def actor() -> Principal:
    return Principal(
        id=uuid4(),
        kind=PrincipalKind.SERVICE,
        issuer="authentik",
        subject="svc",
        status=PrincipalStatus.ACTIVE,
    )


@pytest.fixture
def membership(actor: Principal, tenant_id: UUID, knowledge_base_id: UUID) -> Membership:
    return Membership(
        principal_id=actor.id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        role="ServicePrincipal",
        grant_revision=1,
        revoked_at=None,
    )
