from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from brain_domain.facts import ChangeReason, CommitProposal, CommitResult, FactVersion
from brain_domain.principal import Membership, Principal
from brain_security.authorization import AuthorizationService, ResourceRef

from brain_temporal.ranges import TimeRange, split_remainder


class FactSlotNotFound(Exception):
    pass


class StaleVersionError(Exception):
    """`expected_current_version_id` no longer matches the slot's current
    version(s) — the optimistic half of F0001-S0005's concurrency proof."""


class FactCommitRepository(Protocol):
    async def lock_slot(self, slot_id: UUID) -> tuple[UUID, UUID] | None:
        """`SELECT ... FOR UPDATE` the slot; returns `(tenant_id, knowledge_base_id)`,
        or `None` if the slot does not exist. Serializes concurrent commits on the
        same slot (F0001-S0005 logic flow step 2)."""
        ...

    async def current_versions(self, slot_id: UUID) -> tuple[FactVersion, ...]:
        """Rows with `recorded.end IS NULL` — the currently-visible versions."""
        ...

    async def close_recorded(self, version_id: UUID, at: datetime) -> None: ...

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
    ) -> None: ...

    async def insert_change(
        self, *, reason: ChangeReason, from_version_id: UUID | None, to_version_id: UUID
    ) -> None: ...

    async def write_outbox(self, commit_id: UUID, payload: dict) -> None: ...


class CanonicalCommitService:
    """Master blueprint section 109.2, one transaction (F0001-S0005). The caller is
    responsible for the transaction boundary — every repository call here must run
    inside one `AsyncSession`/transaction so facts, `canonical_fact_change`,
    `audit_event` (written by `AuthorizationService.authorize`), and `outbox_event`
    commit or roll back together (logic flow step 5)."""

    def __init__(self, repository: FactCommitRepository, authz: AuthorizationService) -> None:
        self._repository = repository
        self._authz = authz

    async def commit(
        self,
        actor: Principal,
        memberships: Sequence[Membership],
        proposal: CommitProposal,
        *,
        trace_id: str,
    ) -> CommitResult:
        locked = await self._repository.lock_slot(proposal.slot_id)
        if locked is None:
            raise FactSlotNotFound(str(proposal.slot_id))
        tenant_id, knowledge_base_id = locked

        resource = ResourceRef(
            type="fact_slot",
            id=proposal.slot_id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
        )
        decision = await self._authz.authorize(
            actor, memberships, resource, "commit", trace_id=trace_id
        )
        if not decision.allowed:
            raise FactSlotNotFound(str(proposal.slot_id))  # denial -> 404, never disclosed

        # TimeRange.__post_init__ rejects an empty/inverted range (F0001-S0005 AC).
        new_valid = TimeRange(proposal.valid_from, proposal.valid_to)

        current = await self._repository.current_versions(proposal.slot_id)
        if proposal.expected_current_version_id is not None:
            current_ids = {v.id for v in current}
            if proposal.expected_current_version_id not in current_ids:
                raise StaleVersionError(str(proposal.expected_current_version_id))

        now = datetime.now(UTC)
        commit_id = uuid4()
        version_ids: list[UUID] = []
        superseded_version_ids: list[UUID] = []

        for existing in current:
            existing_valid = TimeRange(existing.valid_start, existing.valid_end)
            if not existing_valid.overlaps(new_valid):
                continue

            await self._repository.close_recorded(existing.id, now)
            superseded_version_ids.append(existing.id)

            for remainder in split_remainder(existing_valid, new_valid):
                remainder_id = uuid4()
                await self._repository.insert_version(
                    version_id=remainder_id,
                    slot_id=proposal.slot_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    value=dict(existing.value),
                    valid=remainder,
                    recorded=TimeRange(now, None),
                    change_reason=ChangeReason.SPLIT,
                    evidence_refs=existing.evidence_refs,
                    review_decision_id=None,
                    commit_id=commit_id,
                    source_received_at=proposal.source_received_at,
                    artifact_created_at=proposal.artifact_created_at,
                    assertion_created_at=proposal.assertion_created_at,
                    canonical_accepted_at=now,
                )
                version_ids.append(remainder_id)

        new_version_id = uuid4()
        await self._repository.insert_version(
            version_id=new_version_id,
            slot_id=proposal.slot_id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            value=dict(proposal.value),
            valid=new_valid,
            recorded=TimeRange(now, None),
            change_reason=proposal.change_reason,
            evidence_refs=proposal.evidence_refs,
            review_decision_id=proposal.review_decision_id,
            commit_id=commit_id,
            source_received_at=proposal.source_received_at,
            artifact_created_at=proposal.artifact_created_at,
            assertion_created_at=proposal.assertion_created_at,
            canonical_accepted_at=now,
        )
        version_ids.append(new_version_id)

        if superseded_version_ids:
            reason = proposal.change_reason or ChangeReason.SUPERSEDED
            for from_id in superseded_version_ids:
                await self._repository.insert_change(
                    reason=reason, from_version_id=from_id, to_version_id=new_version_id
                )
        else:
            await self._repository.insert_change(
                reason=proposal.change_reason or ChangeReason.SUPERSEDED,
                from_version_id=None,
                to_version_id=new_version_id,
            )

        await self._repository.write_outbox(
            commit_id,
            {
                "commit_id": str(commit_id),
                "slot_id": str(proposal.slot_id),
                "fact_version_ids": [str(v) for v in version_ids],
            },
        )

        return CommitResult(
            commit_id=commit_id, fact_version_ids=tuple(version_ids), canonical_accepted_at=now
        )
