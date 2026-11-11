"""Authorized entry points for F0007 (ADR-0077 D7).

Authorization always precedes validation detail:

- Slot creation runs as the operation of `AuthorizationExecution.mutate` over the
  source content artifacts with the existing `content_artifact:interpret` action.
  F0007 adds no grant, route or Casbin row.
- Answer reads and the name hook authorize each slot with `fact_slot:read`. A
  denied slot is indistinguishable from a missing one.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.fact_answers import FactAnswer
from brain_domain.fact_slots import SlotReason, SlotRejected
from brain_domain.principal import Principal
from brain_security.execution import AuthorizationDenied, AuthorizationExecution

from brain_factslots.answers import FactAnswerReader
from brain_factslots.names import NameFact, NameFactReader, order_names
from brain_factslots.resolution import FactSlotResolver, ResolutionResult


class SlotNotFound(LookupError):
    """A missing slot, or one the principal may not read: never distinguished."""


def _slot_key(slot_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.FACT_SLOT, slot_id)


class AuthorizedFactSlots:
    def __init__(
        self,
        execution: AuthorizationExecution,
        resolver: FactSlotResolver,
        names: NameFactReader,
        answers: FactAnswerReader,
    ) -> None:
        self._execution = execution
        self._resolver = resolver
        self._names = names
        self._answers = answers

    async def resolve(
        self,
        principal: Principal,
        key: dict,
        *,
        source_artifact_ids: Sequence[UUID],
        trace_id: str,
    ) -> ResolutionResult:
        """Resolve or create a slot. A denial raises `AuthorizationDenied` before any
        reason; a rejection returns `REJECTED` with zero rows written."""
        sources = sorted(
            {ResourceKey(ResourceType.CONTENT_ARTIFACT, a) for a in source_artifact_ids}
        )
        if not sources:
            raise ValueError("slot resolution names at least one source artifact")
        evidence: list[ResourceKey] = []

        async def evidence_reads() -> Sequence[ResourceKey]:
            # A name member cites an F0006 assertion. Its source artifacts must be
            # readable before any reason is returned, and they join the new
            # member's restrictions (ADR-0077 D7, threat T-08).
            evidence.extend(await self._resolver.evidence_source_keys(key))
            return evidence

        async def operation(decisions: Sequence[AuthorizationDecision]) -> ResolutionResult:
            scopes = {
                (d.scope.tenant_id, d.scope.knowledge_base_id)
                for d in decisions
                if d.scope is not None
            }
            if len(scopes) != 1:
                # Sources from two owners cannot motivate one KB-owned slot.
                raise SlotRejected(SlotReason.SUBJECT_NOT_FOUND)
            (scope,) = scopes
            return await self._resolver.resolve(
                key,
                authorized_scope=scope,
                source_keys=sorted({*sources, *evidence}),
                actor_id=principal.id,
                decision=decisions[0],
            )

        try:
            return await self._execution.mutate(
                principal,
                sources,
                Action.INTERPRET,
                trace_id=trace_id,
                operation=operation,
                additional_reads=evidence_reads,
            )
        except SlotRejected as exc:
            # `mutate` rolled the unit of work back and durably recorded the
            # decisions as FAILED, so the rejection left zero rows.
            return ResolutionResult.rejected(exc.reason)

    async def read_answer(
        self,
        principal: Principal,
        slot_id: UUID,
        *,
        valid_at: datetime,
        known_at: datetime,
        trace_id: str,
    ) -> FactAnswer:
        async def load(decision: AuthorizationDecision) -> FactAnswer:
            try:
                return await self._answers.read(slot_id, valid_at=valid_at, known_at=known_at)
            except LookupError as exc:
                raise SlotNotFound(str(slot_id)) from exc

        async def scope_reads(answer: FactAnswer) -> Sequence[ResourceKey]:
            if answer.scope is None:
                return ()
            return (ResourceKey(ResourceType.CONTENT_ARTIFACT, answer.scope.content_artifact_id),)

        try:
            return await self._execution.read(
                principal,
                _slot_key(slot_id),
                Action.READ,
                trace_id=trace_id,
                load=load,
                additional_reads=scope_reads,
            )
        except AuthorizationDenied as exc:
            raise SlotNotFound(str(slot_id)) from exc

    async def current_names(
        self,
        principal: Principal,
        *,
        knowledge_base_id: UUID,
        entity_id: UUID,
        valid_at: datetime,
        known_at: datetime,
        trace_id: str,
    ) -> list[NameFact]:
        """The display-name hook. Each candidate slot is authorized for READ; a slot
        the principal cannot read is silently absent, exactly like a missing one."""
        facts: list[NameFact] = []
        for slot_id in await self._names.candidate_slots(knowledge_base_id, entity_id):

            async def load(
                _decision: AuthorizationDecision, slot_id: UUID = slot_id
            ) -> NameFact | None:
                return await self._names.name_fact(slot_id, valid_at=valid_at, known_at=known_at)

            try:
                fact = await self._execution.read(
                    principal, _slot_key(slot_id), Action.READ, trace_id=trace_id, load=load
                )
            except AuthorizationDenied:
                continue
            if fact is not None:
                facts.append(fact)
        return order_names(facts)
