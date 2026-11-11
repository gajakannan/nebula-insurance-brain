"""Typed FactSlot values and their canonical encodings (F0007, ADR-0077 D3/D5/D6).

Pure functions: no I/O, no clock, no model call. Every rejection carries one
named reason from the F0007 contract so callers never have to parse messages.
The JSON value shapes are the `typed_value` definitions in
`planning-mds/schemas/fact-slot-key-v1.schema.json`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from functools import cache
from importlib import resources
from typing import Any
from uuid import UUID

ISO4217_LIST_VERSION = "2026-01"
IDENTIFIER_NORMALIZATION_VERSION = 1
DECIMAL_MAX_INPUT = 64
DECIMAL_MAX_CANONICAL = DECIMAL_MAX_INPUT
TEXT_MAX = 4000
NAME_MAX = 1000
IDENTIFIER_MAX = 256

_DECIMAL = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_SCHEME = re.compile(r"^[a-z][a-z0-9-]{0,31}(?::[A-Za-z0-9._-]{1,128})?$")
_IDENTIFIER_TYPE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
# Money keys that mark a converted amount. F0007 accepts original currency only.
_CONVERSION_KEYS = frozenset(
    {
        "converted",
        "converted_from",
        "conversion",
        "exchange_rate",
        "fx_rate",
        "original_amount",
        "original_currency",
    }
)


class ValueType(StrEnum):
    TEXT = "text"
    CODE = "code"
    DECIMAL = "decimal"
    DATE = "date"
    BOOLEAN = "boolean"
    ENTITY_REF = "entity_ref"
    MONEY = "money"
    IDENTIFIER = "identifier"
    NAME = "name"


# Qualifiers use the scalar typed values only (fact-slot-key-v1 `qualifier_value`).
QUALIFIER_TYPES = frozenset(ValueType) - {ValueType.NAME}


class ValueReason(StrEnum):
    """Value-level rejection reasons shared by slot resolution and answers."""

    DECIMAL_INVALID = "DECIMAL_INVALID"
    TEXT_INVALID = "TEXT_INVALID"
    MONEY_FLOAT_REJECTED = "MONEY_FLOAT_REJECTED"
    CURRENCY_INVALID = "CURRENCY_INVALID"
    BASIS_REQUIRED = "BASIS_REQUIRED"
    CONVERTED_MONEY_UNSUPPORTED = "CONVERTED_MONEY_UNSUPPORTED"
    IDENTIFIER_SCHEME_REQUIRED = "IDENTIFIER_SCHEME_REQUIRED"
    IDENTIFIER_INVALID = "IDENTIFIER_INVALID"
    NAME_EVIDENCE_REQUIRED = "NAME_EVIDENCE_REQUIRED"
    VALUE_TYPE_MISMATCH = "VALUE_TYPE_MISMATCH"


class ValueRejected(ValueError):
    def __init__(self, reason: ValueReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


Json = Any


def jcs(value: Json) -> bytes:
    """RFC 8785 serialization for the JSON subset F0007 hashes.

    The subset is objects with ASCII keys, strings, integers, booleans, null and
    arrays; no floats ever reach it. For that subset, sorted keys, no whitespace,
    literal non-ASCII and the json module's escapes match JCS byte for byte.
    """
    _check_jcs_subset(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _check_jcs_subset(value: Json) -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, list):
        for item in value:
            _check_jcs_subset(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise TypeError("JCS subset keys are ASCII strings")
            _check_jcs_subset(item)
        return
    raise TypeError(f"{type(value).__name__} is outside the F0007 JCS subset")


def nfc_text(raw: object, *, max_length: int = TEXT_MAX) -> str:
    """Unicode NFC text that can be encoded as UTF-8 (no lone surrogates)."""
    if not isinstance(raw, str):
        raise ValueRejected(ValueReason.TEXT_INVALID)
    text = unicodedata.normalize("NFC", raw)
    if not text or len(text) > max_length:
        raise ValueRejected(ValueReason.TEXT_INVALID)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueRejected(ValueReason.TEXT_INVALID) from exc
    return text


def canonical_decimal(raw: object) -> str:
    """One canonical decimal text: no exponent, no trailing fractional zeros, `-0`
    becomes `0`. `1E+6`, `1000000.00` and `1000000` all become `1000000`.

    Input and canonical output are limited to 64 total characters, including
    sign and decimal point, so every emitted form can be read back. Digits are
    handled exactly, never through a float or a precision-limited Decimal context.
    """
    if not isinstance(raw, str) or len(raw) > DECIMAL_MAX_INPUT or not _DECIMAL.match(raw):
        raise ValueRejected(ValueReason.DECIMAL_INVALID)
    try:
        sign, digit_tuple, exponent = Decimal(raw).as_tuple()
    except InvalidOperation as exc:  # pragma: no cover - the pattern admits only finite forms
        raise ValueRejected(ValueReason.DECIMAL_INVALID) from exc
    assert isinstance(exponent, int)
    digits = list(digit_tuple)
    while len(digits) > 1 and digits[0] == 0:
        digits.pop(0)
    if all(d == 0 for d in digits):
        return "0"
    while exponent < 0 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    text = "".join(str(d) for d in digits)
    # WHY: exponent text is short even when its expanded value is enormous.
    # Bound the total canonical size before allocating any exponent-sized string.
    if exponent >= 0:
        body_length = len(text) + exponent
    elif -exponent >= len(text):
        body_length = 2 - exponent
    else:
        body_length = len(text) + 1
    if body_length + sign > DECIMAL_MAX_CANONICAL:
        raise ValueRejected(ValueReason.DECIMAL_INVALID)
    if exponent >= 0:
        body = text + "0" * exponent
    elif -exponent >= len(text):
        body = "0." + "0" * (-exponent - len(text)) + text
    else:
        body = text[:exponent] + "." + text[exponent:]
    return ("-" if sign else "") + body


@cache
def iso4217_codes() -> frozenset[str]:
    """The pinned ISO 4217 alphabetic list (`ISO4217_LIST_VERSION`), process-cached."""
    raw = (
        resources.files("brain_domain")
        .joinpath(f"data/iso4217-{ISO4217_LIST_VERSION}.txt")
        .read_text(encoding="utf-8")
    )
    return frozenset(
        line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#")
    )


@dataclass(frozen=True, slots=True)
class Money:
    amount: str
    currency: str
    basis: str | None = None

    def to_json(self) -> dict[str, Json]:
        value: dict[str, Json] = {"type": "money", "amount": self.amount, "currency": self.currency}
        if self.basis is not None:
            value["basis"] = self.basis
        return value

    def identity(self) -> dict[str, Json]:
        return {k: v for k, v in self.to_json().items() if k != "type"}


def canonical_money(raw: Mapping[str, object], *, basis_required: bool) -> Money:
    """ADR-0039 decision 4: exact decimal string, ISO 4217 currency, required basis,
    original currency only. Check order: conversion, amount, currency, basis."""
    keys = set(raw) - {"type"}
    if keys & _CONVERSION_KEYS or any("convert" in k or "exchange" in k for k in keys):
        raise ValueRejected(ValueReason.CONVERTED_MONEY_UNSUPPORTED)
    if keys - {"amount", "currency", "basis"}:
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
    amount = raw.get("amount")
    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        raise ValueRejected(ValueReason.MONEY_FLOAT_REJECTED)
    canonical_amount = canonical_decimal(amount)
    currency = raw.get("currency")
    if (
        not isinstance(currency, str)
        or not _CURRENCY.match(currency)
        or currency not in iso4217_codes()
    ):
        raise ValueRejected(ValueReason.CURRENCY_INVALID)
    basis = raw.get("basis")
    if basis is None:
        if basis_required:
            raise ValueRejected(ValueReason.BASIS_REQUIRED)
    elif not isinstance(basis, str) or not _CODE.match(basis):
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
    return Money(canonical_amount, currency, basis)


@dataclass(frozen=True, slots=True)
class ScopedIdentifier:
    scheme: str
    identifier_type: str
    value: str
    normalized_value: str
    effective_from: str | None = None
    effective_to: str | None = None

    def to_json(self) -> dict[str, Json]:
        value: dict[str, Json] = {
            "type": "identifier",
            "scheme": self.scheme,
            "identifier_type": self.identifier_type,
            "value": self.value,
            "normalized_value": self.normalized_value,
        }
        if self.effective_from is not None:
            effective: dict[str, Json] = {"from": self.effective_from}
            if self.effective_to is not None:
                effective["to"] = self.effective_to
            value["effective"] = effective
        return value

    def identity(self) -> dict[str, Json]:
        """Equality includes the scheme, so normalization never equates two schemes.
        The verbatim value and effective interval are attributes, not identity."""
        return {
            "scheme": self.scheme,
            "identifier_type": self.identifier_type,
            "normalized_value": self.normalized_value,
        }


def _normalize_fein(value: str) -> str:
    digits = value.replace("-", "")
    if len(digits) != 9 or not digits.isascii() or not digits.isdigit():
        raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
    return digits


# Versioned normalization table (IDENTIFIER_NORMALIZATION_VERSION = 1). Every
# identifier type not listed here uses NFC only.
_IDENTIFIER_NORMALIZERS = {"fein": _normalize_fein}


def normalize_identifier(identifier_type: str, value: str) -> str:
    normalizer = _IDENTIFIER_NORMALIZERS.get(identifier_type)
    return normalizer(value) if normalizer is not None else value


def _iso_date(raw: object) -> str:
    if not isinstance(raw, str) or not _ISO_DATE.match(raw):
        raise ValueError("not an ISO date")
    date.fromisoformat(raw)
    return raw


def canonical_identifier(raw: Mapping[str, object]) -> ScopedIdentifier:
    scheme = raw.get("scheme")
    if scheme is None or scheme == "":
        raise ValueRejected(ValueReason.IDENTIFIER_SCHEME_REQUIRED)
    if set(raw) - {"type", "scheme", "identifier_type", "value", "normalized_value", "effective"}:
        raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
    identifier_type = raw.get("identifier_type")
    if (
        not isinstance(scheme, str)
        or not _SCHEME.match(scheme)
        or not isinstance(identifier_type, str)
        or not _IDENTIFIER_TYPE.match(identifier_type)
    ):
        raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
    try:
        value = nfc_text(raw.get("value"), max_length=IDENTIFIER_MAX)
    except ValueRejected as exc:
        raise ValueRejected(ValueReason.IDENTIFIER_INVALID) from exc
    normalized = normalize_identifier(identifier_type, value)
    supplied = raw.get("normalized_value")
    if supplied is not None and supplied != normalized:
        raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
    effective_from = effective_to = None
    effective = raw.get("effective")
    if effective is not None:
        if not isinstance(effective, Mapping) or set(effective) - {"from", "to"}:
            raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
        try:
            effective_from = _iso_date(effective.get("from"))
            if effective.get("to") is not None:
                effective_to = _iso_date(effective.get("to"))
        except ValueError as exc:
            raise ValueRejected(ValueReason.IDENTIFIER_INVALID) from exc
        if effective_to is not None and effective_to < effective_from:
            raise ValueRejected(ValueReason.IDENTIFIER_INVALID)
    return ScopedIdentifier(
        scheme, identifier_type, value, normalized, effective_from, effective_to
    )


def normalize_name(verbatim: str) -> str:
    """NFC, then casefold, then whitespace collapse and strip (ADR-0066 §2). The same
    algorithm F0006 uses for name claims, so a name value and its claim agree."""
    return " ".join(unicodedata.normalize("NFC", verbatim).casefold().split())


@dataclass(frozen=True, slots=True)
class NameEvidence:
    assertion_id: UUID
    document_version_id: UUID


@dataclass(frozen=True, slots=True)
class NameValue:
    verbatim: str
    normalized: str
    evidence: NameEvidence
    name_kind: str | None = None

    def to_json(self) -> dict[str, Json]:
        value: dict[str, Json] = {
            "type": "name",
            "verbatim": self.verbatim,
            "normalized": self.normalized,
            "evidence": {
                "assertion_id": str(self.evidence.assertion_id),
                "document_version_id": str(self.evidence.document_version_id),
            },
        }
        if self.name_kind is not None:
            value["name_kind"] = self.name_kind
        return value


def _uuid(raw: object) -> UUID:
    if not isinstance(raw, str):
        raise ValueError("not a UUID string")
    return UUID(raw)


def canonical_name(raw: Mapping[str, object]) -> NameValue:
    evidence = raw.get("evidence")
    if not isinstance(evidence, Mapping) or set(evidence) != {
        "assertion_id",
        "document_version_id",
    }:
        raise ValueRejected(ValueReason.NAME_EVIDENCE_REQUIRED)
    try:
        reference = NameEvidence(
            _uuid(evidence["assertion_id"]), _uuid(evidence["document_version_id"])
        )
    except ValueError as exc:
        raise ValueRejected(ValueReason.NAME_EVIDENCE_REQUIRED) from exc
    if set(raw) - {"type", "verbatim", "normalized", "name_kind", "evidence"}:
        raise ValueRejected(ValueReason.TEXT_INVALID)
    verbatim = nfc_text(raw.get("verbatim"), max_length=NAME_MAX)
    normalized = normalize_name(verbatim)
    if not normalized:
        raise ValueRejected(ValueReason.TEXT_INVALID)
    supplied = raw.get("normalized")
    if supplied is not None and supplied != normalized:
        raise ValueRejected(ValueReason.TEXT_INVALID)
    name_kind = raw.get("name_kind")
    if name_kind is not None and (not isinstance(name_kind, str) or not _CODE.match(name_kind)):
        raise ValueRejected(ValueReason.TEXT_INVALID)
    return NameValue(verbatim, normalized, reference, name_kind)


@dataclass(frozen=True, slots=True)
class TypedValue:
    """A canonical typed value. `canonical` is the stored JSON form; `identity` is
    the part that decides equality (qualifier rows and member keys)."""

    value_type: ValueType
    canonical: dict[str, Json]
    identity: Json

    def identity_text(self) -> str:
        return jcs(self.identity).decode("utf-8")


def canonical_value(
    raw: object, *, expected: ValueType | None = None, basis_required: bool = False
) -> TypedValue:
    """Validate and canonicalize one typed value object.

    `expected` (the predicate contract's value type) is checked before any detail,
    so a wrong type is `VALUE_TYPE_MISMATCH` rather than a detail reason."""
    if not isinstance(raw, Mapping):
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
    try:
        value_type = ValueType(raw.get("type"))  # type: ignore[arg-type]
    except ValueError as exc:
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH) from exc
    if expected is not None and value_type != expected:
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
    if value_type == ValueType.MONEY:
        money = canonical_money(raw, basis_required=basis_required)
        return TypedValue(value_type, money.to_json(), money.identity())
    if value_type == ValueType.IDENTIFIER:
        identifier = canonical_identifier(raw)
        return TypedValue(value_type, identifier.to_json(), identifier.identity())
    if value_type == ValueType.NAME:
        name = canonical_name(raw)
        return TypedValue(value_type, name.to_json(), name.normalized)
    if value_type == ValueType.ENTITY_REF:
        if set(raw) != {"type", "entity_id"}:
            raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
        try:
            entity = str(_uuid(raw["entity_id"]))
        except ValueError as exc:
            raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH) from exc
        return TypedValue(value_type, {"type": "entity_ref", "entity_id": entity}, entity)
    if set(raw) != {"type", "value"}:
        raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
    item = raw["value"]
    canonical: Json
    if value_type == ValueType.TEXT:
        canonical = nfc_text(item)
    elif value_type == ValueType.DECIMAL:
        canonical = canonical_decimal(item)
    elif value_type == ValueType.CODE:
        if not isinstance(item, str) or not _CODE.match(item):
            raise ValueRejected(ValueReason.TEXT_INVALID)
        canonical = item
    elif value_type == ValueType.DATE:
        try:
            canonical = _iso_date(item)
        except ValueError as exc:
            raise ValueRejected(ValueReason.TEXT_INVALID) from exc
    else:  # BOOLEAN
        if not isinstance(item, bool):
            raise ValueRejected(ValueReason.VALUE_TYPE_MISMATCH)
        canonical = item
    return TypedValue(value_type, {"type": value_type.value, "value": canonical}, canonical)
