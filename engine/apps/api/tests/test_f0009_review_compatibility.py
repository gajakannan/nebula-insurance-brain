"""F0009 S0006 AC4: existing review, fact and commit surfaces keep their shipped
routes and envelopes; the provenance reader is exported but not routed."""

from __future__ import annotations

import inspect

from brain_api import app as app_module
from brain_api.app import create_app
from brain_api.deps import get_provenance_reader
from brain_api.routes import content as content_routes
from brain_api.routes import facts as facts_routes
from brain_api.routes import reviews as reviews_routes
from brain_api.schemas.review import (
    ReviewDecisionBatchIn,
    ReviewDecisionIn,
    ReviewDecisionOut,
    ReviewDecisionReceiptOut,
    ReviewItemOut,
)

# The exact shipped HTTP surface before F0009 (OpenAPI path names).
SHIPPED = {
    ("/health", "GET"),
    ("/content/{artifactId}", "GET"),
    ("/content/{artifactId}/files/{path}", "GET"),
    ("/facts/{factSlotId}", "GET"),
    ("/facts/{factSlotId}/commits", "POST"),
    ("/reviews/{reviewItemId}", "GET"),
    ("/reviews/batches/{reviewBatchId}/decisions", "POST"),
}


def _routes() -> set[tuple[str, str]]:
    paths = create_app().openapi()["paths"]
    return {(path, method.upper()) for path, item in paths.items() for method in item}


def test_no_route_is_added_and_shipped_routes_remain() -> None:
    routes = _routes()
    assert routes == SHIPPED
    assert not any("provenance" in path or "lineage" in path for path, _ in routes)


def test_review_envelopes_are_unchanged() -> None:
    assert set(ReviewDecisionReceiptOut.model_fields) == {
        "decision_ids",
        "applied",
        "duplicate",
        "stale",
        "blocked",
    }
    assert set(ReviewDecisionIn.model_fields) == {
        "review_item_id",
        "action",
        "assertion_version",
        "reason_code",
        "corrected_value",
        "evidence",
        "reviewer_comment",
    }
    assert set(ReviewDecisionBatchIn.model_fields) == {"decisions"}
    assert set(ReviewDecisionOut.model_fields) == {
        "id",
        "review_item_id",
        "review_batch_id",
        "action",
        "reason_code",
        "corrected_value",
        "corrected_assertion_id",
        "evidence",
        "reviewer_principal_id",
        "reviewer_comment",
        "decided_at",
        "assertion_version",
        "stale",
        "event_sha256",
    }
    assert "decision" in ReviewItemOut.model_fields
    # No reservation, attempt or lineage field leaks onto the legacy envelopes.
    for model in (ReviewDecisionReceiptOut, ReviewDecisionOut, ReviewItemOut):
        assert not {"reservation", "learning_reservation_id", "attempt_ids", "lineage"} & set(
            model.model_fields
        )


def test_provenance_reader_factory_is_exported_but_unrouted() -> None:
    assert inspect.iscoroutinefunction(get_provenance_reader)
    sources = [
        inspect.getsource(module)
        for module in (reviews_routes, facts_routes, content_routes, app_module)
    ]
    assert not any("get_provenance_reader" in source for source in sources)
