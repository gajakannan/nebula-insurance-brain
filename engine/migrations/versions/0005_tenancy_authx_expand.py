"""F0002 tenancy and AuthX substrate — expand (ADR-0061/0062).

Additive only: structural registries, identity/authority/restriction/delegation/
policy-release/authentication-event tables, the commit ownership registry,
nullable ownership columns on KB-owned semantic rows, nullable membership slice
columns, v1 audit columns, and composite parent keys. No existing ID or history
row is rewritten.

Data written here is deterministic and grants nothing:
- every existing principal's own verified `(issuer, subject)` becomes its first
  `external_identity` alias (the alias table is authoritative from now on);
- every existing principal gets `principal_authority.revision =
  max(1, max(its memberships' grant_revision))`, preserving recorded revisions.

Workspace/KB registries, child ownership backfill and all restriction data come
only from the reviewed reconciliation batch (`scripts/dev/reconcile_authx.py`);
0006 validates and constrains after that batch passes its preflight.

brain-jobs (0004) text IDs are converted to uuid here. Invalid UUID text fails the
preflight with a count report before any DDL changes that table.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

TS = sa.DateTime(timezone=True)

OWNED_CHILDREN = (
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "assertion_evidence",
    "review_batch",
    "review_decision",
    "canonical_fact_change",
)

# Parents referenced by composite (id, tenant_id, knowledge_base_id) child keys in 0006.
OWNER_KEYED = (
    "source_document",
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "review_item",
    "review_batch",
    "fact_slot",
    "canonical_fact_version",
)

JOB_UUID_COLUMNS = {
    "document_job": ("id", "tenant_id", "knowledge_base_id", "artifact_id"),
    "document_artifact_lease": ("artifact_id", "tenant_id", "knowledge_base_id", "job_id"),
    "document_job_event": ("id", "job_id"),
    "document_job_outbox": ("job_id", "tenant_id", "knowledge_base_id"),
}
UUID_TEXT = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def _jobs_uuid_preflight() -> None:
    bind = op.get_bind()
    problems: list[str] = []
    for table, columns in JOB_UUID_COLUMNS.items():
        for column in columns:
            count = bind.execute(
                sa.text(
                    f"SELECT count(*) FROM {table} WHERE {column} IS NOT NULL "  # noqa: S608
                    f"AND {column} !~ :pattern"
                ),
                {"pattern": UUID_TEXT},
            ).scalar_one()
            if count:
                problems.append(f"{table}.{column}: {count} invalid UUID values")
    if problems:
        raise RuntimeError("0005 preflight failed; repair and retry: " + "; ".join(problems))


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
    )
    op.create_table(
        "workspace",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.UniqueConstraint("id", "tenant_id", name="uq_workspace_owner"),
    )
    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "tenant_id"],
            ["workspace.id", "workspace.tenant_id"],
            name="fk_kb_workspace_owner",
        ),
        sa.UniqueConstraint("id", "tenant_id", name="uq_kb_owner"),
    )
    op.create_table(
        "entity_identity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("external_namespace", sa.String(), nullable=True),
        sa.Column("external_key", sa.String(), nullable=True),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", "tenant_id", name="pk_entity_identity"),
        sa.UniqueConstraint(
            "tenant_id", "external_namespace", "external_key", name="uq_entity_external_key"
        ),
    )
    op.create_table(
        "entity_knowledge_base",
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint(
            "entity_id", "tenant_id", "knowledge_base_id", name="pk_entity_knowledge_base"
        ),
        sa.ForeignKeyConstraint(
            ["entity_id", "tenant_id"],
            ["entity_identity.id", "entity_identity.tenant_id"],
            name="fk_entity_kb_identity",
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id", "tenant_id"],
            ["knowledge_base.id", "knowledge_base.tenant_id"],
            name="fk_entity_kb_owner",
        ),
    )
    op.create_table(
        "external_identity",
        sa.Column("issuer", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), sa.ForeignKey("principal.id"), nullable=False),
        sa.Column("linked_at", TS, nullable=False),
        sa.Column("linked_by", sa.Uuid(), nullable=True),
        sa.Column("approval_ref", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("issuer", "subject", name="pk_external_identity"),
    )
    op.create_table(
        "principal_authority",
        sa.Column("principal_id", sa.Uuid(), sa.ForeignKey("principal.id"), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.CheckConstraint("revision >= 1", name="ck_principal_authority_revision"),
    )
    op.create_table(
        "resource_access",
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=False),
        sa.Column("parent_chain", postgresql.JSONB(), nullable=False),
        sa.Column("classifications", postgresql.JSONB(), nullable=False),
        sa.Column("source_acl_ids", postgresql.JSONB(), nullable=False),
        sa.Column("dependency_keys", postgresql.JSONB(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("resource_type", "resource_id", name="pk_resource_access"),
        sa.CheckConstraint("revision >= 1", name="ck_resource_access_revision"),
        sa.CheckConstraint(
            "resource_type IN ('content_artifact', 'review_task', 'fact_slot')",
            name="ck_resource_access_type",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(classifications) = 'array' AND jsonb_array_length(classifications) >= 1",
            name="ck_resource_access_classified",
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id", "tenant_id"],
            ["knowledge_base.id", "knowledge_base.tenant_id"],
            name="fk_resource_access_owner",
        ),
    )
    op.create_table(
        "delegation",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("acting_principal_id", sa.Uuid(), sa.ForeignKey("principal.id"), nullable=False),
        sa.Column(
            "executor_principal_id", sa.Uuid(), sa.ForeignKey("principal.id"), nullable=False
        ),
        sa.Column("issued_by", sa.Uuid(), sa.ForeignKey("principal.id"), nullable=False),
        sa.Column("issued_at", TS, nullable=False),
        sa.Column("not_before", TS, nullable=False),
        sa.Column("expires_at", TS, nullable=False),
        sa.Column("revoked_at", TS, nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("ceilings", postgresql.JSONB(), nullable=False),
        sa.Column("approval_ref", sa.String(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.CheckConstraint("expires_at > not_before", name="ck_delegation_window"),
        sa.CheckConstraint("revision >= 1", name="ck_delegation_revision"),
        sa.CheckConstraint(
            "acting_principal_id <> executor_principal_id", name="ck_delegation_self"
        ),
    )
    op.create_table(
        "policy_release",
        sa.Column("release_id", sa.String(), primary_key=True),
        sa.Column("release_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("model_sha256", sa.String(64), nullable=False),
        sa.Column("policy_sha256", sa.String(64), nullable=False),
        sa.Column("contract_version", sa.String(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "policy_release_pointer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "release_id", sa.String(), sa.ForeignKey("policy_release.release_id"), nullable=False
        ),
        sa.Column("activated_at", TS, nullable=False),
        sa.Column("activated_by", sa.Uuid(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_policy_release_pointer_singleton"),
    )
    op.create_table(
        "authentication_event",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("occurred_at", TS, nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("route_template", sa.String(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "canonical_commit",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=False),
        sa.Column("authorization_decision_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", TS, nullable=False),
        sa.UniqueConstraint(
            "id", "tenant_id", "knowledge_base_id", name="uq_canonical_commit_owner"
        ),
    )

    for table in OWNED_CHILDREN:
        op.add_column(table, sa.Column("tenant_id", sa.Uuid(), nullable=True))
        op.add_column(table, sa.Column("knowledge_base_id", sa.Uuid(), nullable=True))
    for table in OWNER_KEYED:
        op.create_unique_constraint(
            f"uq_{table}_owner", table, ["id", "tenant_id", "knowledge_base_id"]
        )

    op.add_column("membership", sa.Column("valid_from", TS, nullable=True))
    op.add_column("membership", sa.Column("expires_at", TS, nullable=True))
    op.add_column("membership", sa.Column("selectors", postgresql.JSONB(), nullable=True))
    op.add_column("membership", sa.Column("classifications", postgresql.JSONB(), nullable=True))
    op.add_column("membership", sa.Column("source_acl_ids", postgresql.JSONB(), nullable=True))
    op.alter_column(
        "membership",
        "revoked_at",
        type_=TS,
        postgresql_using="revoked_at AT TIME ZONE 'UTC'",
    )

    op.add_column("audit_event", sa.Column("decision_id", sa.Uuid(), nullable=True))
    op.add_column("audit_event", sa.Column("event_type", sa.String(), nullable=True))
    op.add_column("audit_event", sa.Column("operation_outcome", sa.String(), nullable=True))
    op.add_column("audit_event", sa.Column("payload", postgresql.JSONB(), nullable=True))
    op.create_index("ix_audit_event_decision_id", "audit_event", ["decision_id"])

    _jobs_uuid_preflight()
    for table, columns in JOB_UUID_COLUMNS.items():
        for column in columns:
            op.alter_column(table, column, type_=sa.Uuid(), postgresql_using=f"{column}::uuid")

    # Deterministic identity substrate for existing principals (no grants).
    op.execute(
        """
        INSERT INTO external_identity (issuer, subject, principal_id, linked_at)
        SELECT issuer, subject, id, now() FROM principal
        ON CONFLICT (issuer, subject) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO principal_authority (principal_id, revision)
        SELECT p.id, GREATEST(1, COALESCE(max(m.grant_revision), 1))
        FROM principal p LEFT JOIN membership m ON m.principal_id = p.id
        GROUP BY p.id
        ON CONFLICT (principal_id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Reverses unused expansion only. Once new records depend on the contract, use a
    forward repair or restore the pre-migration snapshot (ADR-0061 rollback)."""
    for table, columns in JOB_UUID_COLUMNS.items():
        for column in columns:
            op.alter_column(table, column, type_=sa.String(36), postgresql_using=f"{column}::text")
    op.drop_index("ix_audit_event_decision_id", table_name="audit_event")
    for column in ("payload", "operation_outcome", "event_type", "decision_id"):
        op.drop_column("audit_event", column)
    op.alter_column(
        "membership",
        "revoked_at",
        type_=sa.DateTime(),
        postgresql_using="revoked_at AT TIME ZONE 'UTC'",
    )
    for column in ("source_acl_ids", "classifications", "selectors", "expires_at", "valid_from"):
        op.drop_column("membership", column)
    for table in reversed(OWNER_KEYED):
        op.drop_constraint(f"uq_{table}_owner", table, type_="unique")
    for table in reversed(OWNED_CHILDREN):
        op.drop_column(table, "knowledge_base_id")
        op.drop_column(table, "tenant_id")
    for table in (
        "canonical_commit",
        "authentication_event",
        "policy_release_pointer",
        "policy_release",
        "delegation",
        "resource_access",
        "principal_authority",
        "external_identity",
        "entity_knowledge_base",
        "entity_identity",
        "knowledge_base",
        "workspace",
        "tenant",
    ):
        op.drop_table(table)
