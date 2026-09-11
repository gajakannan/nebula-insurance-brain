from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from brain_domain.facts import CommitResult, FactVersion
from pydantic import BaseModel, ConfigDict

ChangeReasonLiteral = Literal[
    "superseded", "corrected", "retracted", "expired", "invalidated", "merged", "split"
]


class CommitProposalIn(BaseModel):
    """Request body for `POST /facts/{factSlotId}/commits` — matches
    `planning-mds/schemas/canonical-commit-request.schema.json` (F0001-S0005)."""

    model_config = ConfigDict(extra="forbid")

    value: dict
    valid_from: datetime
    valid_to: datetime | None = None
    change_reason: ChangeReasonLiteral | None = None
    evidence_refs: list[UUID]
    review_decision_id: UUID | None = None
    source_received_at: datetime
    artifact_created_at: datetime
    assertion_created_at: datetime
    expected_current_version_id: UUID | None = None
    idempotency_key: str


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
        )
