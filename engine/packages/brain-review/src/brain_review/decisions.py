from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

from brain_domain.review import (
    EvidenceLocator,
    ReviewDecision,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItem,
    ReviewItemStatus,
)


class ReviewItemNotFound(Exception):
    pass


class ReviewItemAlreadyDecided(Exception):
    """A distinct (non-duplicate) decision was submitted against an item that
    already carries a decision. Not one of F0001-S0004's named edge cases; a
    defensive invariant this proof does not otherwise need to relax."""


class UnresolvedEvidenceRequiresBlocked(Exception):
    """The reviewer was shown unresolved evidence but submitted an action other
    than BLOCKED (ADR-0058 invariant 37: never asked to adjudicate evidence they
    were not shown, which the panel enforces by not offering accept/correct for
    an unresolved field — this is the server-side backstop)."""


class InvalidBlockedReasonCode(Exception):
    """BLOCKED is valid only with reason code EVIDENCE_UNRESOLVED."""


class ReviewLineageChanged(Exception):
    """F0009 (PR-L2): the batch's source set changed between authorization and the
    item locks. Nothing is applied or recorded; the facade audits the failure and
    the caller resubmits as a fresh operation (sanitized 503)."""


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    review_item_id: UUID
    action: ReviewDecisionAction
    reviewer_principal_id: UUID
    assertion_version: int  # the version the reviewer saw when they decided
    reason_code: ReviewDecisionReasonCode | None = None
    corrected_value: dict | None = None
    evidence_seen: EvidenceLocator | None = None
    reviewer_comment: str | None = None


def compute_event_sha256(request: DecisionRequest) -> str:
    """The idempotency key for resubmission of a batch (F0001-S0004 Data
    Requirements: 'decision event hash unique per review item')."""
    payload = {
        "review_item_id": str(request.review_item_id),
        "action": request.action.value,
        "reviewer_principal_id": str(request.reviewer_principal_id),
        "assertion_version": request.assertion_version,
        "reason_code": request.reason_code.value if request.reason_code else None,
        "corrected_value": request.corrected_value,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class ReviewItemRepository(Protocol):
    async def get(self, review_item_id: UUID) -> ReviewItem | None: ...

    async def get_decision_by_event_sha256(
        self, review_item_id: UUID, event_sha256: str
    ) -> ReviewDecision | None: ...

    async def has_any_decision(self, review_item_id: UUID) -> bool: ...

    async def get_latest_decision(self, review_item_id: UUID) -> ReviewDecision | None: ...

    async def current_assertion_version(self, assertion_id: UUID) -> int: ...

    async def save_decision(self, decision: ReviewDecision) -> None: ...

    async def reserve_learning_reference(self, decision: ReviewDecision) -> UUID:
        """F0009 S0005: stage the one reserved future-learning identity for a new
        effective correction in the same unit of work. Never commits."""
        ...

    async def create_corrected_assertion(
        self, *, original_assertion_id: UUID, value: dict, evidence: EvidenceLocator | None
    ) -> UUID: ...

    async def mark_item_status(self, review_item_id: UUID, status: ReviewItemStatus) -> None: ...

    async def open_new_review_item_for_new_version(
        self, original_item: ReviewItem, new_version: int
    ) -> None: ...


class AuditRecorder(Protocol):
    async def record_decision(self, decision: ReviewDecision) -> None: ...


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    decision: ReviewDecision
    applied: bool
    duplicate: bool


class ReviewDecisionService:
    """Applies one reviewer decision to a review item transactionally: duplicate
    detection (event hash), staleness (assertion version), unresolved-evidence
    blocking, corrected-assertion creation, and exactly one audit event
    (F0001-S0004 acceptance criteria and edge cases). The corrected assertion's
    origin (HUMAN_REVIEW) and the original assertion's immutability are enforced by
    `create_corrected_assertion`'s implementation, not here — this service never
    mutates the original assertion row."""

    def __init__(self, repository: ReviewItemRepository, audit: AuditRecorder) -> None:
        self._repository = repository
        self._audit = audit

    async def submit(self, request: DecisionRequest) -> DecisionOutcome:
        item = await self._repository.get(request.review_item_id)
        if item is None:
            raise ReviewItemNotFound(str(request.review_item_id))
        if item.review_batch_id is None:
            raise ValueError(f"review item {item.id} has not been assembled into a batch")

        event_sha256 = compute_event_sha256(request)
        existing = await self._repository.get_decision_by_event_sha256(item.id, event_sha256)
        if existing is not None:
            return DecisionOutcome(decision=existing, applied=False, duplicate=True)

        if await self._repository.has_any_decision(item.id):
            raise ReviewItemAlreadyDecided(str(item.id))

        current_version = await self._repository.current_assertion_version(item.assertion_id)
        if current_version != request.assertion_version:
            decision = ReviewDecision(
                id=uuid4(),
                review_item_id=item.id,
                review_batch_id=item.review_batch_id,
                action=request.action,
                reviewer_principal_id=request.reviewer_principal_id,
                decided_at=datetime.now(UTC),
                assertion_version=request.assertion_version,
                stale=True,
                event_sha256=event_sha256,
                reason_code=request.reason_code,
                # F0009 S0002 AC5: the non-applied submission stays attributable.
                corrected_value=request.corrected_value,
                evidence=request.evidence_seen,
                reviewer_comment=request.reviewer_comment,
            )
            await self._repository.save_decision(decision)
            await self._audit.record_decision(decision)
            await self._repository.open_new_review_item_for_new_version(item, current_version)
            return DecisionOutcome(decision=decision, applied=False, duplicate=False)

        evidence_unresolved = (
            request.evidence_seen is not None and request.evidence_seen.precision == "unresolved"
        )
        if evidence_unresolved and request.action != ReviewDecisionAction.BLOCKED:
            raise UnresolvedEvidenceRequiresBlocked(str(item.id))

        if request.action == ReviewDecisionAction.BLOCKED:
            if request.reason_code != ReviewDecisionReasonCode.EVIDENCE_UNRESOLVED:
                raise InvalidBlockedReasonCode(str(item.id))
            decision = ReviewDecision(
                id=uuid4(),
                review_item_id=item.id,
                review_batch_id=item.review_batch_id,
                action=request.action,
                reviewer_principal_id=request.reviewer_principal_id,
                decided_at=datetime.now(UTC),
                assertion_version=request.assertion_version,
                stale=False,
                event_sha256=event_sha256,
                reason_code=request.reason_code,
                evidence=request.evidence_seen,
            )
            await self._repository.save_decision(decision)
            await self._audit.record_decision(decision)
            # BLOCKED creates no assertion and the review item stays open.
            return DecisionOutcome(decision=decision, applied=True, duplicate=False)

        corrected_assertion_id = None
        if request.action == ReviewDecisionAction.CORRECT:
            corrected_assertion_id = await self._repository.create_corrected_assertion(
                original_assertion_id=item.assertion_id,
                value=request.corrected_value or {},
                evidence=request.evidence_seen,
            )

        decision = ReviewDecision(
            id=uuid4(),
            review_item_id=item.id,
            review_batch_id=item.review_batch_id,
            action=request.action,
            reviewer_principal_id=request.reviewer_principal_id,
            decided_at=datetime.now(UTC),
            assertion_version=request.assertion_version,
            stale=False,
            event_sha256=event_sha256,
            reason_code=request.reason_code,
            corrected_value=request.corrected_value,
            corrected_assertion_id=corrected_assertion_id,
            evidence=request.evidence_seen,
            reviewer_comment=request.reviewer_comment,
        )
        await self._repository.save_decision(decision)
        if corrected_assertion_id is not None:
            # F0009 S0005 AC2: same unit of work; a failure here propagates before
            # audit/commit and the facade rolls the whole correction back.
            await self._repository.reserve_learning_reference(decision)
        await self._audit.record_decision(decision)
        await self._repository.mark_item_status(item.id, ReviewItemStatus.DECIDED)
        return DecisionOutcome(decision=decision, applied=True, duplicate=False)


AttemptOutcome = Literal["ALREADY_DECIDED", "BATCH_REFUSED"]


@dataclass(frozen=True, slots=True)
class RefusedSubmission:
    """One nonduplicate submission of a refused batch (F0009 S0002 AC6)."""

    request: DecisionRequest
    item: ReviewItem
    event_sha256: str
    outcome: AttemptOutcome


@dataclass(frozen=True, slots=True)
class RefusedBatch:
    """Internal tagged result: only refusal records and their audit commit, and the
    caller then raises its existing sanitized 422. Not an HTTP response."""

    attempt_ids: tuple[UUID, ...]


class BatchPreflightRepository(Protocol):
    async def get_decision_by_event_sha256(
        self, review_item_id: UUID, event_sha256: str
    ) -> ReviewDecision | None: ...

    async def has_any_decision(self, review_item_id: UUID) -> bool: ...


async def preflight_batch(
    repository: BatchPreflightRepository,
    submissions: Sequence[tuple[ReviewItem, DecisionRequest]],
) -> list[RefusedSubmission]:
    """Decide, before any effect, whether a batch must be refused (assembly plan
    Step 3.3-3.4). Replay identity comes only from ReviewDecision rows: a stored
    refused attempt never short-circuits a request (operator decision 2026-11-24,
    plan-review PR-H1). Items must already be locked by the caller.

    Returns an empty list for a clean batch. Otherwise every nonduplicate
    submission is refused: ALREADY_DECIDED where the item carries a distinct
    decision, BATCH_REFUSED for the rest. Duplicates (an exact prior event) are
    replays and create no attempt."""
    pending: list[tuple[ReviewItem, DecisionRequest, str, bool]] = []
    conflict = False
    for item, request in submissions:
        event_sha256 = compute_event_sha256(request)
        if await repository.get_decision_by_event_sha256(item.id, event_sha256) is not None:
            continue
        decided = await repository.has_any_decision(item.id)
        conflict |= decided
        pending.append((item, request, event_sha256, decided))
    if not conflict:
        return []
    return [
        RefusedSubmission(
            request=request,
            item=item,
            event_sha256=event_sha256,
            outcome="ALREADY_DECIDED" if decided else "BATCH_REFUSED",
        )
        for item, request, event_sha256, decided in pending
    ]


def submitted_now() -> datetime:
    return datetime.now(UTC)
