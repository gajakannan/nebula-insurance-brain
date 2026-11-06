"""Strict, offline adapters for the additive assertion contracts (ADR-0075)."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from typing import Any, ClassVar, Final, Literal, Self
from uuid import UUID

from brain_domain.assertions import (
    AssertionCandidate,
    Basis,
    EntityObject,
    EntityReference,
    EvidenceClaim,
    Kind,
    LiteralObject,
    Mode,
    Origin,
)
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, JsonValue, PrivateAttr, model_validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

NORMALIZATION_VERSION: Final = "f0006-grounding-v1"
SCHEMA_NAMES = (
    "assertion-record-v2.schema.json",
    "interpretation-result-v2.schema.json",
    "assertion-admission-result-v1.schema.json",
    "interpretation-result.schema.json",
)


class AssertionContractError(ValueError):
    """Stable error only: never include an untrusted quote or validation repr."""

    code = "ASSERTION_CONTRACT_INVALID"

    def __init__(self) -> None:
        super().__init__(self.code)


class AssertionContractUnsupported(AssertionContractError):
    code = "ASSERTION_CONTRACT_UNSUPPORTED"


def wire_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return wire_value(asdict(value))
    if isinstance(value, Mapping):
        return {key: wire_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire_value(item) for item in value]
    return value


def _check_json(value: Any) -> None:
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif value is None or type(value) in (bool, int):
        return
    elif type(value) is float:
        if not math.isfinite(value):
            raise AssertionContractError()
    elif isinstance(value, list):
        for item in value:
            _check_json(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AssertionContractError()
            _check_json(key)
            _check_json(item)
    else:
        raise AssertionContractError()


def canonical_json(value: Any) -> bytes:
    value = wire_value(value)
    try:
        _check_json(value)
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise AssertionContractError() from None


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionContractError()
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise AssertionContractError()


def decode_json(raw: bytes | str) -> Any:
    """Reject duplicate keys, non-finite numbers and ill-formed Unicode at any depth."""
    try:
        text = raw.decode("utf-8", errors="strict") if isinstance(raw, bytes) else raw
        value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        _check_json(value)
        return value
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise AssertionContractError() from None


def _no_remote_reference(uri: str) -> Resource:
    # WHY: referencing builds these with its own attrs wrapper, which mypy's
    # attrs plugin does not see; the keyword is the documented constructor.
    raise NoSuchResource(ref=uri)  # type: ignore[call-arg]


@lru_cache(maxsize=1)
def _contracts() -> tuple[dict[str, dict[str, Any]], Registry]:
    contracts = {
        name: decode_json(files("brain_contracts").joinpath("schemas", name).read_bytes())
        for name in SCHEMA_NAMES
    }
    registry = Registry(retrieve=_no_remote_reference).with_resources(  # type: ignore[call-arg]
        (value["$id"], Resource.from_contents(value)) for value in contracts.values()
    )
    return contracts, registry


def validate_contract(name: str, value: Any, definition: str | None = None) -> None:
    contracts, registry = _contracts()
    if name not in contracts:
        raise AssertionContractError()
    schema = contracts[name]
    if definition is not None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"{schema['$id']}#/$defs/{definition}",
        }
    value = wire_value(value)
    try:
        _check_json(value)
        validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        if next(validator.iter_errors(value), None) is not None:
            raise AssertionContractError()
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise AssertionContractError() from None


class StrictModel(BaseModel):
    # WHY: the offline JSON Schema checks impose exact wire types before decoding.
    # Pydantic must still decode JSON arrays, UUIDs and timestamps into Python
    # carriers, including when a before-validator returns an inspected object.
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ContractModel(StrictModel):
    schema_name: ClassVar[str]
    definition: ClassVar[str | None] = None

    @model_validator(mode="before")
    @classmethod
    def input_contract(cls, value: Any) -> Any:
        validate_contract(cls.schema_name, value, cls.definition)
        return value

    @model_validator(mode="after")
    def output_contract(self) -> Self:
        validate_contract(self.schema_name, self.model_dump(mode="json"), self.definition)
        return self


class EvidenceClaimV2(StrictModel):
    artifact_id: UUID
    block_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    model_selector: dict[str, JsonValue] | None = None

    def to_domain(self) -> EvidenceClaim:
        return EvidenceClaim(self.artifact_id, self.block_id, self.quote, self.model_selector)


class EntityObjectV2(StrictModel):
    kind: Literal["ENTITY"]
    ref: UUID
    name: str = Field(min_length=1)


class LiteralObjectV2(StrictModel):
    kind: Literal["LITERAL"]
    value: JsonValue


class EntityReferenceV2(ContractModel):
    schema_name = "assertion-record-v2.schema.json"
    definition = "entity_reference"
    id: UUID
    entity_type: str
    label: str
    introducing_evidence: tuple[EvidenceClaimV2, ...]

    def to_domain(self) -> EntityReference:
        return EntityReference(
            self.id,
            self.entity_type,
            self.label,
            tuple(e.to_domain() for e in self.introducing_evidence),
        )


class AssertionRecordV2(ContractModel):
    schema_name = "assertion-record-v2.schema.json"
    id: UUID
    assertion_kind: Kind
    subject_ref: UUID
    object: EntityObjectV2 | LiteralObjectV2
    predicate_id: str | None
    ontology_release: str | None
    source_relation: str | None
    qualifiers: dict[str, JsonValue]
    time_mention_refs: tuple[UUID, ...]
    valid_time_claim: dict[str, JsonValue] | None
    mode: Mode
    origin: Origin
    interpretation_basis: Basis
    model_confidence: float | None
    evidence: tuple[EvidenceClaimV2, ...]

    def to_domain(self) -> AssertionCandidate:
        obj = (
            EntityObject("ENTITY", self.object.ref, self.object.name)
            if isinstance(self.object, EntityObjectV2)
            else LiteralObject("LITERAL", self.object.value)
        )
        return AssertionCandidate(
            self.id,
            self.assertion_kind,
            self.subject_ref,
            obj,
            self.predicate_id,
            self.ontology_release,
            self.source_relation,
            self.qualifiers,
            self.time_mention_refs,
            self.valid_time_claim,
            self.mode,
            self.origin,
            self.interpretation_basis,
            self.model_confidence,
            tuple(e.to_domain() for e in self.evidence),
        )


class ServerEvidence(ContractModel):
    schema_name = "assertion-admission-result-v1.schema.json"
    definition = "server_evidence"
    evidence_id: UUID
    artifact_id: UUID
    block_id: str
    quote: str
    normalization_version: Literal["f0006-grounding-v1"] = NORMALIZATION_VERSION
    precision: Literal["span", "table_cell", "block", "page", "document", "unresolved"]
    selector: dict[str, JsonValue]
    text_origin: Literal["STATED", "OCR", "TRANSCRIBED", "DESCRIBED"] | None
    origin_qualification: Literal["qualified", "legacy_unqualified"]
    producer: dict[str, JsonValue] | None
    producer_confidence: float | None


@dataclass(frozen=True)
class AdmissionMetadata:
    raw_item_sha256: str
    item_index: int
    entity_snapshots: tuple[dict[str, Any], ...]
    time_reference_snapshot: tuple[dict[str, Any], ...]
    source_hashes: Mapping[str, str]


class AdmittedAssertion(ContractModel):
    schema_name = "assertion-admission-result-v1.schema.json"
    definition = "admitted"
    record: AssertionRecordV2
    server_evidence: tuple[ServerEvidence, ...]
    review_required: bool
    reasons: tuple[str, ...]
    blocked_operations: tuple[str, ...]
    created_by: UUID
    created_at: datetime
    _metadata: AdmissionMetadata | None = PrivateAttr(default=None)

    @property
    def metadata(self) -> AdmissionMetadata:
        if self._metadata is None:
            raise ValueError("admission metadata is available only on checked items")
        return self._metadata

    def with_metadata(self, metadata: AdmissionMetadata) -> Self:
        self._metadata = metadata
        return self


class AdmissionOutcome(ContractModel):
    schema_name = "assertion-admission-result-v1.schema.json"
    definition = "outcome"
    item_index: int | None
    item_path: str
    candidate_id: UUID | None
    block_id: str | None
    disposition: Literal["REJECTED", "SIGNAL", "RUN_ISSUE"]
    reason: str
    raw_item_sha256: str
    excerpt: str | None
    model_id: str
    prompt_hash: str


class AdmissionBatch(ContractModel):
    schema_name = "assertion-admission-result-v1.schema.json"
    schema_version: Literal[1] = 1
    run_id: UUID
    artifact_id: UUID
    accepted: tuple[AdmittedAssertion, ...]
    outcomes: tuple[AdmissionOutcome, ...]
    requires_partial: bool


def parse_assertion(raw: bytes | str) -> AssertionRecordV2:
    try:
        value = decode_json(raw)
        validate_contract("assertion-record-v2.schema.json", value)
        return AssertionRecordV2.model_validate_json(canonical_json(value))
    except (ValueError, TypeError):
        raise AssertionContractError() from None


def parse_entity(
    value: EntityReference | EntityReferenceV2 | Mapping[str, Any],
) -> EntityReferenceV2:
    try:
        return EntityReferenceV2.model_validate_json(canonical_json(value))
    except (ValueError, TypeError):
        raise AssertionContractError() from None
