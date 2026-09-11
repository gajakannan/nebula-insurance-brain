from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ChangeReason(StrEnum):
    SUPERSEDED = "superseded"
    CORRECTED = "corrected"
    RETRACTED = "retracted"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    MERGED = "merged"
    SPLIT = "split"


@dataclass(frozen=True, slots=True)
class FactSlot:
    id: UUID
    entity_id: UUID
    slot_type: str
    tenant_id: UUID
    knowledge_base_id: UUID


@dataclass(frozen=True, slots=True)
class CommitProposal:
    """One canonical-commit proposal (master blueprint section 109.2,
    F0001-S0005). Matches `planning-mds/schemas/canonical-commit-request
    .schema.json`."""

    slot_id: UUID
    value: Mapping[str, Any]
    valid_from: datetime
    valid_to: datetime | None
    change_reason: ChangeReason | None
    evidence_refs: tuple[UUID, ...]
    review_decision_id: UUID | None
    source_received_at: datetime
    artifact_created_at: datetime
    assertion_created_at: datetime
    expected_current_version_id: UUID | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CommitResult:
    commit_id: UUID
    fact_version_ids: tuple[UUID, ...]
    canonical_accepted_at: datetime


@dataclass(frozen=True, slots=True)
class FactVersion:
    """One row read back from `canonical_fact_version` (API/read-side shape;
    `valid`/`recorded` are resolved half-open ranges, `end=None` means open)."""

    id: UUID
    fact_slot_id: UUID
    value: Mapping[str, Any]
    valid_start: datetime
    valid_end: datetime | None
    recorded_start: datetime
    recorded_end: datetime | None
    change_reason: ChangeReason | None
    evidence_refs: tuple[UUID, ...]
    commit_id: UUID
    canonical_accepted_at: datetime
