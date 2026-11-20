"""F0008 review remediation: split lineage stays within one slot (FR-ARCH-L2).

Revision 0014 checks that a split remainder's predecessor exists, and its
composite self-FK pins tenant and knowledge base, but nothing tied the
predecessor to the same slot. The commit service never writes a cross-slot
split; this adds the database guard so a direct insert cannot either, which
F0009 lineage depends on.

Additive: one SECURITY INVOKER function and one BEFORE INSERT trigger. The
preflight refuses the upgrade if an existing row already crosses slots, and
repairs nothing. Downgrade drops only what this revision adds.

Revision ID: 0015
Revises: 0014
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

TABLE = "canonical_fact_version"
TRIGGER = "trg_canonical_fact_version_v1_split_slot"
FUNCTION = "brain_cfv_split_same_slot"

GUARD = f"""
CREATE FUNCTION {FUNCTION}() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
BEGIN
    IF NEW.split_of_version_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.canonical_fact_version p
         WHERE p.id = NEW.split_of_version_id AND p.slot_id = NEW.slot_id) THEN
        RAISE EXCEPTION 'canonical_fact_version: split lineage crosses slots'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$$
"""

CROSSING = (
    f"FROM {TABLE} v JOIN {TABLE} p ON p.id = v.split_of_version_id WHERE p.slot_id <> v.slot_id"
)


def upgrade() -> None:
    bind = op.get_bind()
    # WHY: hold the lock from the scan through the new trigger.
    bind.execute(text(f"LOCK TABLE {TABLE} IN SHARE ROW EXCLUSIVE MODE"))
    count = bind.execute(text(f"SELECT count(*) {CROSSING}")).scalar_one()
    if count:
        sample = ", ".join(
            str(i)
            for i in bind.execute(text(f"SELECT v.id {CROSSING} ORDER BY v.id LIMIT 10")).scalars()
        )
        raise RuntimeError(
            f"0015 upgrade refused: {count} versions name a split predecessor in another slot; "
            f"sample version IDs: {sample}. No rows modified; governed repair required."
        )
    op.execute(GUARD)
    # Named after 0014's insert guard so it fires after it (BEFORE triggers run by name).
    op.execute(
        f"CREATE TRIGGER {TRIGGER} BEFORE INSERT ON {TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION {FUNCTION}()"
    )
    log.info("0015 split-lineage same-slot guard installed")


def downgrade() -> None:
    op.execute(f"DROP TRIGGER {TRIGGER} ON {TABLE}")
    op.execute(f"DROP FUNCTION {FUNCTION}()")
