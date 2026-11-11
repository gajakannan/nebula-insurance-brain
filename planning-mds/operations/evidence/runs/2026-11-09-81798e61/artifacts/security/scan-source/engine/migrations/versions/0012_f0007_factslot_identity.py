"""F0007 FactSlot identity: additive identity columns and qualifier rows (ADR-0077 D8).

Additive only. Existing pilot slots keep NULL identity columns ("legacy") and are
never retro-checked or backfilled. Nothing touches `canonical_fact_version`,
which F0008 owns.

- `fact_slot` gains nullable identity columns, a generated `subject_kb_entity_id`
  (NULL for legacy rows, so the subject-KB key ignores them under MATCH SIMPLE),
  a partial unique fingerprint index, and owner-bound parent/subject/object keys.
- `fact_slot_qualifier` holds the authoritative normalized qualifier rows,
  append-only and bound to the slot's owner by a composite foreign key.
- Identity columns are immutable by trigger, including NULL to value, so a
  legacy row can never acquire a fabricated identity.
- A deferred constraint trigger checks, at transaction end, that a member's
  parent is an identity-v1 MULTI header and that a qualifier's slot is an
  identity-v1 header.

No RLS policy, BYPASSRLS role or SECURITY DEFINER function is added; the trigger
functions run with invoker rights. F0018 enables RLS on `fact_slot` and
`fact_slot_qualifier`.

Downgrade refuses while any identity-v1 slot or qualifier row exists; evidence is
never deleted to make a downgrade pass.

Revision ID: 0012
Revises: 0011
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

IDENTITY_COLUMNS = (
    "identity_version",
    "slot_role",
    "predicate_key",
    "predicate_release_ref",
    "cardinality",
    "object_entity_id",
    "parent_slot_id",
    "member_key",
    "fingerprint_version",
    "identity_fingerprint",
    "created_by",
)

UPGRADE = r"""
ALTER TABLE fact_slot
  ADD COLUMN identity_version smallint,
  ADD COLUMN slot_role text,
  ADD COLUMN predicate_key text,
  ADD COLUMN predicate_release_ref text,
  ADD COLUMN cardinality text,
  ADD COLUMN object_entity_id uuid,
  ADD COLUMN parent_slot_id uuid,
  ADD COLUMN member_key text,
  ADD COLUMN fingerprint_version smallint,
  ADD COLUMN identity_fingerprint char(64),
  ADD COLUMN created_by uuid,
  ADD COLUMN subject_kb_entity_id uuid
    GENERATED ALWAYS AS (CASE WHEN identity_version IS NOT NULL THEN entity_id END) STORED;

ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_created_by
  FOREIGN KEY (created_by) REFERENCES principal(id);

ALTER TABLE fact_slot ADD CONSTRAINT ck_fact_slot_identity CHECK (
  (identity_version IS NULL AND slot_role IS NULL AND predicate_key IS NULL
     AND predicate_release_ref IS NULL AND cardinality IS NULL AND object_entity_id IS NULL
     AND parent_slot_id IS NULL AND member_key IS NULL AND fingerprint_version IS NULL
     AND identity_fingerprint IS NULL AND created_by IS NULL)
  OR (identity_version = 1 AND fingerprint_version = 1 AND created_by IS NOT NULL
     AND identity_fingerprint ~ '^[0-9a-f]{64}$'
     AND predicate_key ~ '^[a-z][a-z0-9-]{0,31}:[A-Za-z][A-Za-z0-9]{0,63}@v[1-9][0-9]{0,3}$'
     AND length(predicate_release_ref) > 0 AND slot_type = predicate_key
     AND cardinality IN ('SINGLE','MULTI','RELATIONSHIP')
     AND ((slot_role = 'SLOT' AND parent_slot_id IS NULL AND member_key IS NULL
            AND ((cardinality = 'RELATIONSHIP') = (object_entity_id IS NOT NULL)))
       OR (slot_role = 'MEMBER' AND cardinality = 'MULTI' AND parent_slot_id IS NOT NULL
            AND length(member_key) > 0 AND object_entity_id IS NULL))));

CREATE UNIQUE INDEX uq_fact_slot_identity
  ON fact_slot (tenant_id, knowledge_base_id, identity_fingerprint)
  WHERE identity_version IS NOT NULL;
CREATE INDEX ix_fact_slot_parent ON fact_slot (parent_slot_id) WHERE parent_slot_id IS NOT NULL;
CREATE INDEX ix_fact_slot_subject_predicate
  ON fact_slot (knowledge_base_id, entity_id, predicate_key)
  WHERE identity_version IS NOT NULL;

ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_parent_owner FOREIGN KEY
  (parent_slot_id, tenant_id, knowledge_base_id)
  REFERENCES fact_slot (id, tenant_id, knowledge_base_id);
ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_subject_kb FOREIGN KEY
  (subject_kb_entity_id, tenant_id, knowledge_base_id)
  REFERENCES entity_knowledge_base (entity_id, tenant_id, knowledge_base_id);
ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_object_kb FOREIGN KEY
  (object_entity_id, tenant_id, knowledge_base_id)
  REFERENCES entity_knowledge_base (entity_id, tenant_id, knowledge_base_id);

CREATE TABLE fact_slot_qualifier (
  slot_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  knowledge_base_id uuid NOT NULL,
  qualifier_name text NOT NULL,
  value_type text NOT NULL,
  canonical_value text NOT NULL,
  created_at timestamptz NOT NULL,
  CONSTRAINT pk_fact_slot_qualifier PRIMARY KEY (slot_id, qualifier_name),
  CONSTRAINT fk_fact_slot_qualifier_owner FOREIGN KEY (slot_id, tenant_id, knowledge_base_id)
    REFERENCES fact_slot (id, tenant_id, knowledge_base_id),
  CONSTRAINT ck_fact_slot_qualifier_type CHECK (value_type IN
    ('text','code','decimal','date','boolean','entity_ref','money','identifier')),
  CONSTRAINT ck_fact_slot_qualifier_name CHECK (qualifier_name ~ '^[a-z][a-z0-9_]{0,63}$'),
  CONSTRAINT ck_fact_slot_qualifier_value CHECK (length(canonical_value) > 0)
);

CREATE FUNCTION brain_forbid_slot_identity_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.entity_id IS DISTINCT FROM OLD.entity_id
     OR NEW.slot_type IS DISTINCT FROM OLD.slot_type
     OR NEW.identity_version IS DISTINCT FROM OLD.identity_version
     OR NEW.slot_role IS DISTINCT FROM OLD.slot_role
     OR NEW.predicate_key IS DISTINCT FROM OLD.predicate_key
     OR NEW.predicate_release_ref IS DISTINCT FROM OLD.predicate_release_ref
     OR NEW.cardinality IS DISTINCT FROM OLD.cardinality
     OR NEW.object_entity_id IS DISTINCT FROM OLD.object_entity_id
     OR NEW.parent_slot_id IS DISTINCT FROM OLD.parent_slot_id
     OR NEW.member_key IS DISTINCT FROM OLD.member_key
     OR NEW.fingerprint_version IS DISTINCT FROM OLD.fingerprint_version
     OR NEW.identity_fingerprint IS DISTINCT FROM OLD.identity_fingerprint
     OR NEW.created_by IS DISTINCT FROM OLD.created_by THEN
    RAISE EXCEPTION 'fact_slot identity is immutable' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_fact_slot_identity_immutable BEFORE UPDATE ON fact_slot
  FOR EACH ROW EXECUTE FUNCTION brain_forbid_slot_identity_change();

CREATE TRIGGER trg_fact_slot_qualifier_append_only BEFORE UPDATE OR DELETE ON fact_slot_qualifier
  FOR EACH ROW EXECUTE FUNCTION brain_append_only();
CREATE TRIGGER trg_fact_slot_qualifier_owner_immutable BEFORE UPDATE ON fact_slot_qualifier
  FOR EACH ROW EXECUTE FUNCTION brain_forbid_owner_change('tenant_id', 'knowledge_base_id');

CREATE FUNCTION brain_fact_slot_identity_integrity() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  parent fact_slot%ROWTYPE;
  target fact_slot%ROWTYPE;
BEGIN
  IF TG_TABLE_NAME = 'fact_slot' THEN
    IF NEW.slot_role = 'MEMBER' THEN
      SELECT * INTO parent FROM fact_slot WHERE id = NEW.parent_slot_id;
      IF NOT FOUND OR parent.identity_version IS DISTINCT FROM 1
         OR parent.slot_role IS DISTINCT FROM 'SLOT'
         OR parent.cardinality IS DISTINCT FROM 'MULTI'
         OR parent.entity_id IS DISTINCT FROM NEW.entity_id
         OR parent.predicate_key IS DISTINCT FROM NEW.predicate_key THEN
        RAISE EXCEPTION 'fact_slot member requires an identity-v1 MULTI header'
          USING ERRCODE = 'check_violation';
      END IF;
    END IF;
  ELSE
    SELECT * INTO target FROM fact_slot WHERE id = NEW.slot_id;
    IF NOT FOUND OR target.identity_version IS DISTINCT FROM 1
       OR target.slot_role IS DISTINCT FROM 'SLOT' THEN
      RAISE EXCEPTION 'fact_slot_qualifier requires an identity-v1 slot header'
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER trg_fact_slot_identity_integrity
  AFTER INSERT ON fact_slot DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION brain_fact_slot_identity_integrity();
CREATE CONSTRAINT TRIGGER trg_fact_slot_qualifier_integrity
  AFTER INSERT ON fact_slot_qualifier DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION brain_fact_slot_identity_integrity();
"""

DOWNGRADE = r"""
DROP TRIGGER trg_fact_slot_qualifier_integrity ON fact_slot_qualifier;
DROP TRIGGER trg_fact_slot_identity_integrity ON fact_slot;
DROP FUNCTION brain_fact_slot_identity_integrity();
DROP TRIGGER trg_fact_slot_qualifier_owner_immutable ON fact_slot_qualifier;
DROP TRIGGER trg_fact_slot_qualifier_append_only ON fact_slot_qualifier;
DROP TRIGGER trg_fact_slot_identity_immutable ON fact_slot;
DROP FUNCTION brain_forbid_slot_identity_change();
DROP TABLE fact_slot_qualifier;
ALTER TABLE fact_slot DROP CONSTRAINT fk_fact_slot_object_kb;
ALTER TABLE fact_slot DROP CONSTRAINT fk_fact_slot_subject_kb;
ALTER TABLE fact_slot DROP CONSTRAINT fk_fact_slot_parent_owner;
DROP INDEX ix_fact_slot_subject_predicate;
DROP INDEX ix_fact_slot_parent;
DROP INDEX uq_fact_slot_identity;
ALTER TABLE fact_slot DROP CONSTRAINT ck_fact_slot_identity;
ALTER TABLE fact_slot DROP CONSTRAINT fk_fact_slot_created_by;
ALTER TABLE fact_slot
  DROP COLUMN subject_kb_entity_id,
  DROP COLUMN created_by,
  DROP COLUMN identity_fingerprint,
  DROP COLUMN fingerprint_version,
  DROP COLUMN member_key,
  DROP COLUMN parent_slot_id,
  DROP COLUMN object_entity_id,
  DROP COLUMN cardinality,
  DROP COLUMN predicate_release_ref,
  DROP COLUMN predicate_key,
  DROP COLUMN slot_role,
  DROP COLUMN identity_version;
"""


def _preflight() -> None:
    bind = op.get_bind()
    owner_key = bind.execute(
        text(
            "SELECT count(*) FROM pg_constraint WHERE conname = 'uq_fact_slot_owner' "
            "AND conrelid = 'fact_slot'::regclass"
        )
    ).scalar_one()
    if owner_key != 1:
        raise RuntimeError(
            "0012 requires uq_fact_slot_owner (fact_slot id, tenant_id, kb) from 0005"
        )
    legacy = bind.execute(text("SELECT count(*) FROM fact_slot")).scalar_one()
    log.info("0012 preflight: uq_fact_slot_owner present; %s legacy fact_slot rows kept", legacy)


def upgrade() -> None:
    _preflight()
    op.execute(UPGRADE)


def downgrade() -> None:
    bind = op.get_bind()
    identity_rows = bind.execute(
        text("SELECT count(*) FROM fact_slot WHERE identity_version IS NOT NULL")
    ).scalar_one()
    qualifier_rows = bind.execute(text("SELECT count(*) FROM fact_slot_qualifier")).scalar_one()
    if identity_rows or qualifier_rows:
        raise RuntimeError(
            "0012 downgrade refused: identity-v1 fact_slot or fact_slot_qualifier rows exist "
            f"({identity_rows} slots, {qualifier_rows} qualifiers). F0007 never deletes "
            "evidence to make a downgrade pass."
        )
    op.execute(DOWNGRADE)
