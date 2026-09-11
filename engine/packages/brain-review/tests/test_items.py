from __future__ import annotations

from uuid import uuid4

from brain_domain.review import EvidenceLocator, ReviewItemStatus, ReviewItemType
from brain_review.items import LOW_CONFIDENCE_THRESHOLD, route_low_confidence_assertion


def test_low_confidence_assertion_is_routed_to_review() -> None:
    item = route_low_confidence_assertion(
        assertion_id=uuid4(),
        assertion_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        model_confidence=0.41,
        evidence=EvidenceLocator(source="artifact-1", precision="exact-span"),
    )

    assert item is not None
    assert item.type == ReviewItemType.LOW_CONFIDENCE_ASSERTION
    assert item.status == ReviewItemStatus.OPEN


def test_high_confidence_assertion_is_not_routed() -> None:
    item = route_low_confidence_assertion(
        assertion_id=uuid4(),
        assertion_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        model_confidence=0.99,
        evidence=EvidenceLocator(source="artifact-1", precision="exact-span"),
    )

    assert item is None


def test_threshold_boundary_is_not_routed() -> None:
    item = route_low_confidence_assertion(
        assertion_id=uuid4(),
        assertion_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        model_confidence=LOW_CONFIDENCE_THRESHOLD,
        evidence=EvidenceLocator(source="artifact-1", precision="exact-span"),
    )

    assert item is None
