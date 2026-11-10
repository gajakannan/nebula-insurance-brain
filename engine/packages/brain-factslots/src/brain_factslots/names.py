"""Name facts and the precedence-free display hook (F0007-S0005, ADR-0066).

The hook returns the reader KB's current accepted name facts. The order
(predicate key, normalized form, slot ID) is stable but is NOT a display
precedence: choosing a display name is an open decision owned by F0017/F0023.
It never creates `entity_alias` rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from brain_domain.fact_answers import InformationState

from brain_factslots.answers import FactAnswerReader
from brain_factslots.ports import FactSlotStore
from brain_factslots.predicates import NAME_PREDICATE_KEYS


@dataclass(frozen=True, slots=True)
class NameFact:
    predicate_key: str
    slot_id: UUID
    verbatim: str
    normalized: str
    name_kind: str | None


class NameFactReader:
    def __init__(self, store: FactSlotStore) -> None:
        self._store = store
        self._answers = FactAnswerReader(store)

    async def candidate_slots(self, knowledge_base_id: UUID, entity_id: UUID) -> tuple[UUID, ...]:
        slots = await self._store.name_slots(knowledge_base_id, entity_id, NAME_PREDICATE_KEYS)
        return tuple(s.id for s in slots)

    async def name_fact(
        self, slot_id: UUID, *, valid_at: datetime, known_at: datetime
    ) -> NameFact | None:
        slot = await self._store.slot(slot_id)
        if slot is None or slot.legacy or slot.predicate_key not in NAME_PREDICATE_KEYS:
            return None
        answer = await self._answers.read(slot_id, valid_at=valid_at, known_at=known_at)
        name = answer.name
        if answer.state != InformationState.PRESENT or name is None:
            return None
        return NameFact(slot.predicate_key, slot.id, name.verbatim, name.normalized, name.name_kind)

    async def current_names(
        self,
        *,
        authorized_scope: tuple[UUID, UUID],
        entity_id: UUID,
        valid_at: datetime,
        known_at: datetime,
    ) -> list[NameFact]:
        """Trusted form: every name fact of the entity in the authorized KB."""
        _tenant_id, knowledge_base_id = authorized_scope
        facts = []
        for slot_id in await self.candidate_slots(knowledge_base_id, entity_id):
            fact = await self.name_fact(slot_id, valid_at=valid_at, known_at=known_at)
            if fact is not None:
                facts.append(fact)
        return order_names(facts)


def order_names(facts: list[NameFact]) -> list[NameFact]:
    return sorted(facts, key=lambda f: (f.predicate_key, f.normalized, str(f.slot_id)))
