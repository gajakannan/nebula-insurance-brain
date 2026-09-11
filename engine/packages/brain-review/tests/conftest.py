from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecision,
    ReviewItem,
    ReviewItemStatus,
    ReviewItemType,
)


class FakeReviewItemRepository:
    """In-memory `ReviewItemRepository` for testing the decision transaction."""

    def __init__(self) -> None:
        self.items: dict[UUID, ReviewItem] = {}
        self.decisions: dict[UUID, list[ReviewDecision]] = {}
        self.assertion_versions: dict[UUID, int] = {}
        self.corrected_assertions: dict[UUID, dict] = {}
        self.new_items_opened: list[tuple[ReviewItem, int]] = []

    def seed_item(self, item: ReviewItem, *, assertion_version: int | None = None) -> None:
        self.items[item.id] = item
        self.assertion_versions[item.assertion_id] = (
            assertion_version if assertion_version is not None else item.assertion_version
        )
        self.decisions.setdefault(item.id, [])

    async def get(self, review_item_id: UUID) -> ReviewItem | None:
        return self.items.get(review_item_id)

    async def get_decision_by_event_sha256(
        self, review_item_id: UUID, event_sha256: str
    ) -> ReviewDecision | None:
        for decision in self.decisions.get(review_item_id, []):
            if decision.event_sha256 == event_sha256:
                return decision
        return None

    async def has_any_decision(self, review_item_id: UUID) -> bool:
        return bool(self.decisions.get(review_item_id))

    async def get_latest_decision(self, review_item_id: UUID) -> ReviewDecision | None:
        rows = self.decisions.get(review_item_id, [])
        return rows[-1] if rows else None

    async def current_assertion_version(self, assertion_id: UUID) -> int:
        return self.assertion_versions[assertion_id]

    async def save_decision(self, decision: ReviewDecision) -> None:
        self.decisions.setdefault(decision.review_item_id, []).append(decision)

    async def create_corrected_assertion(
        self, *, original_assertion_id: UUID, value: dict, evidence: EvidenceLocator | None
    ) -> UUID:
        new_id = uuid4()
        self.corrected_assertions[new_id] = {
            "original_assertion_id": original_assertion_id,
            "value": value,
            "evidence": evidence,
        }
        return new_id

    async def mark_item_status(self, review_item_id: UUID, status: ReviewItemStatus) -> None:
        item = self.items[review_item_id]
        self.items[review_item_id] = ReviewItem(
            id=item.id,
            type=item.type,
            status=status,
            assertion_id=item.assertion_id,
            assertion_version=item.assertion_version,
            tenant_id=item.tenant_id,
            knowledge_base_id=item.knowledge_base_id,
            created_at=item.created_at,
            review_batch_id=item.review_batch_id,
            evidence=item.evidence,
        )

    async def open_new_review_item_for_new_version(
        self, original_item: ReviewItem, new_version: int
    ) -> None:
        self.new_items_opened.append((original_item, new_version))


class FakeAuditRecorder:
    def __init__(self) -> None:
        self.recorded: list[ReviewDecision] = []

    async def record_decision(self, decision: ReviewDecision) -> None:
        self.recorded.append(decision)


@pytest.fixture
def repository() -> FakeReviewItemRepository:
    return FakeReviewItemRepository()


@pytest.fixture
def audit() -> FakeAuditRecorder:
    return FakeAuditRecorder()


def make_review_item(
    *,
    assertion_id: UUID | None = None,
    assertion_version: int = 1,
    review_batch_id: UUID | None = None,
    evidence: EvidenceLocator | None = None,
) -> ReviewItem:
    return ReviewItem(
        id=uuid4(),
        type=ReviewItemType.LOW_CONFIDENCE_ASSERTION,
        status=ReviewItemStatus.OPEN,
        assertion_id=assertion_id or uuid4(),
        assertion_version=assertion_version,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        created_at=datetime.now(UTC),
        review_batch_id=review_batch_id or uuid4(),
        evidence=evidence,
    )
