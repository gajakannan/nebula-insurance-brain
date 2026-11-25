"""F0009 provenance hooks: learning reservations and refused review submissions.

ADR-0080 (Proposed). Additive only:

- `review_decision.correction_lineage_contract` (nullable smallint, NULL or 1).
  A server-owned BEFORE INSERT trigger stamps 1 on every new decision; existing
  rows stay NULL, so historical decisions can never acquire a fabricated
  reservation (S0005 AC4).
- `learning_candidate_reservation`: one append-only, scoped future-learning
  identity per new effective non-stale CORRECT (S0005 AC1).
- `review_submission_attempt`: append-only protected attribution of a submission
  that was not applied (S0002 AC6). Unique per (item, event, outcome), so a
  repeated refusal reuses its row and a refused attempt never becomes a replay key
  (plan-review PR-H1, operator decision 2026-11-24).
- Append-only protection for `review_decision`, the decision half of the new link.
- A DEFERRABLE INITIALLY DEFERRED constraint trigger: every new non-stale CORRECT
  that created a child has exactly one matching reservation by transaction end.
- `uq_review_decision_owner` (id, tenant_id, knowledge_base_id), so the new
  composite owner keys can reference a decision. Feature G2 found the key absent
  (the design note assumed 0005/0006 provided it). `id` is the primary key, so the
  constraint holds for every existing row.

Every guard is SECURITY INVOKER with a fixed search_path and constant messages.
No existing row is rewritten or backfilled.

Upgrade: run with review writers quiesced. Downgrade: refuses, under ACCESS
EXCLUSIVE locks, if either new table has any row; it never drops data. After real
reservations or refused submissions exist, roll forward instead.

Revision ID: 0016
Revises: 0015
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

RESERVATION = "learning_candidate_reservation"
ATTEMPT = "review_submission_attempt"
DECISION = "review_decision"

_SECURE = "LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public"


def _refuse(message: str) -> str:
    return f"RAISE EXCEPTION '{message}' USING ERRCODE = 'check_violation';"


FUNCTIONS = {
    "brain_f0009_append_only": f"""
CREATE FUNCTION brain_f0009_append_only() RETURNS trigger {_SECURE} AS $$
BEGIN
    {_refuse("F0009 lineage rows are append-only")}
END
$$
""",
    "brain_f0009_decision_marker": f"""
CREATE FUNCTION brain_f0009_decision_marker() RETURNS trigger {_SECURE} AS $$
BEGIN
    -- Server-owned: a submitted value is always overridden.
    NEW.correction_lineage_contract := 1;
    RETURN NEW;
END
$$
""",
    "brain_f0009_reservation_guard": f"""
CREATE FUNCTION brain_f0009_reservation_guard() RETURNS trigger {_SECURE} AS $$
DECLARE
    d public.review_decision%ROWTYPE;
    i public.review_item%ROWTYPE;
    c public.assertion%ROWTYPE;
    o public.assertion%ROWTYPE;
BEGIN
    SELECT * INTO d FROM public.review_decision WHERE id = NEW.review_decision_id;
    IF NOT FOUND
       OR d.tenant_id <> NEW.tenant_id OR d.knowledge_base_id <> NEW.knowledge_base_id
       OR d.correction_lineage_contract IS DISTINCT FROM 1
       OR d.stale OR d.action <> 'CORRECT'
       OR d.corrected_assertion_id IS DISTINCT FROM NEW.corrected_assertion_id
       OR d.reviewer_principal_id <> NEW.reviewer_principal_id
       -- PR-M1: decided_at is the naive-UTC F0001 column; compare as UTC instants.
       OR (d.decided_at AT TIME ZONE 'UTC') <> NEW.reserved_at THEN
        {_refuse("reservation does not match an effective new correction")}
    END IF;
    SELECT * INTO i FROM public.review_item WHERE id = d.review_item_id;
    IF NOT FOUND
       OR i.tenant_id <> NEW.tenant_id OR i.knowledge_base_id <> NEW.knowledge_base_id
       OR i.assertion_id <> NEW.original_assertion_id
       OR i.review_batch_id IS DISTINCT FROM d.review_batch_id THEN
        {_refuse("reservation does not match its review item")}
    END IF;
    SELECT * INTO c FROM public.assertion WHERE id = NEW.corrected_assertion_id;
    SELECT * INTO o FROM public.assertion WHERE id = NEW.original_assertion_id;
    IF c.id IS NULL OR o.id IS NULL
       OR c.origin <> 'HUMAN_REVIEW'
       OR c.original_assertion_id IS DISTINCT FROM NEW.original_assertion_id
       OR c.semantic_contract_version <> o.semantic_contract_version THEN
        {_refuse("reservation does not match its corrected assertion")}
    END IF;
    RETURN NEW;
END
$$
""",
    "brain_f0009_attempt_guard": f"""
CREATE FUNCTION brain_f0009_attempt_guard() RETURNS trigger {_SECURE} AS $$
DECLARE
    i public.review_item%ROWTYPE;
BEGIN
    SELECT * INTO i FROM public.review_item WHERE id = NEW.review_item_id;
    IF NOT FOUND
       OR i.tenant_id <> NEW.tenant_id OR i.knowledge_base_id <> NEW.knowledge_base_id
       OR i.assertion_id <> NEW.original_assertion_id
       OR i.review_batch_id IS DISTINCT FROM NEW.review_batch_id THEN
        {_refuse("attempt does not match its review item")}
    END IF;
    -- The verified reviewer's allowed review_task:annotate decision for this item,
    -- staged in the same transaction by the authorization facade.
    IF NOT EXISTS (
        SELECT 1 FROM public.audit_event a
         WHERE a.decision_id = NEW.authorization_decision_id
           AND a.event_type = 'authorization_decision'
           AND a.decision
           AND a.actor_principal_id = NEW.reviewer_principal_id
           AND a.resource_type = 'review_task'
           AND a.resource_id = NEW.review_item_id
           AND a.action = 'annotate') THEN
        {_refuse("attempt has no matching annotate authorization")}
    END IF;
    RETURN NEW;
END
$$
""",
    "brain_f0009_correction_reserved": f"""
CREATE FUNCTION brain_f0009_correction_reserved() RETURNS trigger {_SECURE} AS $$
BEGIN
    IF NEW.correction_lineage_contract = 1 AND NOT NEW.stale
       AND NEW.action = 'CORRECT' AND NEW.corrected_assertion_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM public.learning_candidate_reservation r
            WHERE r.review_decision_id = NEW.id
              AND r.corrected_assertion_id = NEW.corrected_assertion_id) THEN
        {_refuse("an effective correction requires its learning reservation")}
    END IF;
    RETURN NULL;
END
$$
""",
}

TABLES_DDL = f"""
CREATE TABLE {RESERVATION} (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    review_decision_id uuid NOT NULL,
    original_assertion_id uuid NOT NULL,
    corrected_assertion_id uuid NOT NULL,
    reviewer_principal_id uuid NOT NULL REFERENCES principal(id),
    reserved_at timestamptz NOT NULL,
    CONSTRAINT uq_f0009_reservation_decision UNIQUE (review_decision_id),
    CONSTRAINT uq_f0009_reservation_child UNIQUE (corrected_assertion_id),
    CONSTRAINT uq_f0009_reservation_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0009_reservation_decision
        FOREIGN KEY (review_decision_id, tenant_id, knowledge_base_id)
        REFERENCES review_decision(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT fk_f0009_reservation_original
        FOREIGN KEY (original_assertion_id, tenant_id, knowledge_base_id)
        REFERENCES assertion(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT fk_f0009_reservation_child
        FOREIGN KEY (corrected_assertion_id, tenant_id, knowledge_base_id)
        REFERENCES assertion(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE
);
CREATE TABLE {ATTEMPT} (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    review_item_id uuid NOT NULL,
    review_batch_id uuid NOT NULL,
    original_assertion_id uuid NOT NULL,
    reviewer_principal_id uuid NOT NULL REFERENCES principal(id),
    submitted_at timestamptz NOT NULL,
    event_sha256 text NOT NULL CHECK (event_sha256 ~ '^[a-f0-9]{{64}}$'),
    assertion_version integer NOT NULL CHECK (assertion_version > 0),
    action text NOT NULL CHECK (action IN ('ACCEPT','CORRECT','REJECT','BLOCKED')),
    reason_code text NULL CHECK (reason_code IS NULL OR reason_code IN
        ('MISREAD_VALUE','WRONG_REGION','NOT_IN_SOURCE','OUT_OF_SCOPE','EVIDENCE_UNRESOLVED')),
    corrected_value jsonb NULL,
    evidence jsonb NULL,
    reviewer_comment text NULL,
    outcome text NOT NULL CHECK (outcome IN ('ALREADY_DECIDED','BATCH_REFUSED')),
    authorization_decision_id uuid NOT NULL,
    CONSTRAINT uq_f0009_attempt_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT uq_f0009_attempt_event_outcome UNIQUE (review_item_id, event_sha256, outcome),
    CONSTRAINT fk_f0009_attempt_item
        FOREIGN KEY (review_item_id, tenant_id, knowledge_base_id)
        REFERENCES review_item(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT fk_f0009_attempt_batch
        FOREIGN KEY (review_batch_id, tenant_id, knowledge_base_id)
        REFERENCES review_batch(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT fk_f0009_attempt_original
        FOREIGN KEY (original_assertion_id, tenant_id, knowledge_base_id)
        REFERENCES assertion(id, tenant_id, knowledge_base_id)
        DEFERRABLE INITIALLY IMMEDIATE
);
"""

INDEXES = (
    ("ix_f0009_reservation_original", f"{RESERVATION} (original_assertion_id)"),
    ("ix_f0009_attempt_assertion", f"{ATTEMPT} (original_assertion_id)"),
    (
        "ix_f0009_assertion_parent",
        "assertion (original_assertion_id) WHERE original_assertion_id IS NOT NULL",
    ),
    (
        "ix_f0009_decision_corrected",
        f"{DECISION} (corrected_assertion_id) WHERE corrected_assertion_id IS NOT NULL",
    ),
    ("ix_f0009_evidence_assertion", "assertion_evidence (assertion_id)"),
    ("ix_f0009_change_to", "canonical_fact_change (to_version_id)"),
    (
        "ix_f0009_change_from",
        "canonical_fact_change (from_version_id) WHERE from_version_id IS NOT NULL",
    ),
)

# (trigger, table, timing/definition). BEFORE triggers fire in name order.
TRIGGERS = (
    (
        "trg_f0009_reservation_append_only",
        RESERVATION,
        "BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_reservation_no_truncate",
        RESERVATION,
        "BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_reservation_guard",
        RESERVATION,
        "BEFORE INSERT ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_reservation_guard()",
    ),
    (
        "trg_f0009_attempt_append_only",
        ATTEMPT,
        "BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_attempt_no_truncate",
        ATTEMPT,
        "BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_attempt_guard",
        ATTEMPT,
        "BEFORE INSERT ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_attempt_guard()",
    ),
    (
        "trg_f0009_decision_append_only",
        DECISION,
        "BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_decision_no_truncate",
        DECISION,
        "BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION brain_f0009_append_only()",
    ),
    (
        "trg_f0009_decision_marker",
        DECISION,
        "BEFORE INSERT ON {t} FOR EACH ROW EXECUTE FUNCTION brain_f0009_decision_marker()",
    ),
)
CONSTRAINT_TRIGGER = "trg_f0009_correction_reserved"
DECISION_OWNER = "uq_review_decision_owner"
MARKER_CHECK = "ck_review_decision_correction_lineage_contract"


def upgrade() -> None:
    bind = op.get_bind()
    # WHY: parent-to-child order, held through the install, so no review writer
    # inserts between the preflight and the new guards.
    bind.execute(text(f"LOCK TABLE review_item, {DECISION} IN SHARE ROW EXCLUSIVE MODE"))
    op.execute(f"ALTER TABLE {DECISION} ADD COLUMN correction_lineage_contract smallint NULL")
    op.execute(
        f"ALTER TABLE {DECISION} ADD CONSTRAINT {MARKER_CHECK} CHECK "
        "(correction_lineage_contract IS NULL OR correction_lineage_contract = 1)"
    )
    op.execute(
        f"ALTER TABLE {DECISION} ADD CONSTRAINT {DECISION_OWNER} "
        "UNIQUE (id, tenant_id, knowledge_base_id)"
    )
    op.execute(TABLES_DDL)
    for definition in FUNCTIONS.values():
        op.execute(definition)
    for name, columns in INDEXES:
        op.execute(f"CREATE INDEX {name} ON {columns}")
    for name, table, definition in TRIGGERS:
        op.execute(f"CREATE TRIGGER {name} " + definition.format(t=table))
    op.execute(
        f"CREATE CONSTRAINT TRIGGER {CONSTRAINT_TRIGGER} AFTER INSERT ON {DECISION} "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION brain_f0009_correction_reserved()"
    )
    legacy = bind.execute(
        text(f"SELECT count(*) FROM {DECISION} WHERE correction_lineage_contract IS NOT NULL")
    ).scalar_one()
    if legacy:
        raise RuntimeError("0016 upgrade invariant failed: historical decisions were stamped")
    log.info("0016 F0009 provenance hooks installed; existing decisions keep a NULL marker")


def downgrade() -> None:
    bind = op.get_bind()
    # WHY: ACCESS EXCLUSIVE in a fixed lexical order makes the emptiness check and
    # the drops one race-free step; no writer can insert between them.
    for table in sorted((RESERVATION, DECISION, ATTEMPT)):
        bind.execute(text(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE"))
    counts = {
        table: bind.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in (RESERVATION, ATTEMPT)
    }
    if any(counts.values()):
        raise RuntimeError(
            "0016 downgrade refused: F0009 lineage rows exist "
            f"({RESERVATION}={counts[RESERVATION]}, {ATTEMPT}={counts[ATTEMPT]}). "
            "No rows modified; roll forward or redeploy a compatible reader instead."
        )
    op.execute(f"DROP TRIGGER {CONSTRAINT_TRIGGER} ON {DECISION}")
    for name, table, _definition in reversed(TRIGGERS):
        op.execute(f"DROP TRIGGER {name} ON {table}")
    op.execute(f"DROP TABLE {ATTEMPT}")
    op.execute(f"DROP TABLE {RESERVATION}")
    for name, _columns in reversed(INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
    for name in reversed(FUNCTIONS):
        op.execute(f"DROP FUNCTION {name}()")
    op.execute(f"ALTER TABLE {DECISION} DROP CONSTRAINT {DECISION_OWNER}")
    op.execute(f"ALTER TABLE {DECISION} DROP CONSTRAINT {MARKER_CHECK}")
    op.execute(f"ALTER TABLE {DECISION} DROP COLUMN correction_lineage_contract")
    log.info("0016 downgraded; no lineage rows existed and no existing row was rewritten")
