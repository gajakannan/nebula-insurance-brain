"""F0006 additive versioned assertion semantics and immutable evidence.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


SCHEMA = r"""
ALTER TABLE assertion ADD COLUMN semantic_contract_version smallint NOT NULL DEFAULT 1;
ALTER TABLE assertion ADD CONSTRAINT ck_assertion_contract_version
  CHECK (semantic_contract_version IN (1,2));
ALTER TABLE assertion ADD CONSTRAINT ck_assertion_confidence
  CHECK (model_confidence IS NULL OR (model_confidence >= 0 AND model_confidence <= 1));

CREATE TABLE assertion_document_reference (
  id uuid PRIMARY KEY,
  document_version_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  entity_type text NOT NULL CHECK (length(entity_type) > 0),
  label text NOT NULL CHECK (length(label) > 0),
  created_by uuid NOT NULL REFERENCES principal(id),
  created_at timestamptz NOT NULL,
  CONSTRAINT uq_assertion_reference_owner UNIQUE
    (id,document_version_id,tenant_id,knowledge_base_id),
  CONSTRAINT fk_assertion_reference_document FOREIGN KEY
    (document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_version(id,tenant_id,knowledge_base_id)
);

CREATE TABLE assertion_name_claim (
  document_version_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  normalized_name text NOT NULL CHECK (length(normalized_name) > 0),
  entity_ref uuid NOT NULL,
  created_by uuid NOT NULL REFERENCES principal(id),
  created_at timestamptz NOT NULL,
  PRIMARY KEY (document_version_id,tenant_id,knowledge_base_id,normalized_name),
  CONSTRAINT fk_assertion_name_reference FOREIGN KEY
    (entity_ref,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES assertion_document_reference(id,document_version_id,tenant_id,knowledge_base_id)
);

CREATE TABLE assertion_semantics (
  assertion_id uuid PRIMARY KEY,
  document_version_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  subject_ref uuid NOT NULL,
  object_ref uuid,
  assertion_kind text NOT NULL,
  fact_mode text NOT NULL,
  assertion_origin text NOT NULL,
  predicate_id text,
  ontology_release text,
  record jsonb NOT NULL,
  entity_snapshots jsonb NOT NULL,
  verified_evidence jsonb NOT NULL,
  time_reference_snapshot jsonb NOT NULL,
  raw_item_sha256 char(64) NOT NULL,
  admission_sha256 char(64) NOT NULL,
  created_by uuid NOT NULL REFERENCES principal(id),
  created_at timestamptz NOT NULL,
  CONSTRAINT fk_assertion_semantics_owner FOREIGN KEY (assertion_id,tenant_id,knowledge_base_id)
    REFERENCES assertion(id,tenant_id,knowledge_base_id),
  CONSTRAINT fk_assertion_semantics_document FOREIGN KEY
    (document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_version(id,tenant_id,knowledge_base_id),
  CONSTRAINT fk_assertion_semantics_subject FOREIGN KEY
    (subject_ref,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES assertion_document_reference(id,document_version_id,tenant_id,knowledge_base_id),
  CONSTRAINT fk_assertion_semantics_object FOREIGN KEY
    (object_ref,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES assertion_document_reference(id,document_version_id,tenant_id,knowledge_base_id),
  CONSTRAINT ck_assertion_kind CHECK (assertion_kind IN ('OPEN_STATEMENT','TYPED_ASSERTION')),
  CONSTRAINT ck_assertion_mode CHECK (fact_mode IN ('ASSERTED','OBSERVED','DERIVED')),
  CONSTRAINT ck_assertion_origin CHECK (assertion_origin IN
    ('DOCUMENT_INTERPRETATION','SYSTEM_OBSERVATION',
    'HUMAN_REVIEW','CONVERSATION_DISCOVERY','RULE_DERIVATION','AGENT_ANALYSIS')),
  CONSTRAINT ck_assertion_kind_contract CHECK (coalesce(
    (assertion_kind = 'OPEN_STATEMENT' AND predicate_id IS NULL AND ontology_release IS NULL
      AND record->>'interpretation_basis' = 'EXPLICIT' AND length(record->>'source_relation') > 0)
    OR (assertion_kind = 'TYPED_ASSERTION' AND predicate_id IS NOT NULL AND length(predicate_id) > 0
      AND ontology_release IS NOT NULL AND length(ontology_release) > 0), false)),
  CONSTRAINT ck_assertion_record_shape CHECK (coalesce(jsonb_typeof(record) = 'object'
    AND record ?&
    ARRAY['id','assertion_kind','subject_ref','object','predicate_id','ontology_release',
      'source_relation','qualifiers','time_mention_refs','valid_time_claim','mode','origin',
      'interpretation_basis','model_confidence','evidence']
    AND jsonb_typeof(record->'qualifiers') = 'object'
    AND jsonb_typeof(record->'object') = 'object'
    AND jsonb_typeof(record->'evidence') = 'array' AND jsonb_array_length(record->'evidence') > 0
    AND jsonb_typeof(entity_snapshots) = 'array' AND jsonb_array_length(entity_snapshots) > 0
    AND jsonb_typeof(time_reference_snapshot) = 'array'
    AND jsonb_typeof(verified_evidence) = 'array' AND jsonb_array_length(verified_evidence) > 0
    AND record->>'interpretation_basis' IN ('EXPLICIT','INFERRED','AMBIGUOUS'),false)),
  CONSTRAINT ck_assertion_record_columns CHECK (coalesce(record->>'id' = assertion_id::text
    AND record->>'assertion_kind' = assertion_kind AND record->>'mode' = fact_mode
    AND record->>'origin' = assertion_origin AND record->>'subject_ref' = subject_ref::text
    AND (record->>'predicate_id') IS NOT DISTINCT FROM predicate_id
    AND (record->>'ontology_release') IS NOT DISTINCT FROM ontology_release
    AND ((record->'object'->>'kind' = 'ENTITY' AND object_ref IS NOT NULL
       AND record->'object'->>'ref' = object_ref::text AND length(record->'object'->>'name') > 0)
      OR (record->'object'->>'kind' = 'LITERAL' AND object_ref IS NULL AND (record->'object' ?
    'value'))),false)),
  CONSTRAINT ck_assertion_hashes CHECK (raw_item_sha256 ~ '^[0-9a-f]{64}$'
    AND admission_sha256 ~ '^[0-9a-f]{64}$')
);
CREATE INDEX ix_assertion_semantics_subject ON
    assertion_semantics(tenant_id,knowledge_base_id,subject_ref);
CREATE INDEX ix_assertion_semantics_document ON
    assertion_semantics(tenant_id,knowledge_base_id,document_version_id);

CREATE FUNCTION brain_assertion_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' OR NEW.version <> OLD.version + 1
    OR (to_jsonb(NEW) - 'version') IS DISTINCT FROM (to_jsonb(OLD) - 'version') THEN
    RAISE EXCEPTION 'assertion is append-only except the version increment'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_assertion_immutable BEFORE UPDATE OR DELETE ON assertion
  FOR EACH ROW EXECUTE FUNCTION brain_assertion_immutable();
CREATE TRIGGER trg_assertion_evidence_append_only BEFORE UPDATE OR DELETE ON assertion_evidence
  FOR EACH ROW EXECUTE FUNCTION brain_append_only();
CREATE TRIGGER trg_assertion_reference_append_only BEFORE UPDATE OR DELETE ON
    assertion_document_reference
  FOR EACH ROW EXECUTE FUNCTION brain_append_only();
CREATE TRIGGER trg_assertion_name_append_only BEFORE UPDATE OR DELETE ON assertion_name_claim
  FOR EACH ROW EXECUTE FUNCTION brain_append_only();
CREATE TRIGGER trg_assertion_semantics_append_only BEFORE UPDATE OR DELETE ON assertion_semantics
  FOR EACH ROW EXECUTE FUNCTION brain_append_only();

CREATE FUNCTION brain_assertion_v2_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  candidate_id uuid;
  a assertion%ROWTYPE;
  s assertion_semantics%ROWTYPE;
  parent assertion%ROWTYPE;
  parent_s assertion_semantics%ROWTYPE;
  subject_type text;
  expected_value jsonb;
BEGIN
  IF TG_TABLE_NAME = 'assertion' THEN candidate_id := NEW.id;
  ELSE candidate_id := NEW.assertion_id;
  END IF;
  SELECT * INTO a FROM assertion WHERE id = candidate_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'assertion semantic carrier missing' USING ERRCODE = 'check_violation';
  END IF;
  SELECT * INTO s FROM assertion_semantics WHERE assertion_id = candidate_id;
  IF a.semantic_contract_version = 1 THEN
    IF FOUND OR a.slot_type = '__OPEN_STATEMENT_V2__' THEN
      RAISE EXCEPTION 'legacy assertion cannot carry v2 semantics' USING ERRCODE =
    'check_violation';
    END IF;
    IF a.original_assertion_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM assertion WHERE id = a.original_assertion_id AND semantic_contract_version <>
    1) THEN
      RAISE EXCEPTION 'correction contract mismatch' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
  END IF;
  IF NOT FOUND OR (s.tenant_id,s.knowledge_base_id) IS DISTINCT FROM
    (a.tenant_id,a.knowledge_base_id)
    OR s.assertion_origin IS DISTINCT FROM a.origin
    OR s.record->>'interpretation_basis' IS DISTINCT FROM a.interpretation_basis
    OR coalesce(to_jsonb(a.model_confidence),'null'::jsonb) IS DISTINCT FROM
    s.record->'model_confidence'
    OR a.slot_type IS DISTINCT FROM coalesce(s.predicate_id,'__OPEN_STATEMENT_V2__') THEN
    RAISE EXCEPTION 'v2 assertion carrier disagrees with semantic extension' USING ERRCODE =
    'check_violation';
  END IF;
  SELECT r.entity_type INTO subject_type FROM assertion_document_reference r
    WHERE r.id=s.subject_ref AND r.document_version_id=s.document_version_id
      AND r.tenant_id=s.tenant_id AND r.knowledge_base_id=s.knowledge_base_id;
  IF subject_type IS NULL OR a.subject_type IS DISTINCT FROM subject_type THEN
    RAISE EXCEPTION 'v2 assertion subject carrier mismatch' USING ERRCODE = 'check_violation';
  END IF;
  IF s.record->'object'->>'kind' = 'ENTITY' THEN
    expected_value := jsonb_build_object('object_ref',s.object_ref::text);
  ELSIF jsonb_typeof(s.record->'object'->'value') = 'object' THEN
    expected_value := s.record->'object'->'value';
  ELSE
    expected_value := jsonb_build_object('literal',s.record->'object'->'value');
  END IF;
  IF a.value IS DISTINCT FROM expected_value THEN
    RAISE EXCEPTION 'v2 assertion value carrier mismatch' USING ERRCODE = 'check_violation';
  END IF;
  IF a.original_assertion_id IS NULL THEN
    IF a.run_id IS NULL OR NOT EXISTS (
      SELECT 1 FROM semantic_interpretation_run r JOIN content_artifact c ON c.id=r.artifact_id
      WHERE r.id=a.run_id AND r.tenant_id=a.tenant_id AND r.knowledge_base_id=a.knowledge_base_id
        AND c.tenant_id=a.tenant_id AND c.knowledge_base_id=a.knowledge_base_id
        AND c.document_version_id=s.document_version_id) THEN
      RAISE EXCEPTION 'v2 assertion run/source mismatch' USING ERRCODE = 'check_violation';
    END IF;
  ELSE
    SELECT * INTO parent FROM assertion WHERE id=a.original_assertion_id;
    SELECT * INTO parent_s FROM assertion_semantics WHERE assertion_id=a.original_assertion_id;
    IF a.run_id IS NOT NULL OR a.origin <> 'HUMAN_REVIEW' OR parent.id IS NULL
      OR parent.semantic_contract_version <> 2 OR parent_s.assertion_id IS NULL
      OR (a.tenant_id,a.knowledge_base_id,a.subject_type,a.slot_type,a.interpretation_basis)
        IS DISTINCT FROM
    (parent.tenant_id,parent.knowledge_base_id,parent.subject_type,parent.slot_type,parent.interpretation_basis)
      OR
    (s.document_version_id,s.subject_ref,s.object_ref,s.assertion_kind,s.fact_mode,s.predicate_id,s.ontology_release)
        IS DISTINCT FROM
    (parent_s.document_version_id,parent_s.subject_ref,parent_s.object_ref,parent_s.assertion_kind,parent_s.fact_mode,parent_s.predicate_id,parent_s.ontology_release)
      OR s.record->'qualifiers' IS DISTINCT FROM parent_s.record->'qualifiers'
      OR s.record->'source_relation' IS DISTINCT FROM parent_s.record->'source_relation'
      OR s.record->'valid_time_claim' IS DISTINCT FROM parent_s.record->'valid_time_claim'
      OR s.record->'time_mention_refs' IS DISTINCT FROM parent_s.record->'time_mention_refs'
      OR s.entity_snapshots IS DISTINCT FROM parent_s.entity_snapshots
      OR s.time_reference_snapshot IS DISTINCT FROM parent_s.time_reference_snapshot
      OR (s.assertion_kind='OPEN_STATEMENT' AND s.record->'object' IS DISTINCT FROM
    parent_s.record->'object') THEN
      RAISE EXCEPTION 'v2 correction changes immutable semantics' USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  IF (SELECT count(*) FROM assertion_evidence e WHERE e.assertion_id=a.id) <>
    jsonb_array_length(s.verified_evidence)
    OR EXISTS (
      SELECT 1 FROM jsonb_array_elements(s.verified_evidence) v
      WHERE NOT EXISTS (
        SELECT 1 FROM assertion_evidence e JOIN content_artifact c ON c.id=e.artifact_id
        WHERE e.id::text=v->>'evidence_id' AND e.assertion_id=a.id
          AND (e.tenant_id,e.knowledge_base_id)=(a.tenant_id,a.knowledge_base_id)
          AND e.artifact_id::text=v->>'artifact_id' AND e.block_id IS NOT DISTINCT FROM
    (v->>'block_id')
          AND e.precision=v->>'precision'
          AND e.page IS NOT DISTINCT FROM (v->'selector'->>'page')::integer
          AND NULLIF(e.bbox::jsonb,'null'::jsonb) IS NOT DISTINCT FROM
            NULLIF(v->'selector'->'bbox','null'::jsonb)
          AND e.char_start IS NOT DISTINCT FROM (v->'selector'->>'char_start')::integer
          AND e.char_end IS NOT DISTINCT FROM (v->'selector'->>'char_end')::integer
          AND c.document_version_id=s.document_version_id
          AND (c.tenant_id,c.knowledge_base_id)=(a.tenant_id,a.knowledge_base_id))) THEN
    RAISE EXCEPTION 'v2 assertion verified evidence mismatch' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER trg_assertion_v2_integrity AFTER INSERT ON assertion
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION brain_assertion_v2_integrity();
CREATE CONSTRAINT TRIGGER trg_assertion_semantics_v2_integrity AFTER INSERT ON assertion_semantics
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION brain_assertion_v2_integrity();
CREATE CONSTRAINT TRIGGER trg_assertion_evidence_v2_integrity AFTER INSERT ON assertion_evidence
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION brain_assertion_v2_integrity();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    # WHY: old binaries cannot represent v2 rows; rollback must retain evidence.
    occupied = (
        op.get_bind()
        .execute(
            text("""SELECT
      EXISTS(SELECT 1 FROM assertion WHERE semantic_contract_version=2)
      OR EXISTS(SELECT 1 FROM assertion_semantics)
      OR EXISTS(SELECT 1 FROM assertion_document_reference)
      OR EXISTS(SELECT 1 FROM assertion_name_claim)""")
        )
        .scalar_one()
    )
    if occupied:
        raise RuntimeError("0011 downgrade refused: retain v2 semantics and guard-capable readers")
    op.execute("DROP TRIGGER trg_assertion_evidence_v2_integrity ON assertion_evidence")
    op.execute("DROP TRIGGER trg_assertion_semantics_v2_integrity ON assertion_semantics")
    op.execute("DROP TRIGGER trg_assertion_v2_integrity ON assertion")
    op.execute("DROP FUNCTION brain_assertion_v2_integrity()")
    op.execute("DROP TRIGGER trg_assertion_evidence_append_only ON assertion_evidence")
    op.execute("DROP TRIGGER trg_assertion_immutable ON assertion")
    op.execute("DROP FUNCTION brain_assertion_immutable()")
    op.drop_table("assertion_semantics")
    op.drop_table("assertion_name_claim")
    op.drop_table("assertion_document_reference")
    op.drop_constraint("ck_assertion_confidence", "assertion", type_="check")
    op.drop_constraint("ck_assertion_contract_version", "assertion", type_="check")
    op.drop_column("assertion", "semantic_contract_version")
