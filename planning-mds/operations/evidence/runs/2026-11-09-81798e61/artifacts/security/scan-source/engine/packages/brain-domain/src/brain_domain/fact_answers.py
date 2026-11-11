"""The `fact-answer/v1` carrier (F0007, ADR-0039 D1-D5, ADR-0077 D5). Pure domain.

Information state is separate from the value. Only PRESENT carries a value.
NOT_FOUND and NOT_STATED name the exact scope searched. There is no access-denied
state: authorization is decided before any answer is produced.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from brain_domain.fact_values import (
    Json,
    NameValue,
    TypedValue,
    ValueRejected,
    ValueType,
    canonical_name,
    canonical_value,
)

ANSWER_CONTRACT = "fact-answer/v1"
MAX_SCOPE_PAGES = 2000
MAX_SCOPE_BLOCKS = 5000
_RELEASE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/-")


class InformationState(StrEnum):
    PRESENT = "PRESENT"
    NOT_PROCESSED = "NOT_PROCESSED"
    NOT_FOUND = "NOT_FOUND"
    NOT_STATED = "NOT_STATED"
    ILLEGIBLE = "ILLEGIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    EXPLICIT_NEGATIVE = "EXPLICIT_NEGATIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


SCOPE_REQUIRED = frozenset({InformationState.NOT_FOUND, InformationState.NOT_STATED})
SCOPE_FORBIDDEN = frozenset(
    {InformationState.PRESENT, InformationState.NOT_PROCESSED, InformationState.NOT_APPLICABLE}
)


class AnswerReason(StrEnum):
    """Answer rejections, in precedence order: contract, state, state/value shape,
    scope, value type, value detail. The first reason found is returned."""

    ANSWER_CONTRACT_UNSUPPORTED = "ANSWER_CONTRACT_UNSUPPORTED"
    MULTI_SLOT_REQUIRES_MEMBER = "MULTI_SLOT_REQUIRES_MEMBER"
    INFORMATION_STATE_INVALID = "INFORMATION_STATE_INVALID"
    STATE_VALUE_MISMATCH = "STATE_VALUE_MISMATCH"
    ABSENCE_SCOPE_REQUIRED = "ABSENCE_SCOPE_REQUIRED"
    ABSENCE_SCOPE_OUT_OF_SCOPE = "ABSENCE_SCOPE_OUT_OF_SCOPE"
    VALUE_TYPE_MISMATCH = "VALUE_TYPE_MISMATCH"
    DECIMAL_INVALID = "DECIMAL_INVALID"
    TEXT_INVALID = "TEXT_INVALID"
    MONEY_FLOAT_REJECTED = "MONEY_FLOAT_REJECTED"
    CURRENCY_INVALID = "CURRENCY_INVALID"
    BASIS_REQUIRED = "BASIS_REQUIRED"
    CONVERTED_MONEY_UNSUPPORTED = "CONVERTED_MONEY_UNSUPPORTED"
    IDENTIFIER_SCHEME_REQUIRED = "IDENTIFIER_SCHEME_REQUIRED"
    IDENTIFIER_INVALID = "IDENTIFIER_INVALID"
    NAME_EVIDENCE_REQUIRED = "NAME_EVIDENCE_REQUIRED"
    RELATIONSHIP_OBJECT_OUT_OF_SCOPE = "RELATIONSHIP_OBJECT_OUT_OF_SCOPE"
    MEMBER_VALUE_MISMATCH = "MEMBER_VALUE_MISMATCH"


class FactAnswerRejected(Exception):
    def __init__(self, reason: AnswerReason) -> None:
        super().__init__(reason.value)
        self.reason = reason

    @property
    def code(self) -> str:
        """The API `code`: the lowercase reason, with no detail text."""
        return self.reason.value.lower()


@dataclass(frozen=True, slots=True)
class AbsenceScope:
    content_artifact_id: UUID
    profile_release_ref: str
    pages: tuple[int, ...] = ()
    block_ids: tuple[UUID, ...] = ()

    def to_json(self) -> dict[str, Json]:
        scope: dict[str, Json] = {
            "content_artifact_id": str(self.content_artifact_id),
            "profile_release_ref": self.profile_release_ref,
        }
        if self.pages:
            scope["pages"] = list(self.pages)
        if self.block_ids:
            scope["block_ids"] = [str(b) for b in self.block_ids]
        return scope


@dataclass(frozen=True, slots=True)
class FactAnswer:
    state: InformationState
    value: TypedValue | None = None
    scope: AbsenceScope | None = None
    legacy_value: Mapping[str, Json] | None = None

    def to_json(self) -> dict[str, Json]:
        """The canonical stored envelope."""
        envelope: dict[str, Json] = {"answer_contract": ANSWER_CONTRACT, "state": self.state.value}
        if self.value is not None:
            envelope["value"] = self.value.canonical
        if self.scope is not None:
            envelope["scope"] = self.scope.to_json()
        return envelope

    @property
    def name(self) -> NameValue | None:
        if self.value is None or self.value.value_type != ValueType.NAME:
            return None
        return canonical_name(self.value.canonical)


def _scope(raw: object) -> AbsenceScope:
    required = AnswerReason.ABSENCE_SCOPE_REQUIRED
    if not isinstance(raw, Mapping) or set(raw) - {
        "content_artifact_id",
        "profile_release_ref",
        "pages",
        "block_ids",
    }:
        raise FactAnswerRejected(required)
    try:
        artifact = (
            UUID(raw["content_artifact_id"])
            if isinstance(raw.get("content_artifact_id"), str)
            else None
        )
    except ValueError:
        artifact = None
    release = raw.get("profile_release_ref")
    if (
        artifact is None
        or not isinstance(release, str)
        or not 0 < len(release) <= 128
        or not release[0].isalnum()
        or not set(release) <= _RELEASE_CHARS
    ):
        raise FactAnswerRejected(required)
    pages = raw.get("pages", [])
    blocks = raw.get("block_ids", [])
    if (
        not isinstance(pages, list)
        or not isinstance(blocks, list)
        or len(pages) > MAX_SCOPE_PAGES
        or len(blocks) > MAX_SCOPE_BLOCKS
        or any(isinstance(p, bool) or not isinstance(p, int) or p < 1 for p in pages)
        or len(set(pages)) != len(pages)
        or not (pages or blocks)
    ):
        raise FactAnswerRejected(required)
    try:
        block_ids = tuple(UUID(b) for b in blocks if isinstance(b, str))
    except ValueError as exc:
        raise FactAnswerRejected(required) from exc
    if len(block_ids) != len(blocks) or len(set(block_ids)) != len(block_ids):
        raise FactAnswerRejected(required)
    return AbsenceScope(artifact, release, tuple(pages), block_ids)


def parse_answer(
    raw: object,
    *,
    value_type: ValueType,
    basis_required: bool = False,
    multi_header: bool = False,
) -> FactAnswer:
    """Validate and canonicalize a submitted envelope for one identity-v1 slot.

    Store-dependent checks (scope ownership, name evidence, entity scope) are the
    application policy's; they come after these in the precedence order, because a
    scope never accompanies a value and a value never accompanies a scope."""
    if (
        not isinstance(raw, Mapping)
        or raw.get("answer_contract") != ANSWER_CONTRACT
        or set(raw) - {"answer_contract", "state", "value", "scope"}
    ):
        raise FactAnswerRejected(AnswerReason.ANSWER_CONTRACT_UNSUPPORTED)
    if multi_header:
        raise FactAnswerRejected(AnswerReason.MULTI_SLOT_REQUIRES_MEMBER)
    try:
        state = InformationState(raw.get("state"))  # type: ignore[arg-type]
    except ValueError as exc:
        raise FactAnswerRejected(AnswerReason.INFORMATION_STATE_INVALID) from exc
    has_value = "value" in raw
    has_scope = "scope" in raw
    if (state == InformationState.PRESENT) != has_value:
        raise FactAnswerRejected(AnswerReason.STATE_VALUE_MISMATCH)
    if has_scope and state in SCOPE_FORBIDDEN:
        raise FactAnswerRejected(AnswerReason.STATE_VALUE_MISMATCH)
    scope = None
    if state in SCOPE_REQUIRED and not has_scope:
        raise FactAnswerRejected(AnswerReason.ABSENCE_SCOPE_REQUIRED)
    if has_scope:
        scope = _scope(raw["scope"])
    value = None
    if has_value:
        try:
            value = canonical_value(
                raw["value"], expected=value_type, basis_required=basis_required
            )
        except ValueRejected as exc:
            raise FactAnswerRejected(AnswerReason(exc.reason.value)) from exc
    return FactAnswer(state, value, scope)


def stored_answer(raw: Mapping[str, Json]) -> FactAnswer:
    """Rebuild a domain answer from a stored, already-canonical envelope."""
    state = InformationState(raw["state"])
    value = None
    if "value" in raw:
        item = raw["value"]
        value = canonical_value(item, basis_required=False)
    scope = _scope(raw["scope"]) if "scope" in raw else None
    return FactAnswer(state, value, scope)
