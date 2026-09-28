from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.audit import AuditEvent
from brain_domain.authx import AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.facts import ChangeReason, FactVersion
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecision,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItem,
    ReviewItemStatus,
    ReviewItemType,
)
from brain_security.audit import AuditEventRepository
from brain_temporal.outbox import OutboxEvent
from brain_temporal.ranges import TimeRange
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession

from brain_persistence.authx import audit_timestamp
from brain_persistence.models import (
    Assertion,
    AuditEventRow,
    CanonicalCommitRow,
    CanonicalFactChangeRow,
    CanonicalFactVersionRow,
    FactSlotRow,
    OutboxEventRow,
    ReviewDecisionRow,
    ReviewItemRow,
)
from brain_persistence.tenancy import inherit_resource_access


class ReviewDecisionAuditSink:
    """`brain_review.decisions.AuditRecorder` over an `AuditEventRepository`. Audits
    the *outcome* of a review decision (F0001-S0004) and references the durable
    authorization decision that permitted it (F0002-S0006): the authorization's
    policy hash, authority revision and decision ID replace the F0001 placeholder
    "n/a"/0 values, and the reviewer is the authenticated principal."""

    def __init__(
        self,
        repository: AuditEventRepository,
        authorizations: dict[UUID, AuthorizationDecision],
    ) -> None:
        self._repository = repository
        self._authorizations = authorizations

    async def record_decision(self, decision: ReviewDecision) -> None:
        authorization = self._authorizations[decision.review_item_id]
        await self._repository.append(
            AuditEvent(
                id=uuid4(),
                occurred_at=decision.decided_at,
                actor_principal_id=decision.reviewer_principal_id,
                delegate_principal_id=authorization.executor_principal_id,
                resource_type="review_item",
                resource_id=decision.review_item_id,
                action=decision.action.value,
                decision=not decision.stale,
                reason_code=decision.reason_code.value if decision.reason_code else "n/a",
                policy_hash=authorization.policy_hash,
                grant_revision=authorization.grant_revision,
                trace_id=decision.event_sha256,
                decision_id=authorization.decision_id,
                event_type="review_decision_recorded",
                operation_outcome="succeeded",
                payload={
                    "review_decision_id": str(decision.id),
                    "authorization_decision_id": str(authorization.decision_id),
                    "stale": decision.stale,
                },
            )
        )


class SqlAlchemyAuditEventRepository:
    """`brain_security.audit.AuditEventRepository` over SQLAlchemy (F0001-S0006)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: AuditEvent) -> None:
        self._session.add(
            AuditEventRow(
                id=event.id,
                occurred_at=audit_timestamp(event.occurred_at),
                actor_principal_id=event.actor_principal_id,
                delegate_principal_id=event.delegate_principal_id,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action,
                decision=event.decision,
                reason_code=event.reason_code,
                policy_hash=event.policy_hash,
                grant_revision=event.grant_revision,
                trace_id=event.trace_id,
                decision_id=event.decision_id,
                event_type=event.event_type,
                operation_outcome=event.operation_outcome,
                payload=event.payload,
            )
        )
        await self._session.flush()


def _evidence_from_json(data: dict | None) -> EvidenceLocator | None:
    if data is None:
        return None
    return EvidenceLocator(
        source=data["source"],
        precision=data["precision"],
        part=data.get("part"),
        unresolved_reason=data.get("unresolved_reason"),
        selector=tuple(data.get("selector", ())),
    )


def _evidence_to_json(evidence: EvidenceLocator | None) -> dict | None:
    if evidence is None:
        return None
    return {
        "source": evidence.source,
        "precision": evidence.precision,
        "part": evidence.part,
        "unresolved_reason": evidence.unresolved_reason,
        "selector": list(evidence.selector),
    }


def _review_item_from_row(row: ReviewItemRow) -> ReviewItem:
    return ReviewItem(
        id=row.id,
        type=ReviewItemType(row.type),
        status=ReviewItemStatus(row.status),
        assertion_id=row.assertion_id,
        assertion_version=row.assertion_version,
        tenant_id=row.tenant_id,
        knowledge_base_id=row.knowledge_base_id,
        created_at=row.created_at,
        review_batch_id=row.review_batch_id,
        evidence=_evidence_from_json(row.evidence),
    )


def _decision_from_row(row: ReviewDecisionRow) -> ReviewDecision:
    return ReviewDecision(
        id=row.id,
        review_item_id=row.review_item_id,
        review_batch_id=row.review_batch_id,
        action=ReviewDecisionAction(row.action),
        reviewer_principal_id=row.reviewer_principal_id,
        decided_at=row.decided_at,
        assertion_version=row.assertion_version,
        stale=row.stale,
        event_sha256=row.event_sha256,
        reason_code=ReviewDecisionReasonCode(row.reason_code) if row.reason_code else None,
        corrected_value=row.corrected_value,
        corrected_assertion_id=row.corrected_assertion_id,
        evidence=_evidence_from_json(row.evidence),
        reviewer_comment=row.reviewer_comment,
    )


class SqlAlchemyReviewItemRepository:
    """`brain_review.decisions.ReviewItemRepository` over SQLAlchemy (F0001-S0004).
    `actor_id` attributes derived security metadata to the authenticated reviewer."""

    def __init__(self, session: AsyncSession, *, actor_id: UUID | None = None) -> None:
        self._session = session
        self._actor_id = actor_id

    async def get(self, review_item_id: UUID) -> ReviewItem | None:
        row = await self._session.get(ReviewItemRow, review_item_id)
        return _review_item_from_row(row) if row is not None else None

    async def get_decision_by_event_sha256(
        self, review_item_id: UUID, event_sha256: str
    ) -> ReviewDecision | None:
        row = (
            await self._session.execute(
                select(ReviewDecisionRow).where(
                    ReviewDecisionRow.review_item_id == review_item_id,
                    ReviewDecisionRow.event_sha256 == event_sha256,
                )
            )
        ).scalar_one_or_none()
        return _decision_from_row(row) if row is not None else None

    async def has_any_decision(self, review_item_id: UUID) -> bool:
        row = (
            await self._session.execute(
                select(ReviewDecisionRow.id).where(
                    ReviewDecisionRow.review_item_id == review_item_id
                )
            )
        ).first()
        return row is not None

    async def get_latest_decision(self, review_item_id: UUID) -> ReviewDecision | None:
        row = (
            await self._session.execute(
                select(ReviewDecisionRow)
                .where(ReviewDecisionRow.review_item_id == review_item_id)
                .order_by(ReviewDecisionRow.decided_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _decision_from_row(row) if row is not None else None

    async def current_assertion_version(self, assertion_id: UUID) -> int:
        row = await self._session.get(Assertion, assertion_id)
        return row.version if row is not None else 1

    async def save_decision(self, decision: ReviewDecision) -> None:
        item = await self._session.get(ReviewItemRow, decision.review_item_id)
        if item is None:
            raise ValueError(f"review item {decision.review_item_id} not found")
        self._session.add(
            ReviewDecisionRow(
                id=decision.id,
                review_item_id=decision.review_item_id,
                review_batch_id=decision.review_batch_id,
                action=decision.action.value,
                reason_code=decision.reason_code.value if decision.reason_code else None,
                corrected_value=decision.corrected_value,
                corrected_assertion_id=decision.corrected_assertion_id,
                evidence=_evidence_to_json(decision.evidence),
                reviewer_principal_id=decision.reviewer_principal_id,
                reviewer_comment=decision.reviewer_comment,
                assertion_version=decision.assertion_version,
                stale=decision.stale,
                event_sha256=decision.event_sha256,
                tenant_id=item.tenant_id,
                knowledge_base_id=item.knowledge_base_id,
            )
        )
        await self._session.flush()

    async def create_corrected_assertion(
        self, *, original_assertion_id: UUID, value: dict, evidence: EvidenceLocator | None
    ) -> UUID:
        original = await self._session.get(Assertion, original_assertion_id)
        if original is None:
            raise ValueError(f"original assertion {original_assertion_id} not found")

        corrected = Assertion(
            id=uuid4(),
            run_id=None,
            origin="HUMAN_REVIEW",
            original_assertion_id=original.id,
            subject_type=original.subject_type,
            slot_type=original.slot_type,
            value=value,
            model_confidence=None,
            interpretation_basis="EXPLICIT",
            # A correction inherits its original's ownership (assembly plan Step 1).
            tenant_id=original.tenant_id,
            knowledge_base_id=original.knowledge_base_id,
        )
        self._session.add(corrected)
        await self._session.flush()
        return corrected.id

    async def mark_item_status(self, review_item_id: UUID, status: ReviewItemStatus) -> None:
        row = await self._session.get(ReviewItemRow, review_item_id)
        if row is not None:
            row.status = status.value
            await self._session.flush()

    async def open_new_review_item_for_new_version(
        self, original_item: ReviewItem, new_version: int
    ) -> None:
        new_item_id = uuid4()
        self._session.add(
            ReviewItemRow(
                id=new_item_id,
                type=original_item.type.value,
                status=ReviewItemStatus.OPEN.value,
                assertion_id=original_item.assertion_id,
                assertion_version=new_version,
                tenant_id=original_item.tenant_id,
                knowledge_base_id=original_item.knowledge_base_id,
                evidence=_evidence_to_json(original_item.evidence),
            )
        )
        await self._session.flush()
        # The re-opened task carries its original's security metadata (F0002-S0004).
        actor_id = self._actor_id
        if actor_id is None:
            raise ValueError("re-opening a review task requires the authenticated actor")
        await self._session.run_sync(
            lambda session: inherit_resource_access(
                session,
                ResourceKey(ResourceType.REVIEW_TASK, original_item.id),
                ResourceKey(ResourceType.REVIEW_TASK, new_item_id),
                actor_id=actor_id,
                at=datetime.now(UTC),
            )
        )


def _to_pg_range(span: TimeRange) -> Range:
    return Range(span.start, span.end, bounds="[)")


def _from_pg_range(value: Range) -> TimeRange:
    assert value.lower is not None  # our ranges are always lower-bounded
    return TimeRange(start=value.lower, end=value.upper)


def _fact_version_from_row(row: CanonicalFactVersionRow) -> FactVersion:
    valid = _from_pg_range(row.valid)
    recorded = _from_pg_range(row.recorded)
    return FactVersion(
        id=row.id,
        fact_slot_id=row.slot_id,
        value=row.value,
        valid_start=valid.start,
        valid_end=valid.end,
        recorded_start=recorded.start,
        recorded_end=recorded.end,
        change_reason=ChangeReason(row.change_reason) if row.change_reason else None,
        evidence_refs=tuple(UUID(e) for e in row.evidence.get("refs", [])),
        commit_id=row.commit_id,
        canonical_accepted_at=row.canonical_accepted_at,
    )


class SqlAlchemyFactCommitRepository:
    """`brain_temporal.commit.FactCommitRepository` over SQLAlchemy/Postgres
    (F0001-S0005). The `EEXCLUDE USING gist` constraint on `canonical_fact_version`
    is the database-level backstop; `lock_slot`'s `SELECT ... FOR UPDATE` is what
    actually serializes concurrent commits on the same slot so the algorithm never
    relies on the constraint to arbitrate a race — the constraint only fires if the
    algorithm itself has a bug."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_slot(self, slot_id: UUID) -> tuple[UUID, UUID] | None:
        row = (
            await self._session.execute(
                select(FactSlotRow.tenant_id, FactSlotRow.knowledge_base_id)
                .where(FactSlotRow.id == slot_id)
                .with_for_update()
            )
        ).first()
        return (row.tenant_id, row.knowledge_base_id) if row is not None else None

    async def get_slot(self, slot_id: UUID) -> tuple[UUID, UUID] | None:
        """Same lookup as `lock_slot` without the row lock — used by the read-only
        `GET /facts/{factSlotId}` route, which never contends with a commit."""
        row = (
            await self._session.execute(
                select(FactSlotRow.tenant_id, FactSlotRow.knowledge_base_id).where(
                    FactSlotRow.id == slot_id
                )
            )
        ).first()
        return (row.tenant_id, row.knowledge_base_id) if row is not None else None

    async def current_versions(self, slot_id: UUID) -> tuple[FactVersion, ...]:
        rows = (
            (
                await self._session.execute(
                    select(CanonicalFactVersionRow).where(
                        CanonicalFactVersionRow.slot_id == slot_id,
                        func.upper_inf(CanonicalFactVersionRow.recorded),
                    )
                )
            )
            .scalars()
            .all()
        )
        return tuple(_fact_version_from_row(row) for row in rows)

    async def close_recorded(self, version_id: UUID, at: datetime) -> None:
        row = await self._session.get(CanonicalFactVersionRow, version_id)
        if row is not None:
            row.recorded = _to_pg_range(TimeRange(row.recorded.lower, at))
            await self._session.flush()

    async def resolve_at(
        self, slot_id: UUID, *, valid_as_of: datetime, known_as_of: datetime
    ) -> FactVersion | None:
        """Read-side lookup for `GET /facts/{factSlotId}` (master blueprint section
        109.2: `valid @> validAsOf AND recorded @> knownAsOf`). Not part of
        `FactCommitRepository` — the commit algorithm never needs point lookups."""
        row = (
            await self._session.execute(
                select(CanonicalFactVersionRow).where(
                    CanonicalFactVersionRow.slot_id == slot_id,
                    CanonicalFactVersionRow.valid.op("@>")(valid_as_of),
                    CanonicalFactVersionRow.recorded.op("@>")(known_as_of),
                )
            )
        ).scalar_one_or_none()
        return _fact_version_from_row(row) if row is not None else None

    async def insert_version(
        self,
        *,
        version_id: UUID,
        slot_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        value: dict,
        valid: TimeRange,
        recorded: TimeRange,
        change_reason: ChangeReason | None,
        evidence_refs: tuple[UUID, ...],
        review_decision_id: UUID | None,
        commit_id: UUID,
        source_received_at: datetime,
        artifact_created_at: datetime,
        assertion_created_at: datetime,
        canonical_accepted_at: datetime,
    ) -> None:
        self._session.add(
            CanonicalFactVersionRow(
                id=version_id,
                slot_id=slot_id,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                value=value,
                valid=_to_pg_range(valid),
                recorded=_to_pg_range(recorded),
                change_reason=change_reason.value if change_reason else None,
                evidence={"refs": [str(e) for e in evidence_refs]},
                review_decision_id=review_decision_id,
                commit_id=commit_id,
                source_received_at=source_received_at,
                artifact_created_at=artifact_created_at,
                assertion_created_at=assertion_created_at,
                canonical_accepted_at=canonical_accepted_at,
            )
        )
        await self._session.flush()

    async def insert_change(
        self,
        *,
        reason: ChangeReason,
        from_version_id: UUID | None,
        to_version_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> None:
        self._session.add(
            CanonicalFactChangeRow(
                id=uuid4(),
                reason=reason.value,
                from_version_id=from_version_id,
                to_version_id=to_version_id,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
            )
        )
        await self._session.flush()

    async def register_commit(
        self,
        *,
        commit_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        authorization_decision_id: UUID | None,
        at: datetime,
    ) -> None:
        """Commit ownership registry row; the outbox references it (F0002-S0001)."""
        self._session.add(
            CanonicalCommitRow(
                id=commit_id,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                authorization_decision_id=authorization_decision_id,
                created_at=at,
            )
        )
        await self._session.flush()

    async def write_outbox(self, commit_id: UUID, payload: dict) -> None:
        self._session.add(OutboxEventRow(id=uuid4(), commit_id=commit_id, payload=payload))
        await self._session.flush()


class SqlAlchemyOutboxReader:
    """`brain_temporal.outbox.OutboxReader` over SQLAlchemy (F0001-S0005)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def unprocessed(self, limit: int = 100) -> tuple[OutboxEvent, ...]:
        rows = (
            (
                await self._session.execute(
                    select(OutboxEventRow)
                    .where(OutboxEventRow.processed_at.is_(None))
                    .order_by(OutboxEventRow.created_at)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return tuple(
            OutboxEvent(
                id=row.id,
                commit_id=row.commit_id,
                payload=row.payload,
                created_at=row.created_at,
                processed_at=row.processed_at,
            )
            for row in rows
        )

    async def mark_processed(self, event_id: UUID, *, processed_at: datetime) -> None:
        row = await self._session.get(OutboxEventRow, event_id)
        if row is not None:
            row.processed_at = processed_at
            await self._session.flush()
