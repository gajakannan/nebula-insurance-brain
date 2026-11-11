"""Ports for F0007 FactSlot services. `brain_persistence.fact_slots` implements
`FactSlotStore` over PostgreSQL; unit tests use in-memory fakes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from brain_domain.authx import AuthorizationDecision, ResourceKey
from brain_domain.fact_slots import (
    CanonicalQualifier,
    Cardinality,
    PredicateContract,
    PredicateKey,
    SlotIdentity,
    SlotRole,
)
from brain_domain.fact_values import NameEvidence


@dataclass(frozen=True, slots=True)
class StoredSlot:
    """One `fact_slot` row. `identity_version is None` marks a legacy pilot slot."""

    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    subject_entity_id: UUID
    slot_type: str
    identity_version: int | None = None
    slot_role: SlotRole | None = None
    predicate_key: str | None = None
    predicate_release_ref: str | None = None
    cardinality: Cardinality | None = None
    object_entity_id: UUID | None = None
    parent_slot_id: UUID | None = None
    member_key: str | None = None
    fingerprint_version: int | None = None
    identity_fingerprint: str | None = None

    @property
    def legacy(self) -> bool:
        return self.identity_version is None

    @property
    def owner(self) -> tuple[UUID, UUID]:
        return (self.tenant_id, self.knowledge_base_id)

    @property
    def multi_header(self) -> bool:
        return self.cardinality == Cardinality.MULTI and self.slot_role == SlotRole.SLOT


class PredicateContractRegistry(Protocol):
    def contract(self, key: PredicateKey, release_ref: str) -> PredicateContract:
        """The contract pinned at `release_ref`; `PREDICATE_UNREGISTERED` if absent."""
        ...

    def find(self, key: PredicateKey, release_ref: str) -> PredicateContract | None: ...


class FactSlotStore(Protocol):
    def atomic(self) -> AbstractAsyncContextManager[Any]:
        """A savepoint: a rejection inside it leaves zero rows."""
        ...

    async def entity_in_kb(
        self, tenant_id: UUID, knowledge_base_id: UUID, entity_id: UUID
    ) -> bool: ...

    async def insert_or_get(
        self,
        identity: SlotIdentity,
        *,
        fingerprint: str,
        contract: PredicateContract,
        role: SlotRole,
        actor_id: UUID,
        at: datetime,
    ) -> tuple[StoredSlot, bool]:
        """Insert the identity row or return the row already holding its fingerprint
        (`INSERT ... ON CONFLICT DO NOTHING`, then `SELECT ... FOR SHARE`)."""
        ...

    async def qualifiers(self, slot_id: UUID) -> tuple[CanonicalQualifier, ...]: ...

    async def insert_qualifiers(
        self, slot: StoredSlot, qualifiers: Sequence[CanonicalQualifier], at: datetime
    ) -> None: ...

    async def provision_access(
        self,
        slot: StoredSlot,
        *,
        sources: Sequence[ResourceKey],
        inherit_from: UUID | None,
        actor_id: UUID,
        at: datetime,
    ) -> None:
        """Derive the new slot's restrictions from its sources (and, for a member,
        its header) in the same unit of work."""
        ...

    async def record_created(
        self,
        slot: StoredSlot,
        *,
        event_type: str,
        actor_id: UUID,
        at: datetime,
        decision: AuthorizationDecision | None,
    ) -> None: ...

    async def slot(self, slot_id: UUID) -> StoredSlot | None: ...

    async def artifact_owner(self, artifact_id: UUID) -> tuple[UUID, UUID] | None: ...

    async def name_evidence_eligible(
        self, evidence: NameEvidence, owner: tuple[UUID, UUID]
    ) -> bool: ...

    async def name_evidence_artifacts(
        self, assertion_id: UUID, knowledge_base_id: UUID
    ) -> tuple[UUID, ...]:
        """Evidence artifacts of the assertion, only when it belongs to the KB, so a
        foreign assertion is indistinguishable from a missing one."""
        ...

    async def answer_at(
        self, slot_id: UUID, *, valid_at: datetime, known_at: datetime
    ) -> Mapping[str, Any] | None: ...

    async def name_slots(
        self, knowledge_base_id: UUID, entity_id: UUID, predicate_keys: Sequence[str]
    ) -> tuple[StoredSlot, ...]:
        """SINGLE slots and MULTI members (never headers) for the given predicates."""
        ...
