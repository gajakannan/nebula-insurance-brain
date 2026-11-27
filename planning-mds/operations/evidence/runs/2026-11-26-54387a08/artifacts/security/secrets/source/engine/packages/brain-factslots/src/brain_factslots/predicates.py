"""Predicate contract registry (ADR-0077 D2, ADR-0081 D6).

`StaticPredicateRegistry` holds the `sys` namespace (the four ADR-0066 name
predicates) and, in test composition only, the `test` namespace.
`ReleasePredicateRegistry` (F0012) composes it with the predicates of ontology
releases installed in one tenant/KB: `prepare(scope, refs)` loads exactly the
named releases installed there, and `contract()` reads that snapshot. A key absent
from the static table and every prepared release, or a release that is not
installed for the scope, stays `PREDICATE_UNREGISTERED`; there is no fallback to
an active release.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal, Protocol
from uuid import UUID

from brain_domain.fact_slots import (
    Cardinality,
    PredicateContract,
    PredicateKey,
    SlotReason,
    SlotRejected,
)
from brain_domain.fact_values import ValueType
from brain_domain.temporal import TemporalKind

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


class PredicateRowLike(Protocol):
    """One installed `ontology_term` predicate row (`OntologyReleaseStore.predicates`)."""

    @property
    def release_ref(self) -> str: ...
    @property
    def predicate_key(self) -> str: ...
    @property
    def cardinality(self) -> str: ...
    @property
    def value_type(self) -> str: ...
    @property
    def temporal_kind(self) -> str: ...


class ReleasePredicateSource(Protocol):
    """Implemented by `brain_persistence.ontology_releases.OntologyReleaseStore`."""

    async def predicates(
        self, scope: tuple[UUID, UUID], release_refs: Sequence[str]
    ) -> Sequence[PredicateRowLike]: ...


class RegistryNotPrepared(RuntimeError):
    """Strict (test) mode: a release-backed key was resolved without `prepare`."""


def contract_from_row(row: PredicateRowLike) -> PredicateContract:
    """One installed `ontology_term` predicate row as a contract (manifest rules)."""
    cardinality = Cardinality(row.cardinality)
    value_type = ValueType(row.value_type)
    member: Literal["value", "entity"] | None = None
    if cardinality == Cardinality.MULTI:
        member = "entity" if value_type == ValueType.ENTITY_REF else "value"
    return PredicateContract(
        key=PredicateKey.parse(row.predicate_key),
        release_ref=row.release_ref,
        cardinality=cardinality,
        value_type=value_type,
        member_key_source=member,
        basis_required=value_type == ValueType.MONEY,
        temporal_kind=TemporalKind(row.temporal_kind),
    )


class ReleasePredicateRegistry:
    """Per-unit-of-work registry; one tenant/KB at a time (fail closed)."""

    def __init__(
        self,
        static: StaticPredicateRegistry,
        source: ReleasePredicateSource,
        *,
        strict: bool = False,
    ) -> None:
        self._static = static
        self._source = source
        self._strict = strict
        self._scope: tuple[UUID, UUID] | None = None
        self._loaded: set[str] = set()
        self._table: dict[tuple[PredicateKey, str], PredicateContract] = {}

    async def prepare(self, scope: tuple[UUID, UUID], release_refs: Iterable[str | None]) -> None:
        if scope != self._scope:
            # A new scope never sees another scope's snapshot.
            self._scope, self._loaded, self._table = scope, set(), {}
        wanted = sorted({r for r in release_refs if r and r not in self._loaded})
        if not wanted:
            return
        for row in await self._source.predicates(scope, wanted):
            contract = contract_from_row(row)
            if contract.key.namespace == SYSTEM_NAMESPACE:
                raise SlotRejected(SlotReason.CARDINALITY_CONFLICT)
            self._table[(contract.key, contract.release_ref)] = contract
        self._loaded.update(wanted)

    def contract(self, key: PredicateKey, release_ref: str) -> PredicateContract:
        found = self.find(key, release_ref)
        if found is None:
            raise SlotRejected(SlotReason.PREDICATE_UNREGISTERED)
        return found

    def find(self, key: PredicateKey, release_ref: str) -> PredicateContract | None:
        found = self._static.find(key, release_ref)
        if found is not None:
            return found
        if self._strict and release_ref not in self._loaded:
            raise RegistryNotPrepared(f"{key}@{release_ref}")
        return self._table.get((key, release_ref))


async def prepare_registry(
    registry: object, scope: tuple[UUID, UUID], release_refs: Iterable[object]
) -> None:
    """Prepare a release-backed registry; a static registry needs nothing."""
    prepare = getattr(registry, "prepare", None)
    if prepare is not None:
        await prepare(scope, [r for r in release_refs if isinstance(r, str)])
