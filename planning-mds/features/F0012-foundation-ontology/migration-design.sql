-- F0012 migration design (proposed 0017, after 0016). Plan run 2026-11-25-120320e9; ADR-0081 D4.
-- Design only: the feature run writes engine/migrations/versions/0017_f0012_ontology_releases.py
-- with the F0009 conventions (_SECURE plpgsql SECURITY INVOKER, check_violation refusals).
-- Every table is tenant/KB owned (ADR-0030) and append-only.

CREATE FUNCTION brain_f0012_append_only() RETURNS trigger
  LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
BEGIN
    RAISE EXCEPTION 'F0012 ontology release rows are append-only' USING ERRCODE = 'check_violation';
END
$$;

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
    -- Same module/version with another digest is refused by this key (S0004 AC2).
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
    manifest_digest char(64) NOT NULL,
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
    PRIMARY KEY (release_id, module_id),          -- one version per module per release
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
    term_kind text NOT NULL CHECK (term_kind IN ('class','object_property','datatype_property','code_value')),
    definition_digest char(64) NOT NULL,           -- labels/aliases excluded (ADR-0081 D1)
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
CREATE INDEX ix_f0012_term_predicate ON ontology_term (tenant_id, knowledge_base_id, predicate_key)
    WHERE predicate_key IS NOT NULL;

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
        OR (change_class = 'split' AND cardinality(source_iris) = 1 AND cardinality(replacement_iris) >= 2)
        OR (change_class = 'merge' AND cardinality(source_iris) >= 2 AND cardinality(replacement_iris) = 1)
        OR (change_class IN ('rename_alias','semantic_change') AND cardinality(replacement_iris) >= 1)),
    CONSTRAINT fk_f0012_change_release FOREIGN KEY (release_id, tenant_id, knowledge_base_id)
        REFERENCES ontology_release(id, tenant_id, knowledge_base_id)
);

CREATE TABLE ontology_impact_report (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    predecessor_release_id uuid,                   -- NULL only for a first release
    candidate_release_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('complete','incomplete')),
    report_digest char(64) NOT NULL,
    report jsonb NOT NULL,                         -- ontology-impact-report/v1
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
    decision_id uuid NOT NULL,                     -- authorization decision UUID (ADR-0062)
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
    review_id uuid,                                -- required for activate; rollback targets a previously activated release
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

-- A BEFORE INSERT trigger on ontology_release_selection (brain_f0012_selection_guard) also verifies,
-- under the same tenant/KB: sequence = previous max + 1; for 'activate', the review is 'approve', its
-- report is 'complete' and its candidate is NEW.release_id, and the report predecessor equals the
-- currently selected release (or both are NULL); for 'rollback', NEW.release_id was activated before.
-- The service checks the same rules first with typed refusals; the trigger is the backstop.

-- Append-only on all eight tables (UPDATE, DELETE, TRUNCATE):
--   CREATE TRIGGER trg_f0012_<table>_append_only BEFORE UPDATE OR DELETE ON <table>
--       FOR EACH ROW EXECUTE FUNCTION brain_f0012_append_only();
--   CREATE TRIGGER trg_f0012_<table>_no_truncate BEFORE TRUNCATE ON <table>
--       FOR EACH STATEMENT EXECUTE FUNCTION brain_f0012_append_only();

-- Downgrade: refuse (RAISE) when any ontology_release row exists; otherwise drop in reverse order.
-- No existing table or row is altered. No DDL on canonical_fact_version (ADR-0078 D10 CHECKs already exist).
