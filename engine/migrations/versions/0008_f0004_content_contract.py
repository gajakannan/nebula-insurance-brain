"""F0004 additive content contracts, indexes and append-only date history.

Revision ID: 0008; revises: 0007. Existing ownership guards and identifiers survive.
The existing single-artifact unique constraint remains until authorized legacy
reconciliation. SQL is frozen beside this revision, independent of planning files.
"""

from collections.abc import Sequence
from pathlib import Path

from alembic import op
from sqlalchemy import inspect, select, text
from sqlalchemy import table as sql_table

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

TABLES = (
    "content_table_cell_block",
    "content_table_cell",
    "content_table",
    "content_block",
    "document_date_selection",
    "document_date_candidate",
    "content_artifact_state_event",
    "content_repair_record",
)


def upgrade() -> None:
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    sql = Path(__file__).with_suffix(".sql").read_text()
    if op.get_context().as_sql:
        op.execute(sql)
    else:
        op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("F0004 downgrade requires an online retained-history check")
    bind = op.get_bind()
    op.execute("SET LOCAL search_path TO public, pg_catalog")
    # All history is retained, including v1 repair/state history. Never silently
    # discard rows merely because no v2 bundle has been activated yet.
    for table_name in TABLES:
        history = sql_table(table_name, schema="public")
        if bind.execute(select(select(1).select_from(history).exists())).scalar_one():
            raise RuntimeError("F0004 history exists; use forward repair")
    if bind.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM content_artifact WHERE artifact_contract_version=2 "
            "OR writer_fallback_reason IS NOT NULL)"
        )
    ).scalar_one():
        raise RuntimeError("F0004 v2/fallback data exists; use forward repair")
    if bind.execute(
        text(
            "SELECT EXISTS (SELECT document_version_id FROM content_artifact "
            "GROUP BY document_version_id HAVING count(*)>1)"
        )
    ).scalar_one():
        raise RuntimeError("F0004 artifact cardinality cannot be downgraded")
    unique = inspect(bind).get_unique_constraints("content_artifact", schema="public")
    if not any(c["column_names"] == ["document_version_id"] for c in unique):
        op.create_unique_constraint(
            "uq_content_artifact_legacy_version",
            "content_artifact",
            ["document_version_id"],
            schema="public",
        )
    op.execute("DROP TRIGGER content_artifact_guard ON content_artifact")
    for table in TABLES:
        op.drop_table(table, schema="public")
    op.execute("DROP FUNCTION f0004_guard_content_artifact()")
    op.execute("DROP FUNCTION f0004_stamp_state_event()")
    op.execute("DROP FUNCTION f0004_reject_history_mutation()")
    for name in (
        "fk_f0004_artifact_predecessor",
        "ck_f0004_artifact_not_self",
        "ck_content_v2_metadata",
        "ck_content_writer_fallback",
        "ck_content_publication_state",
        "ck_content_contract_version",
        "uq_f0004_artifact_version_owner",
    ):
        op.execute(f"ALTER TABLE content_artifact DROP CONSTRAINT {name}")
    op.drop_index("uq_f0004_v2_recipe", table_name="content_artifact", schema="public")
    for column in (
        "artifact_contract_version",
        "recipe_sha256",
        "manifest_sha256",
        "supersedes_artifact_id",
        "publication_state",
        "writer_fallback_reason",
    ):
        op.drop_column("content_artifact", column, schema="public")
