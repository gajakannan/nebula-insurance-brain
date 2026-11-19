"""F0008 fact-temporal/v1 contract and close-only immutability (ADR-0078).

Additive. Existing versions are left byte-for-byte as they are and marked
legacy by `temporal_contract IS NULL`. Nothing is backfilled, defaulted or
repaired. The exclusion constraint DDL is unchanged.

- D1/D2/D7: a BEFORE INSERT trigger binds the contract to the slot's identity
  version, checks zones against `pg_timezone_names` and truncation with
  `date_trunc`, and backs the fact-answer/v1 envelope for identity-v1 slots.
- D5: closing an open recorded interval is the only permitted UPDATE. DELETE and
  TRUNCATE are refused, and `canonical_fact_change` is append-only.
- Preflight refuses the upgrade if an existing identity-v1 version fails the
  envelope predicate (the 0013 pattern), and repairs nothing.
- Downgrade refuses while any row uses a field the old schema cannot hold.

Revision ID: 0014
Revises: 0013
"""

import logging
from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None

log = logging.getLogger("alembic.runtime.migration")

TABLE = "canonical_fact_version"

COLUMNS = (
    ("temporal_contract", "smallint"),
    ("temporal_kind", "text"),
    ("valid_from_granularity", "text"),
    ("valid_from_zone", "text"),
    ("valid_from_basis", "text"),
    ("valid_to_state", "text"),
    ("valid_to_granularity", "text"),
    ("valid_to_zone", "text"),
    ("attested_from_value", "varchar(10)"),
    ("attested_from_precision", "text"),
    ("attested_through_value", "varchar(10)"),
    ("attested_through_precision", "text"),
    ("attested_to_value", "varchar(10)"),
    ("attested_to_precision", "text"),
    ("validity_unknown_from", "timestamptz"),
    ("split_of_version_id", "uuid"),
)

GRANULARITIES = "('YEAR','QUARTER','MONTH','DAY','HOUR','MINUTE','SECOND')"
PRECISIONS = "('YEAR','MONTH','DAY')"
DATE_VALUE = r"'^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$'"


def envelope(column: str) -> str:
    """The fact-answer/v1 envelope predicate (ADR-0078 D7, F0007 S0003 AC2)."""
    return (
        f"({column}->>'answer_contract' = 'fact-answer/v1' "
        f"AND (({column}->>'state') = 'PRESENT') = ({column} ? 'value'))"
    )


ENVELOPE = envelope("value")

V1_COLUMNS_NULL = " AND ".join(
    f"{name} IS NULL" for name, _ in COLUMNS if name != "split_of_version_id"
)

CHECKS = (
    ("ck_cfv_temporal_contract", "temporal_contract IS NULL OR temporal_contract = 1"),
    (
        "ck_cfv_temporal_kind",
        "temporal_kind IS NULL OR temporal_kind IN ('STATE','EVENT','ETERNAL')",
    ),
    (
        "ck_cfv_valid_from_granularity",
        f"valid_from_granularity IS NULL OR valid_from_granularity IN {GRANULARITIES}",
    ),
    (
        "ck_cfv_valid_to_granularity",
        f"valid_to_granularity IS NULL OR valid_to_granularity IN {GRANULARITIES}",
    ),
    (
        "ck_cfv_valid_from_basis",
        "valid_from_basis IS NULL OR valid_from_basis IN ('TEMPLATE_FIELD','HUMAN',"
        "'MENTION_A','MENTION_B','MENTION_C','ATTESTATION_FLOOR')",
    ),
    (
        "ck_cfv_valid_to_state",
        "valid_to_state IS NULL OR valid_to_state IN ('OPEN','BOUNDED','UNKNOWN')",
    ),
    *(
        (
            f"ck_cfv_{prefix}",
            f"({prefix}_value IS NULL) = ({prefix}_precision IS NULL) "
            f"AND ({prefix}_precision IS NULL OR ({prefix}_precision IN {PRECISIONS} "
            f"AND {prefix}_value ~ {DATE_VALUE} "
            f"AND length({prefix}_value) = CASE {prefix}_precision "
            "WHEN 'YEAR' THEN 4 WHEN 'MONTH' THEN 7 ELSE 10 END))",
        )
        for prefix in ("attested_from", "attested_through", "attested_to")
    ),
    (
        "ck_cfv_bound_pairs",
        "(valid_from_granularity IS NULL) = (valid_from_zone IS NULL) "
        "AND (valid_to_granularity IS NULL) = (valid_to_zone IS NULL)",
    ),
    (
        "ck_cfv_v1_shape",
        f"(temporal_contract IS NULL AND {V1_COLUMNS_NULL}) "
        "OR (temporal_contract = 1 AND temporal_kind IS NOT NULL AND valid_to_state IS NOT NULL)",
    ),
    (
        # A start is never widened to minus infinity; only ETERNAL has no start.
        "ck_cfv_v1_start",
        "temporal_contract IS NULL OR temporal_kind = 'ETERNAL' "
        "OR (NOT lower_inf(valid) AND valid_from_granularity IS NOT NULL "
        "AND valid_from_zone IS NOT NULL AND valid_from_basis IS NOT NULL)",
    ),
    (
        "ck_cfv_v1_end",
        "temporal_contract IS NULL OR temporal_kind = 'ETERNAL' "
        "OR (valid_to_state = 'OPEN' AND upper_inf(valid) AND valid_to_granularity IS NULL "
        "AND validity_unknown_from IS NULL) "
        "OR (valid_to_state = 'BOUNDED' AND NOT upper_inf(valid) "
        "AND valid_to_granularity IS NOT NULL AND attested_to_value IS NULL "
        "AND validity_unknown_from IS NULL) "
        "OR (valid_to_state = 'UNKNOWN' AND NOT upper_inf(valid) "
        "AND valid_to_granularity IS NOT NULL AND attested_to_value IS NOT NULL "
        "AND validity_unknown_from IS NOT NULL AND validity_unknown_from < upper(valid))",
    ),
    (
        # D10: EVENT is one BOUNDED granularity period (the length is checked in the
        # insert trigger); ETERNAL has valid (,) and no bound columns.
        "ck_cfv_v1_kind_shape",
        "temporal_contract IS NULL "
        "OR (temporal_kind = 'STATE') "
        "OR (temporal_kind = 'EVENT' AND valid_to_state = 'BOUNDED' "
        "AND valid_from_granularity = valid_to_granularity) "
        "OR (temporal_kind = 'ETERNAL' AND lower_inf(valid) AND upper_inf(valid) "
        "AND valid_to_state = 'OPEN' AND valid_from_granularity IS NULL "
        "AND valid_from_basis IS NULL AND valid_to_granularity IS NULL)",
    ),
    (
        "ck_cfv_v1_floor",
        "valid_from_basis IS DISTINCT FROM 'ATTESTATION_FLOOR' OR attested_from_value IS NOT NULL",
    ),
    ("ck_cfv_v1_envelope", f"temporal_contract IS NULL OR {ENVELOPE}"),
)

INSERT_GUARD = rf"""
CREATE FUNCTION brain_cfv_v1_insert_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
DECLARE
    slot_identity smallint;
    predecessor_contract smallint;
    predecessor_found boolean;
BEGIN
    SELECT s.identity_version INTO slot_identity FROM public.fact_slot s WHERE s.id = NEW.slot_id;
    IF slot_identity IS NULL THEN
        IF NEW.temporal_contract IS NOT NULL OR NEW.split_of_version_id IS NOT NULL THEN
            RAISE EXCEPTION 'canonical_fact_version: a legacy slot takes legacy versions only'
                USING ERRCODE = 'check_violation';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.temporal_contract IS NULL THEN
        -- D1: the only legacy row an identity-v1 slot accepts is the split
        -- remainder of a legacy predecessor.
        SELECT true, v.temporal_contract INTO predecessor_found, predecessor_contract
          FROM public.canonical_fact_version v WHERE v.id = NEW.split_of_version_id;
        IF NEW.split_of_version_id IS NULL OR predecessor_found IS NOT TRUE
           OR predecessor_contract IS NOT NULL THEN
            RAISE EXCEPTION 'canonical_fact_version: an identity-v1 slot requires fact-temporal/v1'
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    -- D7: the envelope backstop applies to every row of an identity-v1 slot.
    IF ({envelope("NEW.value")}) IS NOT TRUE THEN
        RAISE EXCEPTION 'canonical_fact_version: fact-answer/v1 state and value disagree'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.temporal_contract = 1 THEN
        IF NEW.valid_from_zone IS NOT NULL AND NOT EXISTS (
               SELECT 1 FROM pg_catalog.pg_timezone_names z WHERE z.name = NEW.valid_from_zone)
           OR NEW.valid_to_zone IS NOT NULL AND NOT EXISTS (
               SELECT 1 FROM pg_catalog.pg_timezone_names z WHERE z.name = NEW.valid_to_zone) THEN
            RAISE EXCEPTION 'canonical_fact_version: unknown time zone'
                USING ERRCODE = 'check_violation';
        END IF;
        -- D2: each finite bound is truncated to its granularity in its zone.
        IF NEW.valid_from_granularity IS NOT NULL AND NOT lower_inf(NEW.valid)
           AND date_trunc(lower(NEW.valid_from_granularity), lower(NEW.valid), NEW.valid_from_zone)
               <> lower(NEW.valid) THEN
            RAISE EXCEPTION 'canonical_fact_version: valid start is not truncated'
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.valid_to_granularity IS NOT NULL AND NOT upper_inf(NEW.valid)
           AND date_trunc(lower(NEW.valid_to_granularity), upper(NEW.valid), NEW.valid_to_zone)
               <> upper(NEW.valid) THEN
            RAISE EXCEPTION 'canonical_fact_version: valid end is not truncated'
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.temporal_kind = 'EVENT' AND upper(NEW.valid) <> (
               (date_trunc(lower(NEW.valid_from_granularity), lower(NEW.valid), NEW.valid_from_zone)
                AT TIME ZONE NEW.valid_from_zone)
               + CASE NEW.valid_from_granularity WHEN 'QUARTER' THEN interval '3 months'
                 ELSE ('1 ' || lower(NEW.valid_from_granularity))::interval END
           ) AT TIME ZONE NEW.valid_from_zone THEN
            RAISE EXCEPTION 'canonical_fact_version: an EVENT spans one granularity period'
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END
$$
"""

CLOSE_ONLY = """
CREATE FUNCTION brain_cfv_close_only() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
BEGIN
    -- D5: the only permitted change sets the finite upper bound of a recorded
    -- interval that is still open. Every other column must be unchanged.
    IF upper_inf(OLD.recorded) AND NOT upper_inf(NEW.recorded)
       AND NOT lower_inf(NEW.recorded)
       AND lower(NEW.recorded) = lower(OLD.recorded)
       AND lower_inc(NEW.recorded) = lower_inc(OLD.recorded)
       AND upper(NEW.recorded) > lower(OLD.recorded)
       AND (to_jsonb(NEW) - 'recorded') = (to_jsonb(OLD) - 'recorded') THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'canonical_fact_version is close-only' USING ERRCODE = 'restrict_violation';
END
$$
"""

REFUSE = """
CREATE FUNCTION brain_refuse_mutation() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, public AS $$
BEGIN
    RAISE EXCEPTION '% is immutable (% rejected)', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'restrict_violation';
END
$$
"""

# WHY names: BEFORE triggers fire in name order, so `..._owner_immutable` (0007)
# still fires before these and existing ownership negatives keep their error.
TRIGGERS = (
    (
        "trg_canonical_fact_version_v1_insert",
        TABLE,
        "BEFORE INSERT ON canonical_fact_version FOR EACH ROW "
        "EXECUTE FUNCTION brain_cfv_v1_insert_guard()",
    ),
    (
        "trg_canonical_fact_version_v1_close_only",
        TABLE,
        "BEFORE UPDATE ON canonical_fact_version FOR EACH ROW "
        "EXECUTE FUNCTION brain_cfv_close_only()",
    ),
    (
        "trg_canonical_fact_version_v1_no_delete",
        TABLE,
        "BEFORE DELETE ON canonical_fact_version FOR EACH ROW "
        "EXECUTE FUNCTION brain_refuse_mutation()",
    ),
    (
        "trg_canonical_fact_version_v1_no_truncate",
        TABLE,
        "BEFORE TRUNCATE ON canonical_fact_version FOR EACH STATEMENT "
        "EXECUTE FUNCTION brain_refuse_mutation()",
    ),
    (
        "trg_canonical_fact_change_v1_append_only",
        "canonical_fact_change",
        "BEFORE UPDATE OR DELETE ON canonical_fact_change FOR EACH ROW "
        "EXECUTE FUNCTION brain_refuse_mutation()",
    ),
    (
        "trg_canonical_fact_change_v1_no_truncate",
        "canonical_fact_change",
        "BEFORE TRUNCATE ON canonical_fact_change FOR EACH STATEMENT "
        "EXECUTE FUNCTION brain_refuse_mutation()",
    ),
)

SPLIT_FK = "fk_canonical_fact_version_split_of_owner"
NEXT_INDEX = "ix_canonical_fact_version_v1_slot_lower"


def _preflight(bind) -> None:  # type: ignore[no-untyped-def]
    # WHY: hold the lock from the scan through the new constraints so no writer can
    # add a violating row in between.
    bind.execute(text(f"LOCK TABLE {TABLE} IN SHARE ROW EXCLUSIVE MODE"))
    invalid = (
        f"FROM {TABLE} v JOIN fact_slot s ON s.id = v.slot_id "
        "WHERE s.identity_version IS NOT NULL "
        f"AND ({envelope('v.value')}) IS NOT TRUE"
    )
    count = bind.execute(text(f"SELECT count(*) {invalid}")).scalar_one()
    if count:
        sample = ", ".join(
            str(i)
            for i in bind.execute(text(f"SELECT v.id {invalid} ORDER BY v.id LIMIT 10")).scalars()
        )
        raise RuntimeError(
            f"0014 upgrade refused: {count} identity-v1 versions fail the fact-answer/v1 "
            f"envelope; sample version IDs: {sample}. No rows modified; governed repair required."
        )


def upgrade() -> None:
    bind = op.get_bind()
    _preflight(bind)
    op.execute(
        f"ALTER TABLE {TABLE} "
        + ", ".join(f"ADD COLUMN {name} {kind} NULL" for name, kind in COLUMNS)
    )
    for name, expression in CHECKS:
        op.execute(f"ALTER TABLE {TABLE} ADD CONSTRAINT {name} CHECK ({expression})")
    op.execute(
        f"ALTER TABLE {TABLE} ADD CONSTRAINT {SPLIT_FK} "
        "FOREIGN KEY (split_of_version_id, tenant_id, knowledge_base_id) "
        f"REFERENCES {TABLE} (id, tenant_id, knowledge_base_id)"
    )
    op.execute(
        f"CREATE INDEX {NEXT_INDEX} ON {TABLE} (slot_id, lower(valid)) WHERE temporal_contract = 1"
    )
    op.execute(INSERT_GUARD)
    op.execute(CLOSE_ONLY)
    op.execute(REFUSE)
    for name, _table, definition in TRIGGERS:
        op.execute(f"CREATE TRIGGER {name} {definition}")
    legacy = bind.execute(text(f"SELECT count(*) FROM {TABLE}")).scalar_one()
    log.info("0014 fact-temporal/v1 contract installed; %s existing versions kept legacy", legacy)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text(f"LOCK TABLE {TABLE} IN SHARE ROW EXCLUSIVE MODE"))
    blocking = (
        f"FROM {TABLE} WHERE temporal_contract IS NOT NULL OR split_of_version_id IS NOT NULL"
    )
    count = bind.execute(text(f"SELECT count(*) {blocking}")).scalar_one()
    if count:
        sample = ", ".join(
            str(i)
            for i in bind.execute(text(f"SELECT id {blocking} ORDER BY id LIMIT 10")).scalars()
        )
        raise RuntimeError(
            f"0014 downgrade refused: {count} versions use fact-temporal/v1 fields the 0013 "
            f"schema cannot hold; blocking version IDs: {sample}. Roll forward instead."
        )
    for name, table, _definition in reversed(TRIGGERS):
        op.execute(f"DROP TRIGGER {name} ON {table}")
    op.execute("DROP FUNCTION brain_refuse_mutation()")
    op.execute("DROP FUNCTION brain_cfv_close_only()")
    op.execute("DROP FUNCTION brain_cfv_v1_insert_guard()")
    op.execute(f"DROP INDEX {NEXT_INDEX}")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT {SPLIT_FK}")
    for name, _expression in reversed(CHECKS):
        op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT {name}")
    op.execute(
        f"ALTER TABLE {TABLE} "
        + ", ".join(f"DROP COLUMN {name}" for name, _kind in reversed(COLUMNS))
    )
    log.info("0014 downgraded; legacy pilot behaviour restored, no row rewritten")
