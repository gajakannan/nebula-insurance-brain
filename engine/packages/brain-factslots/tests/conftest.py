"""In-memory `FactSlotStore` for unit tests. PostgreSQL behaviour (concurrency,
keys, triggers, migration) is proven in `engine/tests/integration/test_factslot_*`."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import AuthorizationDecision, ResourceKey
from brain_domain.fact_slots import (
    CanonicalQualifier,
    PredicateContract,
    SlotIdentity,
    SlotRole,
)
from brain_domain.fact_values import NameEvidence
from brain_factslots.ports import StoredSlot


@dataclass
class MemoryStore:
    entities: set[tuple[UUID, UUID, UUID]] = field(default_factory=set)
    slots: dict[UUID, StoredSlot] = field(default_factory=dict)
    qualifier_rows: dict[UUID, tuple[CanonicalQualifier, ...]] = field(default_factory=dict)
    access: dict[UUID, tuple[tuple[ResourceKey, ...], UUID | None]] = field(default_factory=dict)
    events: list[tuple[str, UUID]] = field(default_factory=list)
    artifacts: dict[UUID, tuple[UUID, UUID]] = field(default_factory=dict)
    evidence: dict[UUID, tuple[UUID, tuple[UUID, UUID], tuple[UUID, ...]]] = field(
        default_factory=dict
    )
    answers: dict[UUID, Mapping[str, Any]] = field(default_factory=dict)

    @asynccontextmanager
    async def atomic(self) -> AsyncIterator[None]:
        saved = deepcopy((self.slots, self.qualifier_rows, self.access, self.events))
        try:
            yield
        except BaseException:
            self.slots, self.qualifier_rows, self.access, self.events = saved
            raise

    async def entity_in_kb(self, tenant_id, knowledge_base_id, entity_id):  # type: ignore[no-untyped-def]
        return (tenant_id, knowledge_base_id, entity_id) in self.entities

    async def insert_or_get(
        self,
        identity: SlotIdentity,
        *,
        fingerprint: str,
        contract: PredicateContract,
        role: SlotRole,
        actor_id: UUID,
        at: datetime,
    ):  # type: ignore[no-untyped-def]
        for slot in self.slots.values():
            if (slot.tenant_id, slot.knowledge_base_id, slot.identity_fingerprint) == (
                identity.tenant_id,
                identity.knowledge_base_id,
                fingerprint,
            ):
                return slot, False
        slot = StoredSlot(
            id=uuid4(),
            tenant_id=identity.tenant_id,
            knowledge_base_id=identity.knowledge_base_id,
            subject_entity_id=identity.subject_entity_id,
            slot_type=str(identity.predicate_key),
            identity_version=1,
            slot_role=role,
            predicate_key=str(identity.predicate_key),
            predicate_release_ref=contract.release_ref,
            cardinality=contract.checked_cardinality(),
            object_entity_id=identity.object_entity_id,
            parent_slot_id=identity.parent_slot_id,
            member_key=identity.member_key,
            fingerprint_version=1,
            identity_fingerprint=fingerprint,
        )
        self.slots[slot.id] = slot
        return slot, True

    async def qualifiers(self, slot_id):  # type: ignore[no-untyped-def]
        return self.qualifier_rows.get(slot_id, ())

    async def insert_qualifiers(self, slot, qualifiers, at):  # type: ignore[no-untyped-def]
        self.qualifier_rows[slot.id] = tuple(qualifiers)

    async def provision_access(self, slot, *, sources, inherit_from, actor_id, at):  # type: ignore[no-untyped-def]
        self.access[slot.id] = (tuple(sources), inherit_from)

    async def record_created(
        self,
        slot,
        *,
        event_type,
        actor_id,
        at,  # type: ignore[no-untyped-def]
        decision: AuthorizationDecision | None,
    ):
        self.events.append((event_type, slot.id))

    async def slot(self, slot_id):  # type: ignore[no-untyped-def]
        return self.slots.get(slot_id)

    async def artifact_owner(self, artifact_id):  # type: ignore[no-untyped-def]
        return self.artifacts.get(artifact_id)

    async def name_evidence_eligible(self, evidence: NameEvidence, owner):  # type: ignore[no-untyped-def]
        found = self.evidence.get(evidence.assertion_id)
        return found is not None and found[0] == evidence.document_version_id and found[1] == owner

    async def name_evidence_artifacts(self, assertion_id, knowledge_base_id):  # type: ignore[no-untyped-def]
        found = self.evidence.get(assertion_id)
        return found[2] if found and found[1][1] == knowledge_base_id else ()

    async def answer_at(self, slot_id, *, valid_at, known_at):  # type: ignore[no-untyped-def]
        return self.answers.get(slot_id)

    async def name_slots(self, knowledge_base_id, entity_id, predicate_keys: Sequence[str]):  # type: ignore[no-untyped-def]
        return tuple(
            s
            for s in self.slots.values()
            if s.knowledge_base_id == knowledge_base_id
            and s.subject_entity_id == entity_id
            and s.predicate_key in predicate_keys
            and (s.cardinality.value == "SINGLE" or s.slot_role == SlotRole.MEMBER)
        )


@dataclass
class Scene:
    store: MemoryStore
    tenant: UUID
    kb: UUID
    subject: UUID
    other_kb: UUID

    def entity(self, kb: UUID | None = None) -> UUID:
        entity = uuid4()
        self.store.entities.add((self.tenant, kb or self.kb, entity))
        return entity


@pytest.fixture
def scene() -> Scene:
    store = MemoryStore()
    tenant, kb, other = uuid4(), uuid4(), uuid4()
    subject = uuid4()
    store.entities.add((tenant, kb, subject))
    return Scene(store, tenant, kb, subject, other)
