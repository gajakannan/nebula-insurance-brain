"""FactSlot identity (F0007, ADR-0077 D1-D4). Pure domain: no I/O.

An identity-v1 slot is (tenant, knowledge base, subject entity, predicate key,
normalized qualifiers), plus the object entity for a RELATIONSHIP slot and the
parent slot and member key for a MULTI member. Stored qualifier rows are the
authoritative identity; the fingerprint only accelerates lookup.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID

from brain_domain.fact_values import (
    QUALIFIER_TYPES,
    Json,
    TypedValue,
    ValueRejected,
    ValueType,
    canonical_value,
    jcs,
)

IDENTITY_VERSION = 1
FINGERPRINT_VERSION = 1
MAX_QUALIFIERS = 16

_PREDICATE_KEY = re.compile(
    r"^(?P<namespace>[a-z][a-z0-9-]{0,31}):(?P<local>[A-Za-z][A-Za-z0-9]{0,63})"
    r"@v(?P<major>[1-9][0-9]{0,3})$"
)
_RELEASE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_QUALIFIER_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class Cardinality(StrEnum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    RELATIONSHIP = "RELATIONSHIP"


class SlotRole(StrEnum):
    """`identity_version IS NULL` marks a legacy pilot slot, which has no role."""

    SLOT = "SLOT"
    MEMBER = "MEMBER"


class SlotReason(StrEnum):
    """`fact-slot-resolution-result-v1` reasons."""

    PREDICATE_KEY_INVALID = "PREDICATE_KEY_INVALID"
    PREDICATE_UNREGISTERED = "PREDICATE_UNREGISTERED"
    CARDINALITY_INVALID = "CARDINALITY_INVALID"
    CARDINALITY_CONFLICT = "CARDINALITY_CONFLICT"
    SUBJECT_NOT_FOUND = "SUBJECT_NOT_FOUND"
    QUALIFIER_UNDECLARED = "QUALIFIER_UNDECLARED"
    QUALIFIER_REQUIRED = "QUALIFIER_REQUIRED"
    QUALIFIER_NULL_REJECTED = "QUALIFIER_NULL_REJECTED"
    QUALIFIER_TYPE_INVALID = "QUALIFIER_TYPE_INVALID"
    FINGERPRINT_COLLISION = "FINGERPRINT_COLLISION"
    MEMBER_KEY_REQUIRED = "MEMBER_KEY_REQUIRED"
    MEMBER_NOT_ALLOWED = "MEMBER_NOT_ALLOWED"
    RELATIONSHIP_OBJECT_REQUIRED = "RELATIONSHIP_OBJECT_REQUIRED"
    RELATIONSHIP_OBJECT_NOT_ALLOWED = "RELATIONSHIP_OBJECT_NOT_ALLOWED"
    RELATIONSHIP_OBJECT_OUT_OF_SCOPE = "RELATIONSHIP_OBJECT_OUT_OF_SCOPE"
    DECIMAL_INVALID = "DECIMAL_INVALID"
    TEXT_INVALID = "TEXT_INVALID"
    MONEY_FLOAT_REJECTED = "MONEY_FLOAT_REJECTED"
    CURRENCY_INVALID = "CURRENCY_INVALID"
    BASIS_REQUIRED = "BASIS_REQUIRED"
    CONVERTED_MONEY_UNSUPPORTED = "CONVERTED_MONEY_UNSUPPORTED"
    IDENTIFIER_SCHEME_REQUIRED = "IDENTIFIER_SCHEME_REQUIRED"
    IDENTIFIER_INVALID = "IDENTIFIER_INVALID"
    NAME_EVIDENCE_REQUIRED = "NAME_EVIDENCE_REQUIRED"


class SlotRejected(Exception):
    def __init__(self, reason: SlotReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


def slot_reason_for(error: ValueRejected, *, type_reason: SlotReason) -> SlotReason:
    """Map a value rejection inside resolution. A value-type mismatch becomes the
    caller's type reason (a qualifier or member of the wrong declared type)."""
    if error.reason.value == "VALUE_TYPE_MISMATCH":
        return type_reason
    return SlotReason(error.reason.value)


@dataclass(frozen=True, slots=True)
class PredicateKey:
    namespace: str
    local_name: str
    major: int

    @classmethod
    def parse(cls, raw: object) -> PredicateKey:
        match = _PREDICATE_KEY.match(raw) if isinstance(raw, str) else None
        if match is None:
            raise SlotRejected(SlotReason.PREDICATE_KEY_INVALID)
        return cls(match["namespace"], match["local"], int(match["major"]))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.local_name}@v{self.major}"


def parse_release_ref(raw: object) -> str:
    """A pinned release reference is required at creation (PREDICATE_KEY_INVALID)."""
    if not isinstance(raw, str) or not _RELEASE_REF.match(raw):
        raise SlotRejected(SlotReason.PREDICATE_KEY_INVALID)
    return raw


@dataclass(frozen=True, slots=True)
class QualifierSpec:
    name: str
    value_type: ValueType
    required: bool = False


@dataclass(frozen=True, slots=True)
class PredicateContract:
    key: PredicateKey
    release_ref: str
    cardinality: Cardinality | str
    value_type: ValueType
    qualifiers: tuple[QualifierSpec, ...] = ()
    member_key_source: Literal["value", "entity"] | None = None
    basis_required: bool = False

    def checked_cardinality(self) -> Cardinality:
        try:
            return Cardinality(self.cardinality)
        except ValueError as exc:
            raise SlotRejected(SlotReason.CARDINALITY_INVALID) from exc


@dataclass(frozen=True, slots=True, order=True)
class CanonicalQualifier:
    name: str
    value_type: ValueType
    canonical: str  # JCS text of the qualifier's canonical identity value

    def to_row(self) -> list[str]:
        return [self.name, self.value_type.value, self.canonical]


def canonical_qualifiers(
    raw: object, contract: PredicateContract
) -> tuple[tuple[CanonicalQualifier, ...], tuple[UUID, ...]]:
    """Canonicalize qualifiers against the contract (ADR-0077 D3).

    Omitted qualifiers contribute nothing; explicit null is rejected and never
    treated as omitted. Returns the sorted qualifiers and any entity references
    they contain, which the resolver must check against the slot's KB."""
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping) or len(raw) > MAX_QUALIFIERS:
        raise SlotRejected(SlotReason.QUALIFIER_TYPE_INVALID)
    declared = {spec.name: spec for spec in contract.qualifiers}
    result: list[CanonicalQualifier] = []
    entities: list[UUID] = []
    for name in sorted(raw):
        if not isinstance(name, str) or not _QUALIFIER_NAME.match(name):
            raise SlotRejected(SlotReason.QUALIFIER_UNDECLARED)
        spec = declared.get(name)
        if spec is None:
            raise SlotRejected(SlotReason.QUALIFIER_UNDECLARED)
        item = raw[name]
        if item is None:
            raise SlotRejected(SlotReason.QUALIFIER_NULL_REJECTED)
        if spec.value_type not in QUALIFIER_TYPES:
            raise SlotRejected(SlotReason.QUALIFIER_TYPE_INVALID)
        try:
            value = canonical_value(item, expected=spec.value_type)
        except ValueRejected as exc:
            raise SlotRejected(
                slot_reason_for(exc, type_reason=SlotReason.QUALIFIER_TYPE_INVALID)
            ) from exc
        if value.value_type == ValueType.ENTITY_REF:
            entities.append(UUID(value.identity))
        result.append(CanonicalQualifier(name, spec.value_type, value.identity_text()))
    missing = [s.name for s in contract.qualifiers if s.required and s.name not in raw]
    if missing:
        raise SlotRejected(SlotReason.QUALIFIER_REQUIRED)
    return tuple(sorted(result)), tuple(entities)


def member_key(value: TypedValue, contract: PredicateContract) -> str:
    """The member key is the canonical encoding of the member value or entity. For
    name predicates it is the normalized name (ADR-0077 D6)."""
    if contract.member_key_source == "entity":
        if value.value_type != ValueType.ENTITY_REF:
            raise SlotRejected(SlotReason.QUALIFIER_TYPE_INVALID)
        return str(value.identity)
    if value.value_type == ValueType.NAME:
        return str(value.identity)
    return value.identity_text()


@dataclass(frozen=True, slots=True)
class SlotIdentity:
    tenant_id: UUID
    knowledge_base_id: UUID
    subject_entity_id: UUID
    predicate_key: PredicateKey
    qualifiers: tuple[CanonicalQualifier, ...]  # sorted by name
    object_entity_id: UUID | None = None
    parent_slot_id: UUID | None = None
    member_key: str | None = None

    def document(self) -> dict[str, Json]:
        """The fingerprint input (version 1). Release reference and cardinality are
        deliberately excluded: a release bump never splits a slot."""
        return {
            "fp_version": FINGERPRINT_VERSION,
            "tenant_id": str(self.tenant_id),
            "knowledge_base_id": str(self.knowledge_base_id),
            "subject_entity_id": str(self.subject_entity_id),
            "predicate_key": str(self.predicate_key),
            "qualifiers": [q.to_row() for q in sorted(self.qualifiers)],
            "object_entity_id": str(self.object_entity_id) if self.object_entity_id else None,
            "parent_slot_id": str(self.parent_slot_id) if self.parent_slot_id else None,
            "member_key": self.member_key,
        }

    def fingerprint(self) -> str:
        return fingerprint_v1(self)


def fingerprint_v1(identity: SlotIdentity) -> str:
    """SHA-256 of the RFC 8785 serialization of the identity document, lowercase hex."""
    return hashlib.sha256(jcs(identity.document())).hexdigest()


Fingerprinter = Callable[[SlotIdentity], str]
