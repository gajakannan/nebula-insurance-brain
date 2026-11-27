"""F0012 ontology releases: immutable release records and append-only selection.

ADR-0081 D4 (Proposed); DDL from the approved design
`planning-mds/features/F0012-foundation-ontology/migration-design.sql`. Additive only:

- eight tenant/KB-owned tables (ADR-0030): module versions, releases, release
  membership, terms, change records, impact reports, reviews and selections;
- UPDATE, DELETE and TRUNCATE are refused on every table;
- `brain_f0012_selection_guard` re-checks every selection the service already
  checked: consecutive sequence, an approved review of a complete report whose
  candidate is the selected release and whose predecessor is the current head;
  a rollback names a release that was activated before.

One existing constraint changes: `resource_access.ck_resource_access_type` also
admits `ontology_release`, the KB ontology scope that authorization hydrates
(G0-5, operator decision 2026-11-26: a trusted resource_access row is required).
Existing rows are revalidated, never rewritten. `canonical_fact_version` keeps its
0014 temporal-kind CHECKs (ADR-0078 D10), which F0012 activates without DDL.

Downgrade: refuses, under ACCESS EXCLUSIVE locks, while any ontology row or
`ontology_release` resource_access row exists.

Revision ID: 0017
Revises: 0016
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

_SECURE = "LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public"

# Creation order; drops run in reverse.
TABLES = (
    "ontology_module_version",
    "ontology_release",
    "ontology_release_module",
    "ontology_term",
    "ontology_change_record",
    "ontology_impact_report",
    "ontology_release_review",
    "ontology_release_selection",
)

TABLES_DDL = r"""
CREATE TABLE ontology_module_version (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    module_id text NOT NULL CHECK (module_id ~ '^[a-z][a-z0-9-]{0,47}$'),
    version integer NOT NULL CHECK (version >= 1),
    content_digest char(64) NOT NULL CHECK (content_digest ~ '^[0-9a-f]{64}$'),
    authoring_schema text NOT NULL CHECK (authoring_schema = 'ontology-module-authoring/v1'),
    normalized jsonb NOT NULL,
    created_by uuid NOT NULL REFERENCES principal(id),
    created_at timestamptz NOT NULL,
    CONSTRAINT uq_f0012_module_version UNIQUE (tenant_id, knowledge_base_id, module_id, version),
    CONSTRAINT uq_f0012_module_version_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_module_version_kb FOREIGN KEY (knowledge_base_id, tenant_id)
        REFERENCES knowledge_base(id, tenant_id)
);

CREATE TABLE ontology_release (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    release_ref text NOT NULL CHECK (release_ref ~ '^ontrel:sha256-[0-9a-f]{64}$'),
    name text NOT NULL,
    sequence integer NOT NULL CHECK (sequence >= 1),
    manifest_digest char(64) NOT NULL CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
    manifest jsonb NOT NULL,
    installed_by uuid NOT NULL REFERENCES principal(id),
    installed_at timestamptz NOT NULL,
    CONSTRAINT ck_f0012_release_ref_digest CHECK (release_ref = 'ontrel:sha256-' || manifest_digest),
    CONSTRAINT uq_f0012_release_ref UNIQUE (tenant_id, knowledge_base_id, release_ref),
    CONSTRAINT uq_f0012_release_name_seq UNIQUE (tenant_id, knowledge_base_id, name, sequence),
    CONSTRAINT uq_f0012_release_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_release_kb FOREIGN KEY (knowledge_base_id, tenant_id)
        REFERENCES knowledge_base(id, tenant_id)
);

CREATE TABLE ontology_release_module (
    release_id uuid NOT NULL,
    module_version_id uuid NOT NULL,
    module_id text NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    PRIMARY KEY (release_id, module_id),
    CONSTRAINT fk_f0012_rm_release FOREIGN KEY (release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_rm_module FOREIGN KEY (module_version_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_module_version(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_term (
    release_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    term_iri text NOT NULL CHECK (term_iri ~ '^urn:nebula:ont:[a-z][a-z0-9.-]+$'),
    term_kind text NOT NULL
        CHECK (term_kind IN ('class','object_property','datatype_property','code_value')),
    definition_digest char(64) NOT NULL CHECK (definition_digest ~ '^[0-9a-f]{64}$'),
    normalized jsonb NOT NULL,
    predicate_key text,
    cardinality text CHECK (cardinality IN ('SINGLE','MULTI','RELATIONSHIP')),
    value_type text,
    temporal_kind text CHECK (temporal_kind IN ('STATE','EVENT','ETERNAL')),
    PRIMARY KEY (release_id, term_iri),
    CONSTRAINT uq_f0012_term_predicate UNIQUE (release_id, predicate_key),
    CONSTRAINT ck_f0012_term_predicate_shape CHECK (
        predicate_key IS NULL
        OR (cardinality IS NOT NULL AND value_type IS NOT NULL AND temporal_kind IS NOT NULL)),
    CONSTRAINT fk_f0012_term_release FOREIGN KEY (release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_change_record (
    id uuid PRIMARY KEY,
    release_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    change_class text NOT NULL
        CHECK (change_class IN ('rename_alias','semantic_change','split','merge','retirement')),
    source_iris text[] NOT NULL CHECK (cardinality(source_iris) >= 1),
    replacement_iris text[] NOT NULL,
    rationale text NOT NULL CHECK (length(rationale) > 0),
    CONSTRAINT ck_f0012_change_shape CHECK (
        (change_class = 'retirement' AND cardinality(replacement_iris) = 0)
        OR (change_class = 'split' AND cardinality(source_iris) = 1
            AND cardinality(replacement_iris) >= 2)
        OR (change_class = 'merge' AND cardinality(source_iris) >= 2
            AND cardinality(replacement_iris) = 1)
        OR (change_class IN ('rename_alias','semantic_change')
            AND cardinality(replacement_iris) >= 1)),
    CONSTRAINT fk_f0012_change_release FOREIGN KEY (release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_impact_report (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    predecessor_release_id uuid,
    candidate_release_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('complete','incomplete')),
    report_digest char(64) NOT NULL CHECK (report_digest ~ '^[0-9a-f]{64}$'),
    report jsonb NOT NULL,
    generated_by uuid NOT NULL REFERENCES principal(id),
    generated_at timestamptz NOT NULL,
    CONSTRAINT uq_f0012_report_digest UNIQUE (tenant_id, knowledge_base_id, report_digest),
    CONSTRAINT uq_f0012_report_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_report_pred FOREIGN KEY (predecessor_release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_report_cand FOREIGN KEY (candidate_release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_release_review (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    report_id uuid NOT NULL,
    decision text NOT NULL CHECK (decision IN ('approve','reject')),
    reviewer_principal_id uuid NOT NULL REFERENCES principal(id),
    decision_id uuid NOT NULL,
    rationale text NOT NULL CHECK (length(rationale) > 0),
    decided_at timestamptz NOT NULL,
    CONSTRAINT uq_f0012_review_owner UNIQUE (id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_review_report FOREIGN KEY (report_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_impact_report(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_release_selection (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    sequence bigint NOT NULL CHECK (sequence >= 1),
    action text NOT NULL CHECK (action IN ('activate','rollback')),
    release_id uuid NOT NULL,
    review_id uuid,
    actor_principal_id uuid NOT NULL REFERENCES principal(id),
    decision_id uuid NOT NULL,
    selected_at timestamptz NOT NULL,
    CONSTRAINT ck_f0012_selection_review CHECK ((action = 'activate') = (review_id IS NOT NULL)),
    CONSTRAINT uq_f0012_selection_seq UNIQUE (tenant_id, knowledge_base_id, sequence),
    CONSTRAINT fk_f0012_selection_release FOREIGN KEY (release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id),
    CONSTRAINT fk_f0012_selection_review FOREIGN KEY (review_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release_review(id, tenant_id, knowledge_base_id)
);

CREATE INDEX ix_f0012_term_predicate ON ontology_term (tenant_id, knowledge_base_id, predicate_key)
    WHERE predicate_key IS NOT NULL;
"""


def _refuse(message: str) -> str:
    return f"RAISE EXCEPTION '{message}' USING ERRCODE = 'check_violation';"


FUNCTIONS = {
    "brain_f0012_append_only": f"""
CREATE FUNCTION brain_f0012_append_only() RETURNS trigger {_SECURE} AS $$
BEGIN
    {_refuse("F0012 ontology release rows are append-only")}
END
$$""",
    "brain_f0012_selection_guard": f"""
CREATE FUNCTION brain_f0012_selection_guard() RETURNS trigger {_SECURE} AS $$
DECLARE
    head_sequence bigint;
    head_release uuid;
    review_decision text;
    report_status text;
    report_candidate uuid;
    report_predecessor uuid;
BEGIN
    SELECT s.sequence, s.release_id INTO head_sequence, head_release
      FROM public.ontology_release_selection s
     WHERE s.tenant_id = NEW.tenant_id AND s.knowledge_base_id = NEW.knowledge_base_id
     ORDER BY s.sequence DESC LIMIT 1;
    IF NEW.sequence <> COALESCE(head_sequence, 0) + 1 THEN
        {_refuse("ontology_release_selection: sequence is not the next value")}
    END IF;
    IF NEW.action = 'activate' THEN
        SELECT v.decision, r.status, r.candidate_release_id, r.predecessor_release_id
          INTO review_decision, report_status, report_candidate, report_predecessor
          FROM public.ontology_release_review v
          JOIN public.ontology_impact_report r
            ON r.id = v.report_id AND r.tenant_id = v.tenant_id
           AND r.knowledge_base_id = v.knowledge_base_id
         WHERE v.id = NEW.review_id AND v.tenant_id = NEW.tenant_id
           AND v.knowledge_base_id = NEW.knowledge_base_id;
        IF review_decision IS DISTINCT FROM 'approve' OR report_status IS DISTINCT FROM 'complete'
           OR report_candidate IS DISTINCT FROM NEW.release_id
           OR report_predecessor IS DISTINCT FROM head_release THEN
            {_refuse("ontology_release_selection: activation needs an approved complete report for this release and head")}
        END IF;
    ELSIF NOT EXISTS (
        SELECT 1 FROM public.ontology_release_selection s
         WHERE s.tenant_id = NEW.tenant_id AND s.knowledge_base_id = NEW.knowledge_base_id
           AND s.release_id = NEW.release_id AND s.action = 'activate') THEN
        {_refuse("ontology_release_selection: rollback target was never activated")}
    END IF;
    RETURN NEW;
END
$$""",
}


def _triggers() -> list[str]:
    statements = []
    for table in TABLES:
        statements.append(
            f"CREATE TRIGGER trg_f0012_{table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION brain_f0012_append_only()"
        )
        statements.append(
            f"CREATE TRIGGER trg_f0012_{table}_no_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION brain_f0012_append_only()"
        )
    statements.append(
        "CREATE TRIGGER trg_f0012_selection_guard BEFORE INSERT ON ontology_release_selection "
        "FOR EACH ROW EXECUTE FUNCTION brain_f0012_selection_guard()"
    )
    return statements


ACCESS_TYPES_BEFORE = "('content_artifact', 'review_task', 'fact_slot')"
ACCESS_TYPES_AFTER = "('content_artifact', 'review_task', 'fact_slot', 'ontology_release')"


def _access_check(types: str) -> None:
    op.execute("ALTER TABLE resource_access DROP CONSTRAINT ck_resource_access_type")
    op.execute(
        "ALTER TABLE resource_access ADD CONSTRAINT ck_resource_access_type "
        f"CHECK (resource_type IN {types})"
    )


def upgrade() -> None:
    _access_check(ACCESS_TYPES_AFTER)
    for definition in FUNCTIONS.values():
        op.execute(definition)
    op.execute(TABLES_DDL)
    for statement in _triggers():
        op.execute(statement)
    log.info("0017 F0012 ontology release tables installed; no existing row touched")


def downgrade() -> None:
    bind = op.get_bind()
    # WHY: ACCESS EXCLUSIVE in a fixed order makes the emptiness check and the
    # drops one race-free step.
    for table in sorted((*TABLES, "resource_access")):
        bind.execute(text(f"LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE"))
    counts = {t: bind.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES}
    counts["resource_access(ontology_release)"] = bind.execute(
        text("SELECT count(*) FROM resource_access WHERE resource_type = 'ontology_release'")
    ).scalar_one()
    if any(counts.values()):
        populated = ", ".join(f"{t}={n}" for t, n in counts.items() if n)
        raise RuntimeError(
            f"0017 downgrade refused: F0012 ontology rows exist ({populated}). "
            "No rows modified; roll forward instead."
        )
    for table in reversed(TABLES):
        op.execute(f"DROP TABLE {table}")
    for name in reversed(list(FUNCTIONS)):
        op.execute(f"DROP FUNCTION {name}()")
    _access_check(ACCESS_TYPES_BEFORE)
