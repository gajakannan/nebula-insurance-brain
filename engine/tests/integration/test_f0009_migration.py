"""F0009 migration 0016 on an owned PostgreSQL database (S0006 AC1/AC2, S0005
AC1/AC4, S0002 AC6). Direct SQL challenges every database guard, including under
the elevated application role that F0018 will later restrict."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
import pytest
from alembic import command
from brain_testing import fixtures
from engine.tests.fixtures.assertions import harness
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
configuration = harness.configuration

LEGACY_TABLES = (
    "assertion",
    "assertion_evidence",
    "review_item",
    "review_batch",
    "review_decision",
    "canonical_fact_version",
    "canonical_fact_change",
    "audit_event",
    "resource_access",
)


class Legacy:
    """Pre-F0009 rows seeded at revision 0015 (raw SQL: the 0015 schema has no marker)."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.tenant, self.kb = uuid4(), uuid4()
        engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
        with Session(engine) as session, session.begin():
            fixtures.seed_scope(session, self.tenant, self.kb)
            self.reviewer = fixtures.seed_principal(
                session, issuer="urn:f0009:migration", subject=str(uuid4())
            ).id
            self.item, self.batch = fixtures.seed_review_item(
                session, self.tenant, self.kb, assembling_principal_id=self.reviewer
            )
        engine.dispose()
        ((self.original,),) = self.rows(
            "SELECT assertion_id FROM review_item WHERE id=%s", self.item
        )
        self.child = self.human_child(self.original)
        self.decision = uuid4()
        self.sql(
            "INSERT INTO review_decision (id, review_item_id, review_batch_id, action, "
            "reason_code, corrected_value, corrected_assertion_id, reviewer_principal_id, "
            "assertion_version, stale, event_sha256, tenant_id, knowledge_base_id, decided_at) "
            "VALUES "
            "(%s, %s, %s, 'CORRECT', 'MISREAD_VALUE', '{\"amount\": 2}'::jsonb, %s, %s, 1, false, "
            "%s, %s, %s, '2026-09-01 12:00:00')",
            self.decision,
            self.item,
            self.batch,
            self.child,
            self.reviewer,
            "a" * 64,
            self.tenant,
            self.kb,
        )

    def sql(self, statement: str, *params: object) -> None:
        with psycopg.connect(self.url) as connection:
            connection.execute(statement, params)

    def rows(self, statement: str, *params: object) -> list[tuple]:
        with psycopg.connect(self.url) as connection:
            return connection.execute(statement, params).fetchall()

    def human_child(self, original: UUID, connection: psycopg.Connection | None = None) -> UUID:
        child = uuid4()
        statement = (
            "INSERT INTO assertion (id, origin, original_assertion_id, version, subject_type, "
            "slot_type, value, interpretation_basis, tenant_id, knowledge_base_id, "
            "semantic_contract_version) VALUES (%s, 'HUMAN_REVIEW', %s, 1, 'Policy', "
            "'each_occurrence_limit', '{\"amount\": 2}'::jsonb, 'EXPLICIT', %s, %s, 1)"
        )
        params = (child, original, self.tenant, self.kb)
        if connection is None:
            self.sql(statement, *params)
        else:
            connection.execute(statement, params)
        return child

    def digest(self) -> dict[str, str]:
        """Byte-level digests; the one documented new nullable column is excluded."""
        result = {}
        with psycopg.connect(self.url) as connection:
            for table in LEGACY_TABLES:
                rows = connection.execute(
                    f"SELECT (to_jsonb(t) - 'correction_lineage_contract')::text FROM {table} t "
                    "ORDER BY 1"
                ).fetchall()
                result[table] = hashlib.sha256("\n".join(r[0] for r in rows).encode()).hexdigest()
        return result


@pytest.fixture
def legacy(database):  # type: ignore[no-untyped-def]
    command.upgrade(configuration(), "0015")
    world = Legacy(database)
    before = world.digest()
    command.upgrade(configuration(), "0016")
    world.before = before
    return world


def new_correction(legacy: Legacy, connection: psycopg.Connection, *, reserve: bool, **override):
    """A fresh CORRECT decision on a new item with its child, in one transaction."""
    engine = create_engine(legacy.url.replace("postgresql://", "postgresql+psycopg://"))
    with Session(engine) as session, session.begin():
        item, batch = fixtures.seed_review_item(
            session, legacy.tenant, legacy.kb, assembling_principal_id=legacy.reviewer
        )
    engine.dispose()
    ((original,),) = connection.execute(
        "SELECT assertion_id FROM review_item WHERE id=%s", (item,)
    ).fetchall()
    child = legacy.human_child(original, connection)
    decision = uuid4()
    decided = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    connection.execute(
        "INSERT INTO review_decision (id, review_item_id, review_batch_id, action, reason_code, "
        "corrected_value, corrected_assertion_id, reviewer_principal_id, assertion_version, "
        "stale, event_sha256, tenant_id, knowledge_base_id, decided_at, "
        "correction_lineage_contract) VALUES (%s, %s, %s, 'CORRECT', 'MISREAD_VALUE', "
        "'{}'::jsonb, %s, %s, 1, false, %s, %s, %s, %s, NULL)",
        (
            decision,
            item,
            batch,
            child,
            legacy.reviewer,
            "b" * 64,
            legacy.tenant,
            legacy.kb,
            decided.replace(tzinfo=None),
        ),
    )
    values = {
        "id": uuid4(),
        "tenant_id": legacy.tenant,
        "knowledge_base_id": legacy.kb,
        "review_decision_id": decision,
        "original_assertion_id": original,
        "corrected_assertion_id": child,
        "reviewer_principal_id": legacy.reviewer,
        "reserved_at": decided,
    }
    values.update(override)
    if reserve:
        connection.execute(
            "INSERT INTO learning_candidate_reservation (id, tenant_id, knowledge_base_id, "
            "review_decision_id, original_assertion_id, corrected_assertion_id, "
            "reviewer_principal_id, reserved_at) VALUES (%(id)s, %(tenant_id)s, "
            "%(knowledge_base_id)s, %(review_decision_id)s, %(original_assertion_id)s, "
            "%(corrected_assertion_id)s, %(reviewer_principal_id)s, %(reserved_at)s)",
            values,
        )
    return item, batch, original, decision, values


def test_upgrade_preserves_legacy_rows_and_fabricates_nothing(legacy):
    """S0006 AC1, S0005 AC4: byte-identical history, NULL marker, no backfill."""
    assert legacy.digest() == legacy.before
    assert legacy.rows("SELECT correction_lineage_contract FROM review_decision") == [(None,)]
    for table in ("learning_candidate_reservation", "review_submission_attempt"):
        assert legacy.rows(f"SELECT count(*) FROM {table}") == [(0,)]


def test_historical_decision_cannot_acquire_a_reservation(legacy):
    with pytest.raises(psycopg.errors.CheckViolation):
        legacy.sql(
            "INSERT INTO learning_candidate_reservation (id, tenant_id, knowledge_base_id, "
            "review_decision_id, original_assertion_id, corrected_assertion_id, "
            "reviewer_principal_id, reserved_at) VALUES (%s, %s, %s, %s, %s, %s, %s, "
            "'2026-09-01 12:00:00+00')",
            uuid4(),
            legacy.tenant,
            legacy.kb,
            legacy.decision,
            legacy.original,
            legacy.child,
            legacy.reviewer,
        )


def test_marker_is_server_owned_and_a_correction_requires_its_reservation(legacy):
    """The marker overrides a submitted NULL; the deferred trigger refuses a new
    effective correction without its reservation at commit."""
    with psycopg.connect(legacy.url) as connection:
        _item, _batch, _orig, decision, _ = new_correction(legacy, connection, reserve=True)
    assert legacy.rows(
        "SELECT correction_lineage_contract FROM review_decision WHERE id=%s", decision
    ) == [(1,)]
    with (
        pytest.raises(psycopg.errors.CheckViolation, match="requires its learning reservation"),
        psycopg.connect(legacy.url) as connection,
    ):
        new_correction(legacy, connection, reserve=False)


@pytest.mark.parametrize(
    "override",
    [
        {"reviewer_principal_id": "other"},
        {"reserved_at": datetime(2026, 11, 24, 12, 0, 1, tzinfo=UTC)},
        {"original_assertion_id": "legacy"},
    ],
)
def test_reservation_guard_rejects_unrelated_links(legacy, override):
    if override.get("reviewer_principal_id") == "other":
        engine = create_engine(legacy.url.replace("postgresql://", "postgresql+psycopg://"))
        with Session(engine) as session, session.begin():
            override = {
                "reviewer_principal_id": fixtures.seed_principal(
                    session, issuer="urn:f0009:migration", subject=str(uuid4())
                ).id
            }
        engine.dispose()
    if override.get("original_assertion_id") == "legacy":
        override = {"original_assertion_id": legacy.original}
    with pytest.raises(psycopg.errors.CheckViolation), psycopg.connect(legacy.url) as connection:
        new_correction(legacy, connection, reserve=True, **override)


def test_reservation_owner_must_match(legacy):
    # The guard (BEFORE INSERT) or the composite owner FK refuses; both are refusals.
    with (
        pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation)),
        psycopg.connect(legacy.url) as connection,
    ):
        new_correction(legacy, connection, reserve=True, knowledge_base_id=uuid4())


def test_lineage_rows_and_decisions_are_append_only(legacy):
    with psycopg.connect(legacy.url) as connection:
        _item, _batch, _orig, decision, values = new_correction(legacy, connection, reserve=True)
    statements = [
        ("UPDATE learning_candidate_reservation SET reserved_at = now() WHERE id=%s", values["id"]),
        ("DELETE FROM learning_candidate_reservation WHERE id=%s", values["id"]),
        ("TRUNCATE learning_candidate_reservation", None),
        ("UPDATE review_decision SET reviewer_comment='x' WHERE id=%s", decision),
        ("DELETE FROM review_decision WHERE id=%s", legacy.decision),
        ("TRUNCATE review_decision CASCADE", None),
        ("TRUNCATE review_submission_attempt", None),
    ]
    for statement, param in statements:
        with pytest.raises(psycopg.errors.CheckViolation):
            legacy.sql(statement, *(() if param is None else (param,)))
    assert legacy.rows("SELECT count(*) FROM learning_candidate_reservation") == [(1,)]


def _attempt(legacy: Legacy, authorization: UUID, **override) -> None:
    values = {
        "id": uuid4(),
        "tenant": legacy.tenant,
        "kb": legacy.kb,
        "item": legacy.item,
        "batch": legacy.batch,
        "original": legacy.original,
        "reviewer": legacy.reviewer,
        "auth": authorization,
    }
    values.update(override)
    with psycopg.connect(legacy.url) as connection:
        connection.execute(
            "INSERT INTO review_submission_attempt (id, tenant_id, knowledge_base_id, "
            "review_item_id, review_batch_id, original_assertion_id, reviewer_principal_id, "
            "submitted_at, event_sha256, assertion_version, action, outcome, "
            "authorization_decision_id) VALUES (%(id)s, %(tenant)s, %(kb)s, %(item)s, %(batch)s, "
            "%(original)s, %(reviewer)s, now(), repeat('c', 64), 1, 'CORRECT', 'ALREADY_DECIDED', "
            "%(auth)s)",
            values,
        )


def test_attempt_requires_the_reviewers_matching_annotate_authorization(legacy):
    with pytest.raises(psycopg.errors.CheckViolation):
        _attempt(legacy, uuid4())  # no staged authorization decision
    authorization = uuid4()
    legacy.sql(
        "INSERT INTO audit_event (id, actor_principal_id, resource_type, resource_id, action, "
        "decision, reason_code, policy_hash, grant_revision, trace_id, decision_id, event_type, "
        "operation_outcome) VALUES (%s, %s, 'review_task', %s, 'annotate', true, 'ALLOWED', "
        "'h', 1, 't', %s, 'authorization_decision', 'succeeded')",
        uuid4(),
        legacy.reviewer,
        legacy.item,
        authorization,
    )
    with pytest.raises(psycopg.errors.CheckViolation):
        _attempt(legacy, authorization, original=legacy.child)  # wrong original
    _attempt(legacy, authorization)
    assert legacy.rows("SELECT count(*) FROM review_submission_attempt") == [(1,)]
    for statement in (
        "UPDATE review_submission_attempt SET outcome='BATCH_REFUSED'",
        "DELETE FROM review_submission_attempt",
    ):
        with pytest.raises(psycopg.errors.CheckViolation):
            legacy.sql(statement)
    with pytest.raises(psycopg.errors.UniqueViolation):
        _attempt(legacy, authorization)  # one row per (item, event, outcome)


def test_downgrade_round_trip_when_empty_and_refusal_when_populated(legacy):
    """S0006 AC2: empty down/up keeps legacy bytes; populated downgrade refuses
    before any destructive effect."""
    command.downgrade(configuration(), "0015")
    assert legacy.digest() == legacy.before
    command.upgrade(configuration(), "0016")
    assert legacy.digest() == legacy.before
    with psycopg.connect(legacy.url) as connection:
        new_correction(legacy, connection, reserve=True)
    with pytest.raises(RuntimeError, match="0016 downgrade refused"):
        command.downgrade(configuration(), "0015")
    assert legacy.rows("SELECT count(*) FROM learning_candidate_reservation") == [(1,)]
    assert legacy.rows("SELECT version_num FROM alembic_version") == [("0016",)]
