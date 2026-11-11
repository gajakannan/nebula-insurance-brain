"""Typed answers at the existing commit and on read (F0007-S0003/S0004/S0005).

`FactAnswerPolicy` implements `brain_temporal.commit.CommitAnswerPolicy`. It runs
inside `CanonicalCommitService.commit` after the slot lock, so it only ever sees
a slot the caller is authorized to commit to. Legacy pilot slots bypass it.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.fact_answers import (
    AnswerReason,
    FactAnswer,
    FactAnswerRejected,
    InformationState,
    parse_answer,
    stored_answer,
)
from brain_domain.fact_slots import PredicateKey, SlotRejected, SlotRole, member_key
from brain_domain.fact_values import ValueType

from brain_factslots.ports import FactSlotStore, PredicateContractRegistry, StoredSlot


def _uuid(raw: object) -> UUID | None:
    if not isinstance(raw, str):
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


class FactAnswerPolicy:
    def __init__(self, registry: PredicateContractRegistry, store: FactSlotStore) -> None:
        self._registry = registry
        self._store = store

    async def source_keys(self, slot_id: UUID, value: Mapping[str, Any]) -> tuple[ResourceKey, ...]:
        """Extra READ keys for the commit's `additional_reads`: the absence scope's
        artifact and the name evidence's source artifacts. Tolerant by design: a
        malformed value adds no key and is rejected later with its reason, after
        authorization has run."""
        slot = await self._store.slot(slot_id)
        if slot is None or slot.legacy or not isinstance(value, Mapping):
            return ()
        artifacts: set[UUID] = set()
        scope = value.get("scope")
        if isinstance(scope, Mapping):
            artifact = _uuid(scope.get("content_artifact_id"))
            if artifact is not None:
                artifacts.add(artifact)
        item = value.get("value")
        if isinstance(item, Mapping) and item.get("type") == ValueType.NAME.value:
            evidence = item.get("evidence")
            if isinstance(evidence, Mapping):
                assertion = _uuid(evidence.get("assertion_id"))
                if assertion is not None:
                    artifacts.update(
                        await self._store.name_evidence_artifacts(assertion, slot.knowledge_base_id)
                    )
        return tuple(sorted(ResourceKey(ResourceType.CONTENT_ARTIFACT, a) for a in artifacts))

    async def canonical_value(
        self,
        slot_id: UUID,
        value: Mapping[str, Any],
        *,
        authorized_scope: tuple[UUID, UUID],
    ) -> Mapping[str, Any] | None:
        """The canonical envelope to store, or `None` for a legacy slot."""
        slot = await self._store.slot(slot_id)
        if slot is None or slot.legacy:
            return None
        if slot.owner != authorized_scope:  # pragma: no cover - the commit lock checks it first
            raise FactAnswerRejected(AnswerReason.ANSWER_CONTRACT_UNSUPPORTED)
        contract = None
        try:
            if slot.predicate_key and slot.predicate_release_ref:
                contract = self._registry.find(
                    PredicateKey.parse(slot.predicate_key), slot.predicate_release_ref
                )
        except SlotRejected:
            contract = None
        if contract is None:
            raise FactAnswerRejected(AnswerReason.ANSWER_CONTRACT_UNSUPPORTED)
        answer = parse_answer(
            value,
            value_type=contract.value_type,
            basis_required=contract.basis_required,
            multi_header=slot.multi_header,
        )
        if answer.scope is not None:
            owner = await self._store.artifact_owner(answer.scope.content_artifact_id)
            if owner != slot.owner:
                raise FactAnswerRejected(AnswerReason.ABSENCE_SCOPE_OUT_OF_SCOPE)
        if answer.value is not None:
            await self._check_value_detail(slot, answer)
            # WHY: a member's immutable identity is derived from its value; a
            # different canonical value must resolve its own member slot.
            if (
                slot.slot_role == SlotRole.MEMBER
                and member_key(answer.value, contract) != slot.member_key
            ):
                raise FactAnswerRejected(AnswerReason.MEMBER_VALUE_MISMATCH)
        return answer.to_json()

    async def _check_value_detail(self, slot: StoredSlot, answer: FactAnswer) -> None:
        assert answer.value is not None
        name = answer.name
        if name is not None and not await self._store.name_evidence_eligible(
            name.evidence, slot.owner
        ):
            raise FactAnswerRejected(AnswerReason.NAME_EVIDENCE_REQUIRED)
        if answer.value.value_type == ValueType.ENTITY_REF and not await self._store.entity_in_kb(
            slot.tenant_id, slot.knowledge_base_id, UUID(str(answer.value.identity))
        ):
            raise FactAnswerRejected(AnswerReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE)


class FactAnswerReader:
    """Internal reader: an identity-v1 slot with no version at the coordinates
    answers `NOT_PROCESSED`, never null. Read authorization is the caller's
    (`fact_slot:read` through `AuthorizationExecution.read`)."""

    def __init__(self, store: FactSlotStore) -> None:
        self._store = store

    async def scope_keys_for_value(self, slot_id: UUID, stored: object) -> tuple[ResourceKey, ...]:
        """Derive keys from the exact privately loaded version, without selecting
        the answer again. Legacy JSON keeps its existing unwrapped semantics."""
        slot = await self._store.slot(slot_id)
        if slot is None or slot.legacy:
            return ()
        scope = stored.get("scope") if isinstance(stored, Mapping) else None
        artifact = _uuid(scope.get("content_artifact_id")) if isinstance(scope, Mapping) else None
        return (ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),) if artifact else ()

    async def read(self, slot_id: UUID, *, valid_at: datetime, known_at: datetime) -> FactAnswer:
        slot = await self._store.slot(slot_id)
        if slot is None:
            raise LookupError(str(slot_id))
        stored = await self._store.answer_at(slot_id, valid_at=valid_at, known_at=known_at)
        if slot.legacy:
            if stored is None:
                return FactAnswer(InformationState.NOT_PROCESSED)
            return FactAnswer(InformationState.PRESENT, legacy_value=dict(stored))
        if stored is None:
            return FactAnswer(InformationState.NOT_PROCESSED)
        return stored_answer(stored)
