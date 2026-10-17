-- F0004 proposed migration design. NOT applied by the plan action.
-- Implement as the next Alembic revision after 0007, using catalog-discovered
-- names for existing constraints. Expand first; reconcile bytes before activation.
-- Preserve the existing F0002 owner FKs, owner-immutability guards and IDs.

ALTER TABLE content_artifact
  ADD COLUMN artifact_contract_version smallint,
  ADD COLUMN recipe_sha256 varchar(64),
  ADD COLUMN manifest_sha256 varchar(64),
  ADD COLUMN supersedes_artifact_id uuid,
  ADD COLUMN publication_state text NOT NULL DEFAULT 'legacy_unverified',
  ADD CONSTRAINT ck_content_contract_version CHECK (artifact_contract_version IN (1,2)),
  ADD CONSTRAINT ck_content_publication_state CHECK (publication_state IN ('legacy_unverified','ready','quarantined')),
  ADD CONSTRAINT ck_content_v2_metadata CHECK (
    artifact_contract_version IS DISTINCT FROM 2 OR
    (recipe_sha256 IS NOT NULL AND recipe_sha256 ~ '^[a-f0-9]{64}$'
      AND manifest_sha256 IS NOT NULL AND manifest_sha256 ~ '^[a-f0-9]{64}$'));
-- Existing scoped (id,tenant_id,knowledge_base_id) unique keys are retained.
ALTER TABLE content_artifact ADD CONSTRAINT uq_f0004_artifact_version_owner
  UNIQUE (id, document_version_id, tenant_id, knowledge_base_id);
ALTER TABLE content_artifact ADD CONSTRAINT fk_f0004_artifact_predecessor
  FOREIGN KEY (supersedes_artifact_id,document_version_id,tenant_id,knowledge_base_id)
  REFERENCES content_artifact(id,document_version_id,tenant_id,knowledge_base_id)
  DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE content_artifact ADD CONSTRAINT ck_f0004_artifact_not_self
  CHECK (supersedes_artifact_id IS DISTINCT FROM id);
-- After legacy reconciliation: remove ONLY the existing UNIQUE(document_version_id).
-- Migration must discover its actual name; do not drop scoped foreign keys.
CREATE UNIQUE INDEX uq_f0004_v2_recipe ON content_artifact(document_version_id,recipe_sha256)
  WHERE artifact_contract_version=2;

CREATE TABLE content_block (
  artifact_id uuid NOT NULL,
  block_id text NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  native_ref text NOT NULL,
  reading_order integer NOT NULL CHECK (reading_order>=0),
  section_path jsonb NOT NULL CHECK (jsonb_typeof(section_path)='array'),
  text_origin text NOT NULL CHECK (text_origin IN ('STATED','OCR','TRANSCRIBED','DESCRIBED')),
  producer jsonb NOT NULL,
  origin_anchor jsonb NOT NULL,
  confidence double precision CHECK (confidence>=0 AND confidence<=1),
  record_ordinal integer NOT NULL CHECK (record_ordinal>=0),
  record_sha256 varchar(64) NOT NULL CHECK (record_sha256 ~ '^[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES principal(id),
  PRIMARY KEY (artifact_id,block_id),
  UNIQUE (artifact_id,block_id,tenant_id,knowledge_base_id),
  UNIQUE (artifact_id,record_ordinal),
  FOREIGN KEY (artifact_id,tenant_id,knowledge_base_id)
    REFERENCES content_artifact(id,tenant_id,knowledge_base_id)
);
CREATE TABLE content_table (
  artifact_id uuid NOT NULL,
  table_id text NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  native_ref text NOT NULL,
  num_rows integer NOT NULL CHECK (num_rows>=0),
  num_cols integer NOT NULL CHECK (num_cols>=0),
  header_rows jsonb NOT NULL CHECK (jsonb_typeof(header_rows)='array'),
  continuation_of text,
  record_ordinal integer NOT NULL CHECK (record_ordinal>=0),
  record_sha256 varchar(64) NOT NULL CHECK (record_sha256 ~ '^[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES principal(id),
  PRIMARY KEY (artifact_id,table_id),
  UNIQUE (artifact_id,table_id,tenant_id,knowledge_base_id),
  UNIQUE (artifact_id,record_ordinal),
  FOREIGN KEY (artifact_id,tenant_id,knowledge_base_id)
    REFERENCES content_artifact(id,tenant_id,knowledge_base_id),
  FOREIGN KEY (artifact_id,continuation_of,tenant_id,knowledge_base_id)
    REFERENCES content_table(artifact_id,table_id,tenant_id,knowledge_base_id)
    DEFERRABLE INITIALLY IMMEDIATE,
  CHECK (continuation_of IS DISTINCT FROM table_id)
);
CREATE TABLE content_table_cell (
  artifact_id uuid NOT NULL,
  table_id text NOT NULL,
  cell_id text NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  row_start integer NOT NULL CHECK (row_start>=0),
  col_start integer NOT NULL CHECK (col_start>=0),
  row_span integer NOT NULL CHECK (row_span>0),
  col_span integer NOT NULL CHECK (col_span>0),
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES principal(id),
  PRIMARY KEY (artifact_id,table_id,cell_id),
  UNIQUE (artifact_id,table_id,cell_id,tenant_id,knowledge_base_id),
  FOREIGN KEY (artifact_id,table_id,tenant_id,knowledge_base_id)
    REFERENCES content_table(artifact_id,table_id,tenant_id,knowledge_base_id)
);
CREATE TABLE content_table_cell_block (
  artifact_id uuid NOT NULL,
  table_id text NOT NULL,
  cell_id text NOT NULL,
  block_id text NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES principal(id),
  PRIMARY KEY (artifact_id,table_id,cell_id,block_id),
  FOREIGN KEY (artifact_id,table_id,cell_id,tenant_id,knowledge_base_id)
    REFERENCES content_table_cell(artifact_id,table_id,cell_id,tenant_id,knowledge_base_id),
  FOREIGN KEY (artifact_id,block_id,tenant_id,knowledge_base_id)
    REFERENCES content_block(artifact_id,block_id,tenant_id,knowledge_base_id)
);

CREATE TABLE document_date_candidate (
  id uuid PRIMARY KEY,
  document_version_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  date_value varchar(10) NOT NULL,
  date_precision text NOT NULL CHECK (date_precision IN ('YEAR','MONTH','DAY')),
  basis_kind text NOT NULL CHECK (basis_kind IN ('CONTENT','SOURCE_METADATA','HUMAN')),
  basis jsonb NOT NULL CHECK (jsonb_typeof(basis)='object'),
  content_artifact_id uuid,
  content_block_id text,
  supersedes_id uuid,
  idempotency_key text NOT NULL CHECK (length(idempotency_key)>0),
  request_sha256 varchar(64) NOT NULL CHECK (request_sha256 ~ '^[a-f0-9]{64}$'),
  actor_principal_id uuid NOT NULL REFERENCES principal(id),
  authorization_decision_id uuid NOT NULL,
  authorization_audit_event_id uuid NOT NULL REFERENCES audit_event(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id,document_version_id,tenant_id,knowledge_base_id),
  UNIQUE (document_version_id,idempotency_key),
  FOREIGN KEY (document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_version(id,tenant_id,knowledge_base_id),
  FOREIGN KEY (supersedes_id,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_date_candidate(id,document_version_id,tenant_id,knowledge_base_id)
    DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (content_artifact_id,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES content_artifact(id,document_version_id,tenant_id,knowledge_base_id),
  -- CONTENT points to an exact immutable JSONL line in basis (ordinal + SHA-256).
  -- Legacy v1 IDs may repeat and have no v2 index; service verifies the line and quote.
  -- V2 additionally verifies the matching content_block index before insertion.
  CHECK (supersedes_id IS DISTINCT FROM id),
  CHECK (basis->>'kind'=basis_kind),
  CHECK ((basis_kind='CONTENT' AND content_artifact_id IS NOT NULL AND content_block_id IS NOT NULL)
      OR (basis_kind<>'CONTENT' AND content_artifact_id IS NULL AND content_block_id IS NULL)),
  CHECK (CASE date_precision
    WHEN 'YEAR' THEN date_value ~ '^[0-9]{4}$' AND date_value::integer BETWEEN 1 AND 9999
    WHEN 'MONTH' THEN date_value ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'
      AND substring(date_value,1,4)::integer BETWEEN 1 AND 9999
    WHEN 'DAY' THEN date_value ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
      AND date_value::date::text=date_value
    ELSE false END)
);
CREATE TABLE document_date_selection (
  id uuid PRIMARY KEY,
  document_version_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  candidate_id uuid,
  previous_selection_id uuid,
  sequence bigint NOT NULL CHECK (sequence>0),
  reason text NOT NULL CHECK (length(reason)>0),
  idempotency_key text NOT NULL CHECK (length(idempotency_key)>0),
  request_sha256 varchar(64) NOT NULL CHECK (request_sha256 ~ '^[a-f0-9]{64}$'),
  actor_principal_id uuid NOT NULL REFERENCES principal(id),
  authorization_decision_id uuid NOT NULL,
  authorization_audit_event_id uuid NOT NULL REFERENCES audit_event(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id,document_version_id,tenant_id,knowledge_base_id),
  UNIQUE (document_version_id,sequence),
  UNIQUE (document_version_id,idempotency_key),
  FOREIGN KEY (document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_version(id,tenant_id,knowledge_base_id),
  FOREIGN KEY (candidate_id,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_date_candidate(id,document_version_id,tenant_id,knowledge_base_id),
  FOREIGN KEY (previous_selection_id,document_version_id,tenant_id,knowledge_base_id)
    REFERENCES document_date_selection(id,document_version_id,tenant_id,knowledge_base_id)
    DEFERRABLE INITIALLY IMMEDIATE,
  CHECK (previous_selection_id IS DISTINCT FROM id),
  CHECK ((sequence=1 AND previous_selection_id IS NULL) OR (sequence>1 AND previous_selection_id IS NOT NULL))
);

CREATE FUNCTION f0004_reject_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'F0004 content indexes and date records are append-only';
END;
$$;
CREATE TRIGGER content_block_immutable BEFORE UPDATE OR DELETE ON content_block
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER content_table_immutable BEFORE UPDATE OR DELETE ON content_table
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER content_table_cell_immutable BEFORE UPDATE OR DELETE ON content_table_cell
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER content_cell_block_immutable BEFORE UPDATE OR DELETE ON content_table_cell_block
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER document_date_candidate_immutable BEFORE UPDATE OR DELETE ON document_date_candidate
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER document_date_selection_immutable BEFORE UPDATE OR DELETE ON document_date_selection
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();

-- Services additionally validate schema/basis authority, cross-row bounds, cycles,
-- latest-selection CAS, contiguous sequence and exact provenance/index digests.
-- Actor principals are global F0002 identities: never invent a KB owner for principal.
-- authorization_decision_id is the semantic decision UUID; audit_event.id is different.
-- authorization_audit_event_id references the authorization_decision event row.
-- Service verifies that row.decision_id equals authorization_decision_id and checks
-- event type, action, actor, owner and allowed outcome in the same transaction.
-- Core content_artifact identity/hash/recipe/manifest fields become immutable when
-- publication_state is ready. Implement a BEFORE UPDATE/DELETE trigger that rejects
-- identity/content changes; lifecycle-only state changes require current authority
-- and an append-only artifact-state audit in the same transaction. Existing owner
-- guards remain active. No cleanup/retention bypass is introduced here.
-- Quarantined rows cannot be promoted without byte verification and authorized audit.
