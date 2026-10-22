"""Append-only document date contracts and trusted provenance ports.

No verifier is enabled by default. Schema-valid receipts are not authority;
the owning human-decision integration must supply the trusted implementations.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date as CalendarDate
from datetime import datetime
from typing import Annotated, Any, Literal, Protocol, Self
from uuid import UUID

from pydantic import ConfigDict, Field, StrictInt, field_validator, model_validator

from brain_content.contracts import decode_json, validate_contract, wire_value
from brain_content.records import StrictModel
from brain_content.validation import VerifiedBundle

Precision = Literal["YEAR", "MONTH", "DAY"]


class DateBasisInvalid(ValueError):
    code = "DATE_BASIS_INVALID"


class HumanBasisUnavailable(DateBasisInvalid):
    code = "HUMAN_BASIS_UNAVAILABLE"


class IdempotencyConflict(ValueError):
    code = "IDEMPOTENCY_CONFLICT"


class DateSelectionStale(ValueError):
    code = "DATE_SELECTION_STALE"


class DocumentDateValue(StrictModel):
    precision: Precision
    value: str

    @model_validator(mode="after")
    def calendar(self) -> Self:
        patterns = {
            "YEAR": r"[0-9]{4}",
            "MONTH": r"[0-9]{4}-[0-9]{2}",
            "DAY": r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
        }
        if not re.fullmatch(patterns[self.precision], self.value):
            raise DateBasisInvalid("invalid date precision")
        try:
            suffix = {"YEAR": "-01-01", "MONTH": "-01", "DAY": ""}[self.precision]
            CalendarDate.fromisoformat(self.value + suffix)
        except ValueError:
            raise DateBasisInvalid("invalid calendar date") from None
        return self


class ContentDateBasis(StrictModel):
    kind: Literal["CONTENT"]
    artifact_id: UUID
    block_id: str = Field(min_length=1)
    record_ordinal: StrictInt = Field(ge=0)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    quote: str = Field(min_length=1)


class SourceMetadataDateInput(StrictModel):
    kind: Literal["SOURCE_METADATA"]
    system: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    field: str = Field(min_length=1)


class SourceMetadataDateBasis(SourceMetadataDateInput):
    source_value: str = Field(min_length=1)
    snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def snapshot(self) -> Self:
        if self.snapshot_sha256 != metadata_snapshot_hash(
            self.system, self.record_id, self.field, self.source_value
        ):
            raise DateBasisInvalid("source metadata snapshot mismatch")
        reject_processing_date(self.field)
        return self


class HumanDateInput(StrictModel):
    kind: Literal["HUMAN"]
    decision_id: UUID


class DateWireModel(StrictModel):
    @field_validator("created_at", "decided_at", mode="before", check_fields=False)
    @classmethod
    def timestamp(cls, value: Any) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise DateBasisInvalid("date record time requires an explicit timezone")
        return value


class HumanDecisionReceipt(DateWireModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True, frozen=True)
    decision_id: UUID
    actor_principal_id: UUID
    authorization_decision_id: UUID
    decided_at: datetime
    receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def aware(self) -> Self:
        if self.decided_at.tzinfo is None or self.decided_at.utcoffset() is None:
            raise DateBasisInvalid("human decision time requires timezone")
        return self


class HumanDateBasis(HumanDecisionReceipt):
    kind: Literal["HUMAN"]


class VerifiedHumanDateBasis(HumanDecisionReceipt):
    document_version_id: UUID
    date_value: str
    precision: Precision


class VerifiedHumanSelectionBasis(HumanDecisionReceipt):
    document_version_id: UUID
    candidate_id: UUID | None
    expected_selection_id: UUID | None


DateBasisInput = Annotated[
    ContentDateBasis | SourceMetadataDateInput | HumanDateInput, Field(discriminator="kind")
]
DateBasis = Annotated[
    ContentDateBasis | SourceMetadataDateBasis | HumanDateBasis, Field(discriminator="kind")
]


class DateRecord(DateWireModel):
    contract_version: Literal[1]
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    document_version_id: UUID
    created_at: datetime
    actor_principal_id: UUID
    authorization_decision_id: UUID
    authorization_audit_event_id: UUID
    idempotency_key: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def input_contract(cls, value: Any) -> Any:
        validate_contract("document-date-record.schema.json", wire_value(value))
        return value

    @model_validator(mode="after")
    def contract(self) -> Self:
        validate_contract("document-date-record.schema.json", self.model_dump(mode="json"))
        return self


class DocumentDateCandidate(DateRecord):
    record_type: Literal["candidate"]
    date: DocumentDateValue
    basis: DateBasis
    supersedes_id: UUID | None


class DocumentDateSelection(DateRecord):
    record_type: Literal["selection"]
    candidate_id: UUID | None
    previous_selection_id: UUID | None
    sequence: StrictInt = Field(ge=1)
    reason: str = Field(min_length=1)
    human_decision: HumanDecisionReceipt


class DocumentDateView(StrictModel):
    document_version_id: UUID
    candidates: tuple[DocumentDateCandidate, ...]
    selection: DocumentDateSelection | None
    selected_date: DocumentDateValue | None


class HumanDateDecisionVerifier(Protocol):
    def verify(
        self, decision_id: UUID, *, document_version_id: UUID, date_value: str, precision: str
    ) -> VerifiedHumanDateBasis: ...


class HumanDateSelectionVerifier(Protocol):
    def verify_selection(
        self,
        decision_id: UUID,
        *,
        document_version_id: UUID,
        candidate_id: UUID | None,
        expected_selection_id: UUID | None,
    ) -> VerifiedHumanSelectionBasis: ...


class SourceMetadataDateVerifier(Protocol):
    def verify(
        self,
        *,
        document_version_id: UUID,
        system: str,
        record_id: str,
        field: str,
        date: DocumentDateValue,
    ) -> SourceMetadataDateBasis: ...


class UnavailableHumanDateVerifier:
    def verify(
        self, decision_id: UUID, *, document_version_id: UUID, date_value: str, precision: str
    ) -> VerifiedHumanDateBasis:
        raise HumanBasisUnavailable("human date authority unavailable")

    def verify_selection(
        self,
        decision_id: UUID,
        *,
        document_version_id: UUID,
        candidate_id: UUID | None,
        expected_selection_id: UUID | None,
    ) -> VerifiedHumanSelectionBasis:
        raise HumanBasisUnavailable("human selection authority unavailable")


class UnavailableSourceMetadataVerifier:
    def verify(
        self,
        *,
        document_version_id: UUID,
        system: str,
        record_id: str,
        field: str,
        date: DocumentDateValue,
    ) -> SourceMetadataDateBasis:
        raise DateBasisInvalid("trusted source metadata unavailable")


def metadata_snapshot_hash(system: str, record_id: str, field: str, source_value: str) -> str:
    return command_hash(
        {"system": system, "record_id": record_id, "field": field, "source_value": source_value}
    )


def command_hash(command: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            wire_value(command),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def reject_processing_date(field: str) -> None:
    normalized = re.sub(r"[^a-z]", "", field.lower())
    if any(
        word in normalized
        for word in ("receipt", "received", "upload", "ingest", "extract", "import", "processed")
    ):
        raise DateBasisInvalid("processing time is not the document date")


def verify_content_date_basis(bundle: VerifiedBundle, basis: ContentDateBasis) -> None:
    if bundle.key.artifact_id != basis.artifact_id:
        raise DateBasisInvalid("content date belongs to another artifact")
    lines = bundle.files["blocks.jsonl"].splitlines()
    if basis.record_ordinal >= len(lines):
        raise DateBasisInvalid("content date record is absent")
    line = lines[basis.record_ordinal]
    if hashlib.sha256(line).hexdigest() != basis.record_sha256:
        raise DateBasisInvalid("content date record changed")
    record = decode_json(line)
    if (
        not isinstance(record, dict)
        or record.get("block_id") != basis.block_id
        or not isinstance(record.get("text"), str)
        or basis.quote not in record["text"]
    ):
        raise DateBasisInvalid("content date quote does not match the exact record")
