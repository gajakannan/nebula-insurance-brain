"""Resolve-or-create a FactSlot identity (F0007-S0001/S0002/S0005, ADR-0077 D1-D4).

The resolver is trusted application code: the caller has already authorized the
source artifacts (`AuthorizedFactSlots.resolve` runs it as the operation of
`AuthorizationExecution.mutate` with INTERPRET). `authorized_scope` comes from that
decision, never from the payload. Every rejection happens inside a savepoint, so a
rejected request leaves zero slot, qualifier or member rows.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from brain_domain.authx import AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.fact_slots import (
    FINGERPRINT_VERSION,
    CanonicalQualifier,
    Cardinality,
    Fingerprinter,
    PredicateContract,
    PredicateKey,
    SlotIdentity,
    SlotReason,
    SlotRejected,
    SlotRole,
    canonical_qualifiers,
    fingerprint_v1,
    member_key,
    parse_release_ref,
    slot_reason_for,
)
from brain_domain.fact_values import (
    Json,
    TypedValue,
    ValueRejected,
    ValueType,
    canonical_name,
    canonical_value,
)

from brain_factslots.ports import FactSlotStore, PredicateContractRegistry, StoredSlot

KEY_SCHEMA_VERSION = 1
_KEY_FIELDS = frozenset(
    {
        "schema_version",
        "knowledge_base_id",
        "subject_entity_id",
        "predicate_key",
        "predicate_release_ref",
        "qualifiers",
        "object_entity_id",
        "member",
    }
)


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """`fact-slot-resolution-result-v1`."""

    outcome: str
    reason: SlotReason | None = None
    slot_id: UUID | None = None
    member_slot_id: UUID | None = None
    member_created: bool | None = None
    predicate_key: str | None = None
    cardinality: Cardinality | None = None
    fingerprint: str | None = None

    @classmethod
    def rejected(cls, reason: SlotReason) -> ResolutionResult:
        return cls("REJECTED", reason=reason)

    @property
    def target_slot_id(self) -> UUID | None:
        """The slot that answers are committed to: the member for MULTI."""
        return self.member_slot_id or self.slot_id

    def to_json(self) -> dict[str, Json]:
        result: dict[str, Json] = {"schema_version": 1, "outcome": self.outcome}
        if self.outcome == "REJECTED":
            assert self.reason is not None
            result["reason"] = self.reason.value
            return result
        result.update(
            {
                "slot_id": str(self.slot_id),
                "predicate_key": self.predicate_key,
                "cardinality": self.cardinality.value if self.cardinality else None,
                "fingerprint_version": FINGERPRINT_VERSION,
                "fingerprint": self.fingerprint,
            }
        )
        if self.member_slot_id is not None:
            result["member_slot_id"] = str(self.member_slot_id)
            result["member_created"] = bool(self.member_created)
        return result


@dataclass(frozen=True, slots=True)
class _Request:
    key: PredicateKey
    contract: PredicateContract
    cardinality: Cardinality
    qualifiers: tuple[CanonicalQualifier, ...]
    entity_refs: tuple[UUID, ...]
    object_entity_id: UUID | None
    member: TypedValue | None
    member_key: str | None


def _uuid(raw: object) -> UUID | None:
    if not isinstance(raw, str):
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


class FactSlotResolver:
    def __init__(
        self,
        registry: PredicateContractRegistry,
        store: FactSlotStore,
        *,
        fingerprint: Fingerprinter = fingerprint_v1,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._registry = registry
        self._store = store
        self._fingerprint = fingerprint
        self._clock = clock or (lambda: datetime.now(UTC))

    def _parse(self, key: Mapping[str, object]) -> _Request:
        """Steps 2-3: predicate key, contract shape, qualifiers and member value."""
        if key.get("schema_version") != KEY_SCHEMA_VERSION or set(key) - _KEY_FIELDS:
            raise SlotRejected(SlotReason.PREDICATE_KEY_INVALID)
        predicate = PredicateKey.parse(key.get("predicate_key"))
        release = parse_release_ref(key.get("predicate_release_ref"))
        contract = self._registry.contract(predicate, release)
        cardinality = contract.checked_cardinality()
        if "member" in key and cardinality != Cardinality.MULTI:
            raise SlotRejected(SlotReason.MEMBER_NOT_ALLOWED)
        if cardinality == Cardinality.MULTI and key.get("member") is None:
            raise SlotRejected(SlotReason.MEMBER_KEY_REQUIRED)
        has_object = key.get("object_entity_id") is not None
        if cardinality == Cardinality.RELATIONSHIP and not has_object:
            raise SlotRejected(SlotReason.RELATIONSHIP_OBJECT_REQUIRED)
        if cardinality != Cardinality.RELATIONSHIP and "object_entity_id" in key:
            raise SlotRejected(SlotReason.RELATIONSHIP_OBJECT_NOT_ALLOWED)
        object_entity_id = None
        if has_object:
            object_entity_id = _uuid(key.get("object_entity_id"))
            if object_entity_id is None:
                raise SlotRejected(SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE)
        qualifiers, entity_refs = canonical_qualifiers(key.get("qualifiers", {}), contract)
        member = None
        key_text = None
        if cardinality == Cardinality.MULTI:
            expected = (
                ValueType.ENTITY_REF
                if contract.member_key_source == "entity"
                else contract.value_type
            )
            try:
                member = canonical_value(
                    key["member"], expected=expected, basis_required=contract.basis_required
                )
            except ValueRejected as exc:
                raise SlotRejected(
                    slot_reason_for(exc, type_reason=SlotReason.QUALIFIER_TYPE_INVALID)
                ) from exc
            key_text = member_key(member, contract)
            if member.value_type == ValueType.ENTITY_REF:
                entity_refs = (*entity_refs, UUID(str(member.identity)))
        return _Request(
            predicate,
            contract,
            cardinality,
            qualifiers,
            entity_refs,
            object_entity_id,
            member,
            key_text,
        )

    async def evidence_source_keys(self, key: object) -> tuple[ResourceKey, ...]:
        """Source artifacts of a name member's evidence assertion. Tolerant: a
        malformed key adds no key and is rejected later with its reason."""
        member = key.get("member") if isinstance(key, Mapping) else None
        if not isinstance(member, Mapping) or member.get("type") != ValueType.NAME.value:
            return ()
        evidence = member.get("evidence")
        assertion = _uuid(evidence.get("assertion_id")) if isinstance(evidence, Mapping) else None
        knowledge_base_id = (
            _uuid(key.get("knowledge_base_id")) if isinstance(key, Mapping) else None
        )
        if assertion is None or knowledge_base_id is None:
            return ()
        artifacts = await self._store.name_evidence_artifacts(assertion, knowledge_base_id)
        return tuple(sorted(ResourceKey(ResourceType.CONTENT_ARTIFACT, a) for a in artifacts))

    async def resolve(
        self,
        key: Mapping[str, object],
        *,
        authorized_scope: tuple[UUID, UUID],
        source_keys: Sequence[ResourceKey],
        actor_id: UUID,
        decision: AuthorizationDecision | None = None,
    ) -> ResolutionResult:
        """Return the existing or newly created slot. Raises `SlotRejected`."""
        if not isinstance(key, Mapping):
            raise SlotRejected(SlotReason.PREDICATE_KEY_INVALID)
        request = self._parse(key)
        tenant_id, knowledge_base_id = authorized_scope
        subject = _uuid(key.get("subject_entity_id"))
        if subject is None or _uuid(key.get("knowledge_base_id")) != knowledge_base_id:
            raise SlotRejected(SlotReason.SUBJECT_NOT_FOUND)
        async with self._store.atomic():
            await self._check_scope(request, authorized_scope, subject)
            at = self._clock()
            header_identity = SlotIdentity(
                tenant_id,
                knowledge_base_id,
                subject,
                request.key,
                request.qualifiers,
                object_entity_id=request.object_entity_id,
            )
            header, created = await self._insert_or_verify(
                header_identity, request, SlotRole.SLOT, actor_id, at
            )
            if created:
                await self._store.insert_qualifiers(header, request.qualifiers, at)
                await self._store.provision_access(
                    header, sources=source_keys, inherit_from=None, actor_id=actor_id, at=at
                )
                await self._store.record_created(
                    header,
                    event_type="fact_slot_created",
                    actor_id=actor_id,
                    at=at,
                    decision=decision,
                )
            result = ResolutionResult(
                "CREATED" if created else "RESOLVED",
                slot_id=header.id,
                predicate_key=str(request.key),
                cardinality=request.cardinality,
                fingerprint=header.identity_fingerprint,
            )
            if request.cardinality != Cardinality.MULTI:
                return result
            member_identity = SlotIdentity(
                tenant_id,
                knowledge_base_id,
                subject,
                request.key,
                (),
                parent_slot_id=header.id,
                member_key=request.member_key,
            )
            member, member_created = await self._insert_or_verify(
                member_identity, request, SlotRole.MEMBER, actor_id, at
            )
            if member_created:
                await self._store.provision_access(
                    member, sources=source_keys, inherit_from=header.id, actor_id=actor_id, at=at
                )
                await self._store.record_created(
                    member,
                    event_type="fact_slot_member_created",
                    actor_id=actor_id,
                    at=at,
                    decision=decision,
                )
            return ResolutionResult(
                result.outcome,
                slot_id=header.id,
                member_slot_id=member.id,
                member_created=member_created,
                predicate_key=str(request.key),
                cardinality=request.cardinality,
                fingerprint=header.identity_fingerprint,
            )

    async def _check_scope(
        self, request: _Request, owner: tuple[UUID, UUID], subject: UUID
    ) -> None:
        """Step 4. A subject that does not exist and one outside the authorized KB
        give the same reason, so the result never discloses another KB's entity."""
        tenant_id, knowledge_base_id = owner
        if not await self._store.entity_in_kb(tenant_id, knowledge_base_id, subject):
            raise SlotRejected(SlotReason.SUBJECT_NOT_FOUND)
        others = [request.object_entity_id] if request.object_entity_id else []
        for entity in (*others, *request.entity_refs):
            if not await self._store.entity_in_kb(tenant_id, knowledge_base_id, entity):
                raise SlotRejected(SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE)
        if request.member is not None and request.member.value_type == ValueType.NAME:
            name = canonical_name(request.member.canonical)
            if not await self._store.name_evidence_eligible(name.evidence, owner):
                raise SlotRejected(SlotReason.NAME_EVIDENCE_REQUIRED)

    async def _insert_or_verify(
        self,
        identity: SlotIdentity,
        request: _Request,
        role: SlotRole,
        actor_id: UUID,
        at: datetime,
    ) -> tuple[StoredSlot, bool]:
        """Step 5/6. The fingerprint finds a candidate; the stored identity decides."""
        stored, created = await self._store.insert_or_get(
            identity,
            fingerprint=self._fingerprint(identity),
            contract=request.contract,
            role=role,
            actor_id=actor_id,
            at=at,
        )
        if created:
            return stored, True
        same = (
            stored.identity_version is not None
            and stored.subject_entity_id == identity.subject_entity_id
            and stored.predicate_key == str(identity.predicate_key)
            and stored.object_entity_id == identity.object_entity_id
            and stored.parent_slot_id == identity.parent_slot_id
            and stored.member_key == identity.member_key
            and stored.slot_role == role
            and tuple(sorted(await self._store.qualifiers(stored.id)))
            == tuple(sorted(identity.qualifiers))
        )
        if not same:
            raise SlotRejected(SlotReason.FINGERPRINT_COLLISION)
        if stored.cardinality != request.cardinality:
            raise SlotRejected(SlotReason.CARDINALITY_CONFLICT)
        return stored, False
