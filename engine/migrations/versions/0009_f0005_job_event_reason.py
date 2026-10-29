"""F0005 expand-only failure reason on document job events.

Revision ID: 0009; revises: 0008. Adds a nullable, CHECK-constrained `reason` to the
append-only `document_job_event` history. Existing rows keep NULL; there is no
backfill and migrations 0001-0008 are unchanged. The enumeration is frozen here,
independent of application modules (the queue mirrors it).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

REASONS = (
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


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    op.add_column(
        "document_job_event", sa.Column("reason", sa.String(64), nullable=True), schema="public"
    )
    allowed = ", ".join(f"'{reason}'" for reason in REASONS)
    op.create_check_constraint(
        "ck_document_job_event_reason",
        "document_job_event",
        f"reason IS NULL OR reason IN ({allowed})",
        schema="public",
    )


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("F0005 downgrade requires an online retained-history check")
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    # Job history is append-only audit evidence. Never discard recorded reasons.
    if (
        op.get_bind()
        .execute(text("SELECT EXISTS (SELECT 1 FROM document_job_event WHERE reason IS NOT NULL)"))
        .scalar_one()
    ):
        raise RuntimeError("F0005 failure reasons exist; use forward repair")
    op.drop_constraint(
        "ck_document_job_event_reason", "document_job_event", type_="check", schema="public"
    )
    op.drop_column("document_job_event", "reason", schema="public")
