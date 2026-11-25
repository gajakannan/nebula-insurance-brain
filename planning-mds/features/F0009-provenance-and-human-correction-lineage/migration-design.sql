-- Proposed migration 0016; feature action resolves/rebases against the then-current head.
-- Nullable addition leaves historical rows NULL. A server-owned BEFORE INSERT trigger
-- stamps 1 on all new review decisions; no default/backfill rewrites old history.
ALTER TABLE review_decision ADD COLUMN correction_lineage_contract smallint NULL
 CHECK (correction_lineage_contract IS NULL OR correction_lineage_contract = 1);
CREATE TABLE learning_candidate_reservation (
 id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL,
 knowledge_base_id uuid NOT NULL,
 review_decision_id uuid NOT NULL UNIQUE,
 original_assertion_id uuid NOT NULL,
 corrected_assertion_id uuid NOT NULL UNIQUE,
 reviewer_principal_id uuid NOT NULL REFERENCES principal(id),
 reserved_at timestamptz NOT NULL,
 UNIQUE (id, tenant_id, knowledge_base_id),
 FOREIGN KEY (review_decision_id, tenant_id, knowledge_base_id)
   REFERENCES review_decision(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE,
 FOREIGN KEY (original_assertion_id, tenant_id, knowledge_base_id)
   REFERENCES assertion(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE,
 FOREIGN KEY (corrected_assertion_id, tenant_id, knowledge_base_id)
   REFERENCES assertion(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE
);
CREATE TABLE review_submission_attempt (
 id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL,
 knowledge_base_id uuid NOT NULL,
 review_item_id uuid NOT NULL,
 review_batch_id uuid NOT NULL,
 original_assertion_id uuid NOT NULL,
 reviewer_principal_id uuid NOT NULL REFERENCES principal(id),
 submitted_at timestamptz NOT NULL,
 event_sha256 text NOT NULL CHECK (event_sha256 ~ '^[a-f0-9]{64}$'),
 assertion_version integer NOT NULL CHECK (assertion_version > 0),
 action text NOT NULL CHECK (action IN ('ACCEPT','CORRECT','REJECT','BLOCKED')),
 reason_code text NULL CHECK (reason_code IS NULL OR reason_code IN
   ('MISREAD_VALUE','WRONG_REGION','NOT_IN_SOURCE','OUT_OF_SCOPE','EVIDENCE_UNRESOLVED')),
 corrected_value jsonb NULL,
 evidence jsonb NULL,
 reviewer_comment text NULL,
 outcome text NOT NULL CHECK (outcome IN ('ALREADY_DECIDED','BATCH_REFUSED')),
 authorization_decision_id uuid NOT NULL REFERENCES audit_event(id),
 UNIQUE (id, tenant_id, knowledge_base_id),
 -- One row per distinct (submission, outcome); repeat refusals reuse it (rework 2026-11-24-c32acf46, PR-H1).
 UNIQUE (review_item_id, event_sha256, outcome),
 FOREIGN KEY (review_item_id, tenant_id, knowledge_base_id)
   REFERENCES review_item(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE,
 FOREIGN KEY (review_batch_id, tenant_id, knowledge_base_id)
   REFERENCES review_batch(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE,
 FOREIGN KEY (original_assertion_id, tenant_id, knowledge_base_id)
   REFERENCES assertion(id, tenant_id, knowledge_base_id) DEFERRABLE INITIALLY IMMEDIATE
);
CREATE INDEX ix_f0009_reservation_original ON learning_candidate_reservation(original_assertion_id);
CREATE INDEX ix_f0009_attempt_assertion ON review_submission_attempt(original_assertion_id);
CREATE INDEX ix_f0009_assertion_parent ON assertion(original_assertion_id)
 WHERE original_assertion_id IS NOT NULL;
CREATE INDEX ix_f0009_decision_corrected ON review_decision(corrected_assertion_id)
 WHERE corrected_assertion_id IS NOT NULL;
-- Each new table: reject UPDATE, DELETE and TRUNCATE with SECURITY INVOKER trigger
-- function brain_f0009_append_only() (SQLSTATE check_violation).
-- BEFORE INSERT validation functions and deferred correction invariant are specified
-- precisely in the assembly plan; no existing row is rewritten or backfilled.
