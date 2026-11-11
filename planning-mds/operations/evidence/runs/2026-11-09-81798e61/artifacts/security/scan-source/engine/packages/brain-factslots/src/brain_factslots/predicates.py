"""Predicate contract registry (ADR-0077 D2).

Production composition registers only the `sys` namespace: the four ADR-0066 name
predicates. Real predicates arrive with F0012/F0013. Any other key is
`PREDICATE_UNREGISTERED` by design. The `test` namespace exists only in test
composition (`brain_testing.factslots`).
"""

from __future__ import annotations

from collections.abc import Iterable

from brain_domain.fact_slots import (
    Cardinality,
    PredicateContract,
    PredicateKey,
    SlotReason,
    SlotRejected,
)
from brain_domain.fact_values import ValueType

SYSTEM_NAMESPACE = "sys"
SYSTEM_RELEASE = "f0007-system-predicates/1"


def _name(local: str, cardinality: Cardinality) -> PredicateContract:
    return PredicateContract(
        key=PredicateKey(SYSTEM_NAMESPACE, local, 1),
        release_ref=SYSTEM_RELEASE,
        cardinality=cardinality,
        value_type=ValueType.NAME,
        member_key_source="value" if cardinality == Cardinality.MULTI else None,
    )


SYSTEM_PREDICATES: tuple[PredicateContract, ...] = (
    _name("hasLegalName", Cardinality.SINGLE),
    _name("hasTradeName", Cardinality.MULTI),
    _name("hasFormerName", Cardinality.MULTI),
    _name("knownAs", Cardinality.MULTI),
)
NAME_PREDICATE_KEYS: tuple[str, ...] = tuple(str(c.key) for c in SYSTEM_PREDICATES)
_SYSTEM_CARDINALITY = {c.key: c.cardinality for c in SYSTEM_PREDICATES}


class StaticPredicateRegistry:
    """An immutable, process-cacheable registry keyed by (predicate key, release).

    System predicates are fixed: a contract that redeclares one with another
    cardinality is refused with `CARDINALITY_CONFLICT`."""

    def __init__(self, contracts: Iterable[PredicateContract]) -> None:
        table: dict[tuple[PredicateKey, str], PredicateContract] = {}
        for contract in contracts:
            fixed = _SYSTEM_CARDINALITY.get(contract.key)
            if contract.key.namespace == SYSTEM_NAMESPACE and fixed != contract.cardinality:
                raise SlotRejected(SlotReason.CARDINALITY_CONFLICT)
            table[(contract.key, contract.release_ref)] = contract
        self._table = table

    def contract(self, key: PredicateKey, release_ref: str) -> PredicateContract:
        found = self.find(key, release_ref)
        if found is None:
            raise SlotRejected(SlotReason.PREDICATE_UNREGISTERED)
        return found

    def find(self, key: PredicateKey, release_ref: str) -> PredicateContract | None:
        return self._table.get((key, release_ref))


def production_registry() -> StaticPredicateRegistry:
    return StaticPredicateRegistry(SYSTEM_PREDICATES)
