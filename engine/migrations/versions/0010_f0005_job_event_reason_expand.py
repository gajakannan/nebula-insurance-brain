"""F0005 expand-only: four more job failure reasons (Code Review H1/M1, 2026-10-27).

Revision ID: 0010; revises: 0009. Widens `ck_document_job_event_reason` with:
- `model_budget_exceeded`: a context, call or token budget rejected a model call
  before dispatch, or the serving usage exceeded its reservation;
- `model_deadline_exceeded`: the run deadline expired before or during a call;
- `model_contract_fallback`: Graph dense fell back to a direct call, whose answer
  would otherwise carry dense identity;
- `interpretation_failed`: an unexpected error after the bundle was published,
  which is not a conversion failure and never spends the reconversion budget.

Existing rows and the 0009 values are unchanged. The enumeration is frozen here,
independent of application modules (the queue mirrors it).
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

PREVIOUS = (
    "model_unavailable",
    "model_timeout",
    "model_http_error",
    "model_malformed_output",
    "model_schema_invalid",
    "storage_write_failed",
    "conversion_failed",
    "conversion_timeout",
    "stage_guard_mismatch",
    "unsupported_targeting",
    "unsupported_output",
    "authorization_denied",
    "cancelled",
)
ADDED = (
    "model_budget_exceeded",
    "model_deadline_exceeded",
    "model_contract_fallback",
    "interpretation_failed",
)
REASONS = PREVIOUS + ADDED


def _constrain(reasons: Sequence[str]) -> None:
    op.drop_constraint(
        "ck_document_job_event_reason", "document_job_event", type_="check", schema="public"
    )
    allowed = ", ".join(f"'{reason}'" for reason in reasons)
    op.create_check_constraint(
        "ck_document_job_event_reason",
        "document_job_event",
        f"reason IS NULL OR reason IN ({allowed})",
        schema="public",
    )


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    _constrain(REASONS)


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("F0005 downgrade requires an online retained-history check")
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    # Job history is append-only audit evidence. Never discard recorded reasons.
    allowed = ", ".join(f"'{reason}'" for reason in ADDED)
    recorded = text(f"SELECT EXISTS (SELECT 1 FROM document_job_event WHERE reason IN ({allowed}))")
    if op.get_bind().execute(recorded).scalar_one():
        raise RuntimeError("F0005 expanded failure reasons exist; use forward repair")
    _constrain(PREVIOUS)
