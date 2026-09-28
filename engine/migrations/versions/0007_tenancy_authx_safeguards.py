"""F0002 database safeguards (BLUEPRINT §4.11; operator scope amendment at G4, 2026-09-28).

Utopia's same-KB provenance record (0048) carried three safeguards that §4.11
deferred to the F0002 implementation run. The user brought them into this run at
the G4 approval gate:

1. **Ownership is immutable.** Once set, `tenant_id`/`knowledge_base_id` (and the
   structural parents of workspaces, knowledge bases, memberships and verified
   identity aliases) cannot be rewritten; a row moves between owners only by an
   explicit new record, never an UPDATE. A NULL owner may still be filled once,
   so an expand-then-reconcile backfill remains possible.
2. **Audit is append-only.** `audit_event` and `authentication_event` reject row
   UPDATE and DELETE. (TRUNCATE is a DBA operation outside this guard.)
3. **Deferrable self-references for restore.** The `assertion` correction chain
   references itself; its foreign keys become DEFERRABLE INITIALLY IMMEDIATE so a
   restore can load rows in any order inside one transaction
   (`SET CONSTRAINTS ALL DEFERRED`) while normal writes keep immediate checking.

Link tables without owner columns (`outbox_event`, `document_job_event`) have a
single parent whose foreign key fixes their ownership; every multi-parent link
table carries owner columns with composite keys since 0006.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
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
    "resource_access",
    "document_job",
    "document_artifact_lease",
    "document_job_outbox",
    "entity_knowledge_base",
)
# Structural records with owner columns other than (tenant_id, knowledge_base_id).
STRUCTURAL = {
    "workspace": ("tenant_id",),
    "knowledge_base": ("tenant_id", "workspace_id"),
    "entity_identity": ("tenant_id",),
    "membership": ("tenant_id", "knowledge_base_id", "principal_id"),
    "external_identity": ("principal_id",),
    "delegation": ("acting_principal_id", "executor_principal_id", "issued_by"),
}
APPEND_ONLY = ("audit_event", "authentication_event")
SELF_REFERENCES = (
    ("assertion", "fk_assertion_original_assertion_id"),
    ("assertion", "fk_assertion_original_assertion_id_owner"),
)


def _owner_columns() -> dict[str, tuple[str, ...]]:
    return {**{t: ("tenant_id", "knowledge_base_id") for t in OWNED}, **STRUCTURAL}


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION brain_forbid_owner_change() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
            col text;
            old_value text;
            new_value text;
        BEGIN
            FOREACH col IN ARRAY TG_ARGV LOOP
                EXECUTE format('SELECT ($1).%I::text, ($2).%I::text', col, col)
                    INTO old_value, new_value USING OLD, NEW;
                IF old_value IS NOT NULL AND old_value IS DISTINCT FROM new_value THEN
                    RAISE EXCEPTION 'ownership column %.% is immutable', TG_TABLE_NAME, col
                        USING ERRCODE = 'check_violation';
                END IF;
            END LOOP;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION brain_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only (% rejected)', TG_TABLE_NAME, TG_OP
                USING ERRCODE = 'check_violation';
        END
        $$
        """
    )
    for table, columns in _owner_columns().items():
        arguments = ", ".join(f"'{c}'" for c in columns)
        op.execute(
            f"CREATE TRIGGER trg_{table}_owner_immutable BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION brain_forbid_owner_change({arguments})"
        )
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER trg_{table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION brain_append_only()"
        )
    for table, constraint in SELF_REFERENCES:
        op.execute(
            f"ALTER TABLE {table} ALTER CONSTRAINT {constraint} DEFERRABLE INITIALLY IMMEDIATE"
        )


def downgrade() -> None:
    for table, constraint in SELF_REFERENCES:
        op.execute(f"ALTER TABLE {table} ALTER CONSTRAINT {constraint} NOT DEFERRABLE")
    for table in APPEND_ONLY:
        op.execute(f"DROP TRIGGER trg_{table}_append_only ON {table}")
    for table in _owner_columns():
        op.execute(f"DROP TRIGGER trg_{table}_owner_immutable ON {table}")
    op.execute("DROP FUNCTION brain_append_only()")
    op.execute("DROP FUNCTION brain_forbid_owner_change()")
