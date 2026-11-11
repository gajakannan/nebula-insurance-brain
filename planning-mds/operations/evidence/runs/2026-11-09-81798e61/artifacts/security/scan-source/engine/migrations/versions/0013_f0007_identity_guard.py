"""Require a complete legacy/v1 FactSlot identity shape (F0007 review FR-H2).

Revision 0012 is already shipped and stays unchanged. Its CHECK allowed SQL
UNKNOWN for incomplete v1 rows. This follow-up admits only TRUE, refuses any
existing malformed rows without repairing them, and preserves all data on both
upgrade and downgrade. No RLS, grants, ownership keys or version rows change.

Revision ID: 0013
Revises: 0012
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

# WHY: migration history is immutable. The old expression is frozen here so a
# downgrade restores exactly 0012's semantics without importing mutable code.
PREVIOUS_CHECK = r"""
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
            AND length(member_key) > 0 AND object_entity_id IS NULL)))
"""

IDENTITY_SHAPE = r"""
  (identity_version IS NULL AND slot_role IS NULL AND predicate_key IS NULL
     AND predicate_release_ref IS NULL AND cardinality IS NULL AND object_entity_id IS NULL
     AND parent_slot_id IS NULL AND member_key IS NULL AND fingerprint_version IS NULL
     AND identity_fingerprint IS NULL AND created_by IS NULL)
  OR (identity_version IS NOT NULL AND identity_version = 1
     AND fingerprint_version IS NOT NULL AND fingerprint_version = 1
     AND created_by IS NOT NULL AND slot_role IS NOT NULL
     AND identity_fingerprint IS NOT NULL AND identity_fingerprint ~ '^[0-9a-f]{64}$'
     AND predicate_key IS NOT NULL
     AND predicate_key ~ '^[a-z][a-z0-9-]{0,31}:[A-Za-z][A-Za-z0-9]{0,63}@v[1-9][0-9]{0,3}$'
     AND predicate_release_ref IS NOT NULL AND length(predicate_release_ref) > 0
     AND slot_type = predicate_key AND cardinality IS NOT NULL
     AND cardinality IN ('SINGLE','MULTI','RELATIONSHIP')
     AND ((slot_role = 'SLOT' AND parent_slot_id IS NULL AND member_key IS NULL
            AND ((cardinality = 'RELATIONSHIP') = (object_entity_id IS NOT NULL)))
       OR (slot_role = 'MEMBER' AND cardinality = 'MULTI' AND parent_slot_id IS NOT NULL
            AND member_key IS NOT NULL AND length(member_key) > 0 AND object_entity_id IS NULL)))
"""


def upgrade() -> None:
    bind = op.get_bind()
    # WHY: hold the same lock through validation and replacement so another
    # writer cannot insert an invalid shape between the scan and the new CHECK.
    bind.execute(text("LOCK TABLE fact_slot IN ACCESS EXCLUSIVE MODE"))
    invalid = f"({IDENTITY_SHAPE}) IS NOT TRUE"
    malformed = bind.execute(text(f"SELECT count(*) FROM fact_slot WHERE {invalid}")).scalar_one()
    if malformed:
        identifiers = bind.execute(
            text(f"SELECT id FROM fact_slot WHERE {invalid} ORDER BY id LIMIT 10")
        ).scalars()
        samples = ", ".join(str(slot_id) for slot_id in identifiers)
        raise RuntimeError(
            f"0013 upgrade refused: {malformed} malformed fact_slot identity rows; "
            f"sample slot IDs: {samples}. No rows modified; explicit governed repair required."
        )
    op.execute("ALTER TABLE fact_slot DROP CONSTRAINT ck_fact_slot_identity")
    op.execute(
        f"ALTER TABLE fact_slot ADD CONSTRAINT ck_fact_slot_identity "
        f"CHECK (({IDENTITY_SHAPE}) IS TRUE)"
    )
    log.info("0013 identity guard installed; existing FactSlot rows preserved")


def downgrade() -> None:
    op.execute("ALTER TABLE fact_slot DROP CONSTRAINT ck_fact_slot_identity")
    op.execute(
        f"ALTER TABLE fact_slot ADD CONSTRAINT ck_fact_slot_identity CHECK ({PREVIOUS_CHECK})"
    )
