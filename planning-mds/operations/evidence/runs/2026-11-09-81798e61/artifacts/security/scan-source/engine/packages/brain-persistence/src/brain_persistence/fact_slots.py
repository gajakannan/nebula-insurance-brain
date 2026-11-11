"""`brain_factslots.ports.FactSlotStore` over PostgreSQL (F0007, ADR-0077).

Concurrency: `insert_or_get` relies on the partial unique index
`uq_fact_slot_identity`. `INSERT ... ON CONFLICT DO NOTHING` waits for a
concurrent uncommitted insert of the same fingerprint; the follow-up
`SELECT ... FOR SHARE` then reads the committed row, so concurrent resolvers
converge on one slot.

Reads use column projections, not ORM entities, so nothing protected is loaded
into the identity map before the caller's authorization decision.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from brain_assertions.eligibility import evaluate_eligibility
from brain_domain.audit import AuditEvent
from brain_domain.authx import AuthorizationDecision, ResourceKey, ResourceType, ScopedId
from brain_domain.fact_slots import (
    FINGERPRINT_VERSION,
    IDENTITY_VERSION,
    CanonicalQualifier,
    Cardinality,
    PredicateContract,
    SlotIdentity,
    SlotRole,
)
from brain_domain.fact_values import NameEvidence, ValueType
from brain_factslots.ports import StoredSlot
from sqlalchemy import Row, and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from brain_persistence.assertion_models import AssertionSemantics
from brain_persistence.authx import append_audit_event
from brain_persistence.fact_slot_models import FactSlotQualifierRow
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    CanonicalFactVersionRow,
    ContentArtifact,
    EntityKnowledgeBaseRow,
    FactSlotRow,
    ResourceAccessRow,
)
from brain_persistence.tenancy import NOT_AN_AUTHORIZATION, provision_resource_access

_SLOT_COLUMNS = (
    FactSlotRow.id,
    FactSlotRow.tenant_id,
    FactSlotRow.knowledge_base_id,
    FactSlotRow.entity_id,
    FactSlotRow.slot_type,
    FactSlotRow.identity_version,
    FactSlotRow.slot_role,
    FactSlotRow.predicate_key,
    FactSlotRow.predicate_release_ref,
    FactSlotRow.cardinality,
    FactSlotRow.object_entity_id,
    FactSlotRow.parent_slot_id,
    FactSlotRow.member_key,
    FactSlotRow.fingerprint_version,
    FactSlotRow.identity_fingerprint,
)


def _stored(row: Row[Any]) -> StoredSlot:
    return StoredSlot(
        id=row.id,
        tenant_id=row.tenant_id,
        knowledge_base_id=row.knowledge_base_id,
        subject_entity_id=row.entity_id,
        slot_type=row.slot_type,
        identity_version=row.identity_version,
        slot_role=SlotRole(row.slot_role) if row.slot_role else None,
        predicate_key=row.predicate_key,
        predicate_release_ref=row.predicate_release_ref,
        cardinality=Cardinality(row.cardinality) if row.cardinality else None,
        object_entity_id=row.object_entity_id,
        parent_slot_id=row.parent_slot_id,
        member_key=row.member_key,
        fingerprint_version=row.fingerprint_version,
        identity_fingerprint=row.identity_fingerprint,
    )


def _derive_access(
    session: Session,
    target: ResourceKey,
    *,
    owner: tuple[UUID, UUID],
    sources: Sequence[ResourceKey],
    inherit_from: ResourceKey | None,
    actor_id: UUID,
    at: datetime,
) -> None:
    """ADR-0042 decision 4: a derived record inherits its sources' restrictions.
    Classifications, source ACLs and parent chains are unions; the sources (and
    their own dependencies) become evidence dependencies. Missing source metadata
    fails closed inside `provision_resource_access`'s caller transaction."""
    origins = [*sources, *([inherit_from] if inherit_from else [])]
    classifications: set[str] = set()
    acls: set[str] = set()
    parents: set[ScopedId] = set()
    dependencies: set[ResourceKey] = set(sources)
    for origin in origins:
        access = session.get(
            ResourceAccessRow, (origin.type.value, origin.id), populate_existing=True
        )
        if access is None or (access.tenant_id, access.knowledge_base_id) != owner:
            raise PermissionError("source record has no security metadata in the slot's KB")
        classifications.update(access.classifications)
        acls.update(access.source_acl_ids)
        parents.update(ScopedId(p["kind"], UUID(p["id"])) for p in access.parent_chain)
        dependencies.update(ResourceKey(d["type"], UUID(d["id"])) for d in access.dependency_keys)
    provision_resource_access(
        session,
        target,
        tenant_id=owner[0],
        knowledge_base_id=owner[1],
        classifications=classifications,
        source_acl_ids=acls,
        parent_chain=parents,
        dependency_keys=dependencies - {target},
        actor_id=actor_id,
        at=at,
    )


class SqlAlchemyFactSlotStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @asynccontextmanager
    async def atomic(self) -> AsyncIterator[None]:
        async with self._session.begin_nested():
            yield

    async def entity_in_kb(self, tenant_id: UUID, knowledge_base_id: UUID, entity_id: UUID) -> bool:
        found = await self._session.scalar(
            select(EntityKnowledgeBaseRow.entity_id).where(
                EntityKnowledgeBaseRow.entity_id == entity_id,
                EntityKnowledgeBaseRow.tenant_id == tenant_id,
                EntityKnowledgeBaseRow.knowledge_base_id == knowledge_base_id,
            )
        )
        return found is not None

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
        statement = (
            insert(FactSlotRow)
            .values(
                id=uuid4(),
                entity_id=identity.subject_entity_id,
                slot_type=str(identity.predicate_key),
                tenant_id=identity.tenant_id,
                knowledge_base_id=identity.knowledge_base_id,
                identity_version=IDENTITY_VERSION,
                slot_role=role.value,
                predicate_key=str(identity.predicate_key),
                predicate_release_ref=contract.release_ref,
                cardinality=contract.checked_cardinality().value,
                object_entity_id=identity.object_entity_id,
                parent_slot_id=identity.parent_slot_id,
                member_key=identity.member_key,
                fingerprint_version=FINGERPRINT_VERSION,
                identity_fingerprint=fingerprint,
                created_by=actor_id,
            )
            .on_conflict_do_nothing(
                index_elements=["tenant_id", "knowledge_base_id", "identity_fingerprint"],
                index_where=FactSlotRow.identity_version.is_not(None),
            )
            .returning(*_SLOT_COLUMNS)
        )
        created = (await self._session.execute(statement)).first()
        if created is not None:
            return _stored(created), True
        existing = (
            await self._session.execute(
                select(*_SLOT_COLUMNS)
                .where(
                    FactSlotRow.tenant_id == identity.tenant_id,
                    FactSlotRow.knowledge_base_id == identity.knowledge_base_id,
                    FactSlotRow.identity_fingerprint == fingerprint,
                    FactSlotRow.identity_version.is_not(None),
                )
                .with_for_update(read=True)
            )
        ).one()
        return _stored(existing), False

    async def qualifiers(self, slot_id: UUID) -> tuple[CanonicalQualifier, ...]:
        rows = await self._session.execute(
            select(
                FactSlotQualifierRow.qualifier_name,
                FactSlotQualifierRow.value_type,
                FactSlotQualifierRow.canonical_value,
            )
            .where(FactSlotQualifierRow.slot_id == slot_id)
            .order_by(FactSlotQualifierRow.qualifier_name)
        )
        return tuple(
            CanonicalQualifier(r.qualifier_name, ValueType(r.value_type), r.canonical_value)
            for r in rows
        )

    async def insert_qualifiers(
        self, slot: StoredSlot, qualifiers: Sequence[CanonicalQualifier], at: datetime
    ) -> None:
        for qualifier in qualifiers:
            self._session.add(
                FactSlotQualifierRow(
                    slot_id=slot.id,
                    tenant_id=slot.tenant_id,
                    knowledge_base_id=slot.knowledge_base_id,
                    qualifier_name=qualifier.name,
                    value_type=qualifier.value_type.value,
                    canonical_value=qualifier.canonical,
                    created_at=at,
                )
            )
        await self._session.flush()

    async def provision_access(
        self,
        slot: StoredSlot,
        *,
        sources: Sequence[ResourceKey],
        inherit_from: UUID | None,
        actor_id: UUID,
        at: datetime,
    ) -> None:
        target = ResourceKey(ResourceType.FACT_SLOT, slot.id)
        parent = ResourceKey(ResourceType.FACT_SLOT, inherit_from) if inherit_from else None
        await self._session.run_sync(
            lambda session: _derive_access(
                session,
                target,
                owner=slot.owner,
                sources=sources,
                inherit_from=parent,
                actor_id=actor_id,
                at=at,
            )
        )

    async def record_created(
        self,
        slot: StoredSlot,
        *,
        event_type: str,
        actor_id: UUID,
        at: datetime,
        decision: AuthorizationDecision | None,
    ) -> None:
        """One operational audit event per creation: actor, tenant, KB, slot and
        fingerprint version. IDs and versions only, never values or content."""
        payload = {
            "event_type": event_type,
            "tenant_id": str(slot.tenant_id),
            "knowledge_base_id": str(slot.knowledge_base_id),
            "slot_id": str(slot.id),
            "parent_slot_id": str(slot.parent_slot_id) if slot.parent_slot_id else None,
            "predicate_key": slot.predicate_key,
            "cardinality": slot.cardinality.value if slot.cardinality else None,
            "fingerprint_version": slot.fingerprint_version,
            "authorization_decision_id": str(decision.decision_id) if decision else None,
        }
        event_id = uuid4()
        await self._session.run_sync(
            lambda session: append_audit_event(
                session,
                AuditEvent(
                    id=event_id,
                    occurred_at=at,
                    actor_principal_id=actor_id,
                    delegate_principal_id=decision.executor_principal_id if decision else None,
                    resource_type=ResourceType.FACT_SLOT.value,
                    resource_id=slot.id,
                    action=event_type,
                    decision=True,
                    reason_code="applied",
                    policy_hash=decision.policy_hash if decision else NOT_AN_AUTHORIZATION,
                    grant_revision=max(decision.grant_revision, 1) if decision else 1,
                    trace_id=decision.trace_id if decision else str(event_id),
                    decision_id=decision.decision_id if decision else None,
                    event_type=event_type,
                    operation_outcome="succeeded",
                    payload={
                        **payload,
                        "input_digest": hashlib.sha256(
                            json.dumps(payload, sort_keys=True).encode()
                        ).hexdigest(),
                    },
                ),
            )
        )
        await self._session.flush()

    async def slot(self, slot_id: UUID) -> StoredSlot | None:
        row = (
            await self._session.execute(select(*_SLOT_COLUMNS).where(FactSlotRow.id == slot_id))
        ).first()
        return _stored(row) if row is not None else None

    async def artifact_owner(self, artifact_id: UUID) -> tuple[UUID, UUID] | None:
        row = (
            await self._session.execute(
                select(ContentArtifact.tenant_id, ContentArtifact.knowledge_base_id).where(
                    ContentArtifact.id == artifact_id
                )
            )
        ).first()
        return (row.tenant_id, row.knowledge_base_id) if row is not None else None

    async def name_evidence_eligible(
        self, evidence: NameEvidence, owner: tuple[UUID, UUID]
    ) -> bool:
        """An admitted F0006 v2 assertion in the slot's tenant/KB, naming the supplied
        document version, whose F0006 eligibility does not block CREATE."""
        assertion = (
            await self._session.execute(
                select(
                    Assertion.tenant_id,
                    Assertion.knowledge_base_id,
                    Assertion.semantic_contract_version,
                ).where(Assertion.id == evidence.assertion_id)
            )
        ).first()
        if (
            assertion is None
            or assertion.semantic_contract_version != 2
            or (assertion.tenant_id, assertion.knowledge_base_id) != owner
        ):
            return False
        semantics = (
            await self._session.execute(
                select(
                    AssertionSemantics.document_version_id,
                    AssertionSemantics.tenant_id,
                    AssertionSemantics.knowledge_base_id,
                    AssertionSemantics.record,
                    AssertionSemantics.verified_evidence,
                ).where(AssertionSemantics.assertion_id == evidence.assertion_id)
            )
        ).first()
        if (
            semantics is None
            or semantics.document_version_id != evidence.document_version_id
            or (semantics.tenant_id, semantics.knowledge_base_id) != owner
        ):
            return False
        from brain_persistence.assertions import wire_evidence

        eligibility = evaluate_eligibility(
            semantics.record, [wire_evidence(e) for e in semantics.verified_evidence]
        )
        return "CREATE" not in eligibility.blocked_operations

    async def name_evidence_artifacts(
        self, assertion_id: UUID, knowledge_base_id: UUID
    ) -> tuple[UUID, ...]:
        rows = await self._session.execute(
            select(AssertionEvidence.artifact_id)
            .distinct()
            .where(
                AssertionEvidence.assertion_id == assertion_id,
                AssertionEvidence.knowledge_base_id == knowledge_base_id,
            )
        )
        return tuple(sorted(rows.scalars(), key=str))

    async def answer_at(
        self, slot_id: UUID, *, valid_at: datetime, known_at: datetime
    ) -> Mapping[str, Any] | None:
        return await self._session.scalar(
            select(CanonicalFactVersionRow.value).where(
                CanonicalFactVersionRow.slot_id == slot_id,
                CanonicalFactVersionRow.valid.op("@>")(valid_at),
                CanonicalFactVersionRow.recorded.op("@>")(known_at),
            )
        )

    async def name_slots(
        self, knowledge_base_id: UUID, entity_id: UUID, predicate_keys: Sequence[str]
    ) -> tuple[StoredSlot, ...]:
        rows = await self._session.execute(
            select(*_SLOT_COLUMNS)
            .where(
                FactSlotRow.knowledge_base_id == knowledge_base_id,
                FactSlotRow.entity_id == entity_id,
                FactSlotRow.identity_version.is_not(None),
                FactSlotRow.predicate_key.in_(list(predicate_keys)),
                or_(
                    FactSlotRow.cardinality == Cardinality.SINGLE.value,
                    and_(
                        FactSlotRow.cardinality == Cardinality.MULTI.value,
                        FactSlotRow.slot_role == SlotRole.MEMBER.value,
                    ),
                ),
            )
            .order_by(FactSlotRow.predicate_key, FactSlotRow.id)
        )
        return tuple(_stored(r) for r in rows)
