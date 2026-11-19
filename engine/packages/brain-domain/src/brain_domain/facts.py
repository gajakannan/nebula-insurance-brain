from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from brain_domain.temporal import EndState, VersionTemporal


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
    .schema.json`: legacy pilot slots send `valid_from`/`valid_to`, and
    identity-v1 slots send the raw `fact-temporal/v1` block in `temporal`, which
    the commit service parses so that each refusal has its own code (F0008)."""

    slot_id: UUID
    value: Mapping[str, Any]
    valid_from: datetime | None
    valid_to: datetime | None
    change_reason: ChangeReason | None
    evidence_refs: tuple[UUID, ...]
    review_decision_id: UUID | None
    source_received_at: datetime
    artifact_created_at: datetime
    assertion_created_at: datetime
    expected_current_version_id: UUID | None
    idempotency_key: str
    temporal: Mapping[str, Any] | None = None


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
    # F0008 (S0003 AC3, S0006 AC5): remainders copy these from their predecessor,
    # and the read returns them. `temporal` is None for a legacy pilot version.
    review_decision_id: UUID | None = None
    source_received_at: datetime | None = None
    artifact_created_at: datetime | None = None
    assertion_created_at: datetime | None = None
    temporal: VersionTemporal | None = None
    ending_evidence_refs: tuple[UUID, ...] = ()

    @property
    def valid_to_state(self) -> EndState:
        """S0007 AC2: a legacy row has no stored end state, so a NULL upper bound
        reads as OPEN and a finite one as BOUNDED. Nothing is invented."""
        if self.temporal is not None:
            return self.temporal.valid_to_state
        return EndState.OPEN if self.valid_end is None else EndState.BOUNDED
