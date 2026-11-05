"""Trusted source ports, called only inside an authorized application operation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from brain_domain.assertions import ProducerContext, SourceAccessProof, TimeReference, VerifiedBlock


class NameClaimConflict(ValueError):
    code = "NAME_CLAIMED_BY_ANOTHER"


class AdmissionSources(Protocol):
    async def block(self, context: ProducerContext, block_id: str) -> VerifiedBlock: ...

    async def time_reference(self, context: ProducerContext, ref: UUID) -> TimeReference: ...


class AssertionEligibilityGuard(Protocol):
    async def require_commit_sources(
        self,
        *,
        evidence_refs: Sequence[UUID],
        review_decision_id: UUID | None,
        authorized_scope: tuple[UUID, UUID],
        closes_existing: bool,
        source_access: SourceAccessProof | None,
    ) -> None: ...
