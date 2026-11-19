from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from brain_domain.facts import CommitResult, FactVersion
from brain_temporal.reader import ValidityUnknown
from pydantic import BaseModel, ConfigDict, model_validator

ChangeReasonLiteral = Literal[
    "superseded", "corrected", "retracted", "expired", "invalidated", "merged", "split"
]


class CommitProposalIn(BaseModel):
    """Request body for `POST /facts/{factSlotId}/commits` — matches
    `planning-mds/schemas/canonical-commit-request.schema.json` (F0001-S0005)."""

    model_config = ConfigDict(extra="forbid")

    value: dict
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    change_reason: ChangeReasonLiteral | None = None
    evidence_refs: list[UUID]
    review_decision_id: UUID | None = None
    source_received_at: datetime
    artifact_created_at: datetime
    assertion_created_at: datetime
    expected_current_version_id: UUID | None = None
    idempotency_key: str
    # F0008: the raw fact-temporal/v1 block. The commit service parses it so that
    # each structural fault has its own reason code (ADR-0078).
    temporal: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _one_time_shape(self) -> CommitProposalIn:
        """Exactly one of the pilot `valid_from` or the `temporal` block."""
        if (self.valid_from is None) == (self.temporal is None):
            raise ValueError("send exactly one of valid_from or temporal")
        if self.temporal is not None and self.valid_to is not None:
            raise ValueError("valid_to is derived from temporal")
        return self


class CommitResponseOut(BaseModel):
    """Matches `planning-mds/schemas/canonical-commit-response.schema.json`."""

    model_config = ConfigDict(extra="forbid")

    commit_id: UUID
    fact_version_ids: list[UUID]
    canonical_accepted_at: datetime

    @classmethod
    def from_domain(cls, result: CommitResult) -> CommitResponseOut:
        return cls(
            commit_id=result.commit_id,
            fact_version_ids=list(result.fact_version_ids),
            canonical_accepted_at=result.canonical_accepted_at,
        )


class FactVersionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    fact_slot_id: UUID
    value: dict
    valid_start: datetime
    valid_end: datetime | None
    recorded_start: datetime
    recorded_end: datetime | None
    change_reason: ChangeReasonLiteral | None
    evidence_refs: list[UUID]
    commit_id: UUID
    canonical_accepted_at: datetime
    # F0008 (S0006 AC5), additive and optional.
    review_decision_id: UUID | None = None
    source_received_at: datetime | None = None
    artifact_created_at: datetime | None = None
    assertion_created_at: datetime | None = None
    temporal: dict[str, Any] | None = None

    @classmethod
    def from_domain(cls, version: FactVersion) -> FactVersionOut:
        return cls(
            id=version.id,
            fact_slot_id=version.fact_slot_id,
            value=dict(version.value),
            valid_start=version.valid_start,
            valid_end=version.valid_end,
            recorded_start=version.recorded_start,
            recorded_end=version.recorded_end,
            change_reason=version.change_reason.value if version.change_reason else None,
            evidence_refs=list(version.evidence_refs),
            commit_id=version.commit_id,
            canonical_accepted_at=version.canonical_accepted_at,
            review_decision_id=version.review_decision_id,
            source_received_at=version.source_received_at,
            artifact_created_at=version.artifact_created_at,
            assertion_created_at=version.assertion_created_at,
            temporal=version.temporal.to_json() if version.temporal else None,
        )


class FactValidityUnknownOut(BaseModel):
    """F0008 additive 200 variant (`fact-temporal-v1#/$defs/validity_unknown_read`).
    No value is disclosed."""

    model_config = ConfigDict(extra="forbid")

    fact_slot_id: UUID
    validity: Literal["UNKNOWN"] = "UNKNOWN"
    reason: Literal["UNKNOWN_END_WINDOW", "BEFORE_ATTESTATION_FLOOR"]
    version_id: UUID
    temporal: dict[str, Any]

    @classmethod
    def from_domain(cls, result: ValidityUnknown) -> FactValidityUnknownOut:
        return cls(
            fact_slot_id=result.version.fact_slot_id,
            reason=result.reason,
            version_id=result.version_id,
            temporal=result.temporal.to_json(),
        )
