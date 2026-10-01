"""F0002 tenancy and AuthX — validate and constrain (ADR-0061).

Runs only after the reviewed reconciliation batch (`scripts/dev/reconcile_authx.py
--apply`). The preflight counts every row that would violate an ownership
constraint and aborts with a counts-only report (no IDs, no content) before any
DDL, so a failed attempt leaves the schema exactly as 0005 left it. No automatic
deletion, reassignment or grant happens here.

Then: NOT NULL ownership and membership-slice columns, composite
`(parent_id, tenant_id, knowledge_base_id)` foreign keys along every KB-owned
chain, registry foreign keys for every KB reference, the entity-identity foreign
key for fact slots, the commit-ownership foreign key for the outbox, and job-table
ownership keys. Constraints are added NOT VALID and then VALIDATEd.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

OWNED = (
    "source_document",
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "assertion_evidence",
    "review_item",
    "review_batch",
    "review_decision",
    "fact_slot",
    "canonical_fact_version",
    "canonical_fact_change",
    "canonical_commit",
)
NEWLY_OWNED = (
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "assertion_evidence",
    "review_batch",
    "review_decision",
    "canonical_fact_change",
)
KB_REGISTRY_REFS = (
    "source_document",
    "review_batch",
    "review_item",
    "fact_slot",
    "canonical_commit",
    "membership",
    "document_job",
    "document_artifact_lease",
)
# (child table, child FK column, parent table)
CHAINS = (
    ("document_version", "source_document_id", "source_document"),
    ("content_artifact", "document_version_id", "document_version"),
    ("semantic_interpretation_run", "artifact_id", "content_artifact"),
    ("assertion", "run_id", "semantic_interpretation_run"),
    ("assertion", "original_assertion_id", "assertion"),
    ("assertion_evidence", "assertion_id", "assertion"),
    ("assertion_evidence", "artifact_id", "content_artifact"),
    ("review_item", "assertion_id", "assertion"),
    ("review_item", "review_batch_id", "review_batch"),
    ("review_decision", "review_item_id", "review_item"),
    ("review_decision", "review_batch_id", "review_batch"),
    ("review_decision", "corrected_assertion_id", "assertion"),
    ("canonical_fact_version", "slot_id", "fact_slot"),
    ("canonical_fact_version", "commit_id", "canonical_commit"),
    ("canonical_fact_change", "to_version_id", "canonical_fact_version"),
    ("canonical_fact_change", "from_version_id", "canonical_fact_version"),
)
MEMBERSHIP_SLICE = ("valid_from", "selectors", "classifications", "source_acl_ids")


def _count(sql: str) -> int:
    return int(op.get_bind().execute(sa.text(sql)).scalar_one())


def _preflight() -> None:
    problems: list[str] = []

    def check(label: str, sql: str) -> None:
        count = _count(sql)
        if count:
            problems.append(f"{label}: {count}")

    for table in OWNED:
        check(
            f"{table} rows without ownership",
            f"SELECT count(*) FROM {table} WHERE tenant_id IS NULL OR knowledge_base_id IS NULL",
        )
    for table in KB_REGISTRY_REFS:
        check(
            f"{table} rows whose KB is not registered to that tenant",
            f"""SELECT count(*) FROM {table} c WHERE NOT EXISTS (
                SELECT 1 FROM knowledge_base k
                WHERE k.id = c.knowledge_base_id AND k.tenant_id = c.tenant_id)""",
        )
    for child, column, parent in CHAINS:
        check(
            f"{child}.{column} ownership disagreeing with {parent}",
            f"""SELECT count(*) FROM {child} c JOIN {parent} p ON p.id = c.{column}
                WHERE (p.tenant_id, p.knowledge_base_id)
                      IS DISTINCT FROM (c.tenant_id, c.knowledge_base_id)""",
        )
    check(
        "review batches spanning more than one KB",
        """SELECT count(*) FROM (SELECT review_batch_id FROM review_item
           WHERE review_batch_id IS NOT NULL GROUP BY review_batch_id
           HAVING count(DISTINCT (tenant_id, knowledge_base_id)) > 1) mixed""",
    )
    check(
        "fact slots without a tenant entity identity",
        """SELECT count(*) FROM fact_slot f WHERE NOT EXISTS (
           SELECT 1 FROM entity_identity e WHERE e.id = f.entity_id AND e.tenant_id = f.tenant_id)""",
    )
    check(
        "outbox rows without a commit ownership record",
        """SELECT count(*) FROM outbox_event o WHERE NOT EXISTS (
           SELECT 1 FROM canonical_commit c WHERE c.id = o.commit_id)""",
    )
    check(
        "memberships without a complete grant slice",
        "SELECT count(*) FROM membership WHERE "
        + " OR ".join(f"{c} IS NULL" for c in MEMBERSHIP_SLICE),
    )
    check(
        "principals without an authority revision",
        """SELECT count(*) FROM principal p WHERE NOT EXISTS (
           SELECT 1 FROM principal_authority a WHERE a.principal_id = p.id)""",
    )
    check(
        "job outbox rows disagreeing with their job's ownership",
        """SELECT count(*) FROM document_job_outbox o LEFT JOIN document_job j ON j.id = o.job_id
           WHERE j.id IS NULL OR (j.tenant_id, j.knowledge_base_id)
                 IS DISTINCT FROM (o.tenant_id, o.knowledge_base_id)""",
    )
    check(
        "job events without a job",
        """SELECT count(*) FROM document_job_event e WHERE NOT EXISTS (
           SELECT 1 FROM document_job j WHERE j.id = e.job_id)""",
    )
    if problems:
        raise RuntimeError(
            "0006 preflight failed; run scripts/dev/reconcile_authx.py --dry-run, repair the "
            "reviewed mapping and apply it, then retry: " + "; ".join(problems)
        )


def _fk(name: str, table: str, columns: list[str], referent: str, remote: list[str]) -> None:
    op.create_foreign_key(name, table, referent, columns, remote, postgresql_not_valid=True)
    op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")


def upgrade() -> None:
    _preflight()

    for table in NEWLY_OWNED:
        op.alter_column(table, "tenant_id", nullable=False)
        op.alter_column(table, "knowledge_base_id", nullable=False)
    for column in MEMBERSHIP_SLICE:
        op.alter_column("membership", column, nullable=False)

    for table in KB_REGISTRY_REFS:
        _fk(
            f"fk_{table}_kb_owner",
            table,
            ["knowledge_base_id", "tenant_id"],
            "knowledge_base",
            ["id", "tenant_id"],
        )
    for child, column, parent in CHAINS:
        _fk(
            f"fk_{child}_{column}_owner",
            child,
            [column, "tenant_id", "knowledge_base_id"],
            parent,
            ["id", "tenant_id", "knowledge_base_id"],
        )
    _fk(
        "fk_fact_slot_entity_owner",
        "fact_slot",
        ["entity_id", "tenant_id"],
        "entity_identity",
        ["id", "tenant_id"],
    )
    _fk("fk_outbox_event_commit", "outbox_event", ["commit_id"], "canonical_commit", ["id"])
    op.create_unique_constraint(
        "uq_document_job_owner", "document_job", ["id", "tenant_id", "knowledge_base_id"]
    )
    _fk(
        "fk_document_job_outbox_job_owner",
        "document_job_outbox",
        ["job_id", "tenant_id", "knowledge_base_id"],
        "document_job",
        ["id", "tenant_id", "knowledge_base_id"],
    )
    _fk("fk_document_job_event_job", "document_job_event", ["job_id"], "document_job", ["id"])


def downgrade() -> None:
    """Drops constraints only; ownership data stays (forward-repair friendly)."""
    op.drop_constraint("fk_document_job_event_job", "document_job_event", type_="foreignkey")
    op.drop_constraint(
        "fk_document_job_outbox_job_owner", "document_job_outbox", type_="foreignkey"
    )
    op.drop_constraint("uq_document_job_owner", "document_job", type_="unique")
    op.drop_constraint("fk_outbox_event_commit", "outbox_event", type_="foreignkey")
    op.drop_constraint("fk_fact_slot_entity_owner", "fact_slot", type_="foreignkey")
    for child, column, _parent in reversed(CHAINS):
        op.drop_constraint(f"fk_{child}_{column}_owner", child, type_="foreignkey")
    for table in reversed(KB_REGISTRY_REFS):
        op.drop_constraint(f"fk_{table}_kb_owner", table, type_="foreignkey")
    for column in MEMBERSHIP_SLICE:
        op.alter_column("membership", column, nullable=True)
    for table in NEWLY_OWNED:
        op.alter_column(table, "knowledge_base_id", nullable=True)
        op.alter_column(table, "tenant_id", nullable=True)
