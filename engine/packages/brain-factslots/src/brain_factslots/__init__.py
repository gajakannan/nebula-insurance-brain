"""FactSlot identity resolution, typed answer policy and name facts (F0007, ADR-0077).

The pure identity and value rules live in `brain_domain.fact_slots`,
`brain_domain.fact_values` and `brain_domain.fact_answers`. This package adds the
application services over a `FactSlotStore` port; `brain_persistence.fact_slots`
implements the port over PostgreSQL.
"""

from brain_factslots.answers import FactAnswerPolicy, FactAnswerReader
from brain_factslots.names import NameFact, NameFactReader
from brain_factslots.predicates import (
    SYSTEM_PREDICATES,
    SYSTEM_RELEASE,
    StaticPredicateRegistry,
    production_registry,
)
from brain_factslots.resolution import FactSlotResolver, ResolutionResult
from brain_factslots.service import AuthorizedFactSlots

__all__ = [
    "SYSTEM_PREDICATES",
    "SYSTEM_RELEASE",
    "AuthorizedFactSlots",
    "FactAnswerPolicy",
    "FactAnswerReader",
    "FactSlotResolver",
    "NameFact",
    "NameFactReader",
    "ResolutionResult",
    "StaticPredicateRegistry",
    "production_registry",
]
