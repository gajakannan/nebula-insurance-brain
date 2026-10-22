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
  -- Per-document v1 fallback after v2 activation (re-review R-M1): set at insert only.
  ADD COLUMN writer_fallback_reason text,
  ADD CONSTRAINT ck_content_contract_version CHECK (artifact_contract_version IN (1,2)),
  ADD CONSTRAINT ck_content_publication_state CHECK (publication_state IN ('legacy_unverified','ready','quarantined')),
  ADD CONSTRAINT ck_content_writer_fallback CHECK (writer_fallback_reason IS NULL OR
    (writer_fallback_reason = 'ORIGIN_UNAVAILABLE' AND artifact_contract_version = 1)),
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
  -- v0.1: every selection or clear carries a verified human selection decision
  -- (F0022 producer). actor_principal_id is the calling principal; the deciding
  -- human is human_actor_principal_id. The default verifier rejects, so no row
  -- can be written outside controlled verifier fixtures until F0022 lands.
  human_decision_id uuid NOT NULL,
  human_actor_principal_id uuid NOT NULL REFERENCES principal(id),
  human_authorization_decision_id uuid NOT NULL,
  human_decided_at timestamptz NOT NULL,
  human_receipt_sha256 varchar(64) NOT NULL CHECK (human_receipt_sha256 ~ '^[a-f0-9]{64}$'),
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

-- Artifact lifecycle (operator decision 2026-10-16, plan-review H-2).
-- legacy_unverified: pre-F0004 v1 row; readable through the v1 verifier
--   (full bundle hash against artifact_sha256 on every read).
-- ready: verified; v2 rows are written directly in this state.
-- quarantined: a definitive verification failure (hash mismatch, missing
--   declared file under a complete marker); reads return 409 ARTIFACT_INTEGRITY.
--   Transient storage errors (503 CONTENT_UNAVAILABLE) never quarantine.
-- A read that fails verification returns 409 and only persists its failed read
-- decision; it never writes here (re-review R-H1). Every transition is written by
-- an operator-run job or authorized repair under in-transaction authorization:
-- decide() over SyncAuthorityStore, decision and effects committed together.
-- Insert order: content_repair_record, audit_event, state event, then UPDATE.
-- Allowed transitions; everything else is rejected:
--   legacy_unverified -> ready        readiness backfill after verification
--   legacy_unverified -> quarantined  backfill or integrity-sweep failure
--   ready -> quarantined              integrity-sweep or backfill failure
--   quarantined -> ready              authorized repair after byte re-verification
CREATE TABLE content_artifact_state_event (
  id uuid PRIMARY KEY,
  artifact_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  from_state text NOT NULL,
  to_state text NOT NULL,
  trigger text NOT NULL CHECK (trigger IN ('LEGACY_BACKFILL','INTEGRITY_SWEEP','AUTHORIZED_REPAIR')),
  reason_code text NOT NULL CHECK (reason_code IN ('VERIFIED','HASH_MISMATCH','MISSING_FILE','MANIFEST_INVALID','REPAIRED')),
  actor_principal_id uuid NOT NULL REFERENCES principal(id),
  -- The in-transaction decision of the writing job or repair; never a read decision.
  authorization_decision_id uuid NOT NULL,
  audit_event_id uuid NOT NULL REFERENCES audit_event(id),
  repair_record_id uuid,
  -- Stamped by content_artifact_state_event_stamp; a supplied value is overwritten.
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (artifact_id,tenant_id,knowledge_base_id)
    REFERENCES content_artifact(id,tenant_id,knowledge_base_id),
  CHECK ((from_state,to_state) IN (('legacy_unverified','ready'),('legacy_unverified','quarantined'),
                                   ('ready','quarantined'),('quarantined','ready'))),
  -- Promotion out of quarantine needs current content_artifact:ingest authority.
  CHECK (NOT (from_state='quarantined') OR trigger='AUTHORIZED_REPAIR')
);

-- Repair records (plan-review M-3): the durable carrier for anything that needs a
-- governed repair. Written only under in-transaction authorization by operator-run
-- jobs (the backfill, the integrity sweep including orphan-marker detection) and
-- authorized repair; resolved only by appending a resolving row. The isolated
-- restore drill reports in its own evidence and never writes here.
-- Owner: DevOps (triage/repair runbook). No API route and no tenant or human grant
-- reads or writes it.
CREATE TABLE content_repair_record (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  artifact_id uuid,
  storage_key text,
  kind text NOT NULL CHECK (kind IN ('LEGACY_BACKFILL_BLOCKED','INTEGRITY_FAILURE','ORPHAN_MARKER')),
  detail jsonb NOT NULL CHECK (jsonb_typeof(detail)='object'),
  resolves_id uuid REFERENCES content_repair_record(id),
  resolution text CHECK (resolution IN ('REPAIRED','ACCEPTED_LOSS','FALSE_POSITIVE')),
  recorded_by uuid NOT NULL REFERENCES principal(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (artifact_id,tenant_id,knowledge_base_id)
    REFERENCES content_artifact(id,tenant_id,knowledge_base_id),
  CHECK (artifact_id IS NOT NULL OR storage_key IS NOT NULL),
  CHECK ((resolves_id IS NULL) = (resolution IS NULL))
);
ALTER TABLE content_artifact_state_event ADD CONSTRAINT fk_f0004_state_repair
  FOREIGN KEY (repair_record_id) REFERENCES content_repair_record(id);
CREATE TRIGGER content_artifact_state_event_immutable BEFORE UPDATE OR DELETE ON content_artifact_state_event
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
CREATE TRIGGER content_repair_record_immutable BEFORE UPDATE OR DELETE ON content_repair_record
  FOR EACH ROW EXECUTE FUNCTION f0004_reject_history_mutation();
-- Re-review R-L1: the guard below proves same-transaction by created_at = now(),
-- so created_at is always the transaction timestamp.
CREATE FUNCTION f0004_stamp_state_event() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.created_at := now();
  RETURN NEW;
END;
$$;
CREATE TRIGGER content_artifact_state_event_stamp BEFORE INSERT ON content_artifact_state_event
  FOR EACH ROW EXECUTE FUNCTION f0004_stamp_state_event();

-- Ready-row guard (plan-review L-3). Identity and content columns are frozen once a
-- row leaves legacy_unverified; while legacy_unverified, the backfill may only fill
-- NULL metadata columns. Every state change needs a same-transaction state event.
-- Writers insert the state event first, then UPDATE content_artifact, in one
-- transaction (re-review R-L1); an UPDATE before its event is rejected.
CREATE FUNCTION f0004_guard_content_artifact() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'F0004 content_artifact rows are not deleted';
  END IF;
  IF (NEW.id, NEW.document_version_id, NEW.tenant_id, NEW.knowledge_base_id, NEW.artifact_sha256, NEW.writer_fallback_reason)
     IS DISTINCT FROM (OLD.id, OLD.document_version_id, OLD.tenant_id, OLD.knowledge_base_id, OLD.artifact_sha256, OLD.writer_fallback_reason) THEN
    RAISE EXCEPTION 'F0004 content_artifact identity, bundle hash and fallback reason are immutable';
  END IF;
  IF OLD.publication_state <> 'legacy_unverified' AND
     (NEW.artifact_contract_version, NEW.recipe_sha256, NEW.manifest_sha256, NEW.supersedes_artifact_id)
     IS DISTINCT FROM (OLD.artifact_contract_version, OLD.recipe_sha256, OLD.manifest_sha256, OLD.supersedes_artifact_id) THEN
    RAISE EXCEPTION 'F0004 verified content_artifact metadata is immutable';
  END IF;
  IF OLD.publication_state = 'legacy_unverified' AND
     ((OLD.artifact_contract_version IS NOT NULL AND NEW.artifact_contract_version IS DISTINCT FROM OLD.artifact_contract_version)
      OR (OLD.recipe_sha256 IS NOT NULL AND NEW.recipe_sha256 IS DISTINCT FROM OLD.recipe_sha256)
      OR (OLD.manifest_sha256 IS NOT NULL AND NEW.manifest_sha256 IS DISTINCT FROM OLD.manifest_sha256)) THEN
    RAISE EXCEPTION 'F0004 backfill may only fill missing legacy metadata';
  END IF;
  IF NEW.publication_state IS DISTINCT FROM OLD.publication_state AND NOT EXISTS (
       SELECT 1 FROM content_artifact_state_event e
       WHERE e.artifact_id = OLD.id AND e.from_state = OLD.publication_state
         AND e.to_state = NEW.publication_state AND e.created_at = now()) THEN
    RAISE EXCEPTION 'F0004 publication_state change needs a same-transaction state event';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER content_artifact_guard BEFORE UPDATE OR DELETE ON content_artifact
  FOR EACH ROW EXECUTE FUNCTION f0004_guard_content_artifact();

-- Services additionally validate schema/basis authority, cross-row bounds, cycles,
-- latest-selection CAS, contiguous sequence and exact provenance/index digests.
-- Actor principals are global F0002 identities: never invent a KB owner for principal.
-- authorization_decision_id is the semantic decision UUID; audit_event.id is different.
-- authorization_audit_event_id references the authorization_decision event row.
-- Service verifies that row.decision_id equals authorization_decision_id and checks
-- event type, action, actor, owner and allowed outcome in the same transaction.
-- content_artifact_guard (above) enforces identity/metadata immutability and the
-- same-transaction state event (now() is the transaction timestamp). Existing owner
-- guards remain active. No cleanup/retention bypass is introduced here.
-- Quarantined rows return to ready only through AUTHORIZED_REPAIR after byte
-- re-verification, with current content_artifact:ingest authority and audit.
-- New v2 rows and per-document v1 fallback rows are inserted directly as ready;
-- the state machine covers changes only.
