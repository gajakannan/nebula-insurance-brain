"""F0008-S0006 two-coordinate reads through `GET /facts/{id}` (ADR-0078 D9),
the EX-SEM-004/EX-PC-014 A-D worked examples, half-open bounds, current-grant
authorization and attestation-date disclosure (D4). Every test owns its database."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from brain_persistence.grants import revoke_membership
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_temporal.reader import NotProcessed, Resolved, TemporalFactReader, ValidityUnknown
from brain_testing import fixtures
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import CHICAGO, bound, money
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_clean_fact_tables = h._clean_fact_tables
database = h.database
world = h.world

NOW = "2031-01-01T00:00:00Z"


def amount(response) -> str:  # type: ignore[no-untyped-def]
    assert response.status_code == 200, response.text
    return response.json()["value"]["value"]["amount"]


async def _section_87(w):  # type: ignore[no-untyped-def]
    slot = await w.slot()
    await w.commit_at(
        slot,
        w.body(
            money("2000000"), start=bound("2026-01-01T06:00:00Z"), received="2026-01-08T00:00:00Z"
        ),
        "2026-01-10T16:00:00Z",
    )
    await w.commit_at(
        slot,
        w.body(
            money("5000000"), start=bound("2026-06-01T05:00:00Z"), received="2026-06-12T14:00:00Z"
        ),
        "2026-06-14T15:00:00Z",
    )
    return slot


async def test_s0006_ac1_section_87_grid(world):
    w = world
    slot = await _section_87(w)
    assert amount(await w.read(slot, "2026-05-15T12:00:00Z", NOW)) == "2000000"
    assert amount(await w.read(slot, "2026-07-01T12:00:00Z", NOW)) == "5000000"
    assert amount(await w.read(slot, "2026-06-05T12:00:00Z", "2026-06-05T12:00:00Z")) == "2000000"
    assert amount(await w.read(slot, "2026-06-05T12:00:00Z", "2026-06-15T00:00:00Z")) == "5000000"


async def test_s0006_ac2_at_most_one_version_and_not_processed_internally(world):
    w = world
    slot = await _section_87(w)
    checked = 0
    for valid in ("2025-12-31T00:00:00Z", "2026-03-01T00:00:00Z", "2026-06-01T05:00:00Z"):
        for known in ("2026-01-09T00:00:00Z", "2026-01-10T16:00:00Z", "2026-06-14T15:00:00Z", NOW):
            n = w.scalar(
                "SELECT count(*) FROM canonical_fact_version WHERE slot_id = %s "
                "AND valid @> %s::timestamptz AND recorded @> %s::timestamptz",
                slot,
                valid,
                known,
            )
            assert n <= 1
            checked += 1
    assert checked == 12
    # Before any recorded version the internal reader says NOT_PROCESSED; the GET
    # keeps the pilot 404 (HTTP states stay with F0020).
    async with AsyncSession(w.engine) as session:
        reader = TemporalFactReader(SqlAlchemyFactCommitRepository(session))
        result = await reader.resolve(
            slot, valid_at=h.at("2026-03-01T00:00:00Z"), known_at=h.at("2026-01-09T00:00:00Z")
        )
    assert isinstance(result, NotProcessed)
    response = await w.read(slot, "2026-03-01T00:00:00Z", "2026-01-09T00:00:00Z")
    assert response.status_code == 404


async def test_s0006_ac3_ex_sem_004_window_never_returns_the_predecessor(world):
    w = world
    slot = await w.slot()
    positive, note = w.evidence(("2026-06-01", "DAY")), w.evidence(("2026-08-02", "DAY"))
    await w.commit_at(
        slot,
        w.body(money("1000000"), start=bound("2026-01-01T06:00:00Z"), evidence=[positive]),
        "2026-06-05T00:00:00Z",
    )
    await w.commit_at(
        slot,
        w.body(
            money("1000000"),
            start=bound("2026-01-01T06:00:00Z"),
            evidence=[positive],
            end_state="UNKNOWN",
            attestation_zone=CHICAGO,
            ending=[note],
        ),
        "2026-08-05T00:00:00Z",
    )
    window = await w.read(slot, "2026-07-15T12:00:00Z", NOW)
    assert window.json()["reason"] == "UNKNOWN_END_WINDOW" and "value" not in window.json()
    # Known before the ending note, July 15 still read as the open carrier.
    assert amount(await w.read(slot, "2026-07-15T12:00:00Z", "2026-07-01T00:00:00Z")) == "1000000"
    # After the integrity end, nothing: the pilot 404.
    assert (await w.read(slot, "2026-09-01T12:00:00Z", NOW)).status_code == 404


async def test_ex_pc_014_a_to_d_unknown_start_and_unknown_end(world):
    """EX-PC-014: yard fact found 2025-12-15 (start unknown), then a broker request
    dated 2026-05-15 says it ended at an unknown date."""
    w = world
    slot = await w.slot()
    found = w.evidence(("2025-12-15", "DAY"))
    await w.commit_at(
        slot,
        w.body(money("750000"), start=None, attestation_zone=CHICAGO, evidence=[found]),
        "2026-03-20T00:00:00Z",
    )
    request = w.evidence(("2026-05-15", "DAY"))
    await w.commit_at(
        slot,
        w.body(
            money("750000"),
            start=None,
            attestation_zone=CHICAGO,
            evidence=[found],
            end_state="UNKNOWN",
            ending=[request],
        ),
        "2026-07-10T00:00:00Z",
    )
    a = await w.read(slot, "2026-03-15T12:00:00Z", "2026-04-01T00:00:00Z")
    assert amount(a) == "750000" and a.json()["temporal"]["valid_to_state"] == "OPEN"
    b = await w.read(slot, "2025-03-15T12:00:00Z", "2026-07-11T00:00:00Z")
    assert b.json()["reason"] == "BEFORE_ATTESTATION_FLOOR" and "value" not in b.json()
    c = await w.read(slot, "2026-03-15T12:00:00Z", "2026-07-11T00:00:00Z")
    assert c.json()["reason"] == "UNKNOWN_END_WINDOW" and "value" not in c.json()
    d = await w.read(slot, "2026-07-15T12:00:00Z", "2026-07-11T00:00:00Z")
    assert d.status_code == 404
    async with AsyncSession(w.engine) as session:
        reader = TemporalFactReader(SqlAlchemyFactCommitRepository(session))
        internal_d = await reader.resolve(
            slot, valid_at=h.at("2026-07-15T12:00:00Z"), known_at=h.at("2026-07-11T00:00:00Z")
        )
        internal_b = await reader.resolve(
            slot, valid_at=h.at("2025-03-15T12:00:00Z"), known_at=h.at("2026-07-11T00:00:00Z")
        )
    assert isinstance(internal_d, NotProcessed)
    assert (
        isinstance(internal_b, ValidityUnknown) and internal_b.reason == "BEFORE_ATTESTATION_FLOOR"
    )


async def test_s0006_ac4_half_open_boundaries(world):
    w = world
    slot = await _section_87(w)
    assert amount(await w.read(slot, "2026-06-01T05:00:00Z", NOW)) == "5000000"  # at lower
    assert amount(await w.read(slot, "2026-06-01T04:59:59.999999Z", NOW)) == "2000000"
    # At the remainder's upper bound the successor answers.
    async with AsyncSession(w.engine) as session:
        reader = TemporalFactReader(SqlAlchemyFactCommitRepository(session))
        at_upper = await reader.resolve(
            slot, valid_at=h.at("2026-06-01T05:00:00Z"), known_at=h.at(NOW)
        )
    assert isinstance(at_upper, Resolved)
    assert at_upper.version.value["value"]["amount"] == "5000000"


async def test_s0006_ac5_read_returns_every_field_and_keeps_pilot_names(world):
    w = world
    slot = await _section_87(w)
    body = (await w.read(slot, "2026-05-15T12:00:00Z", NOW)).json()
    for pilot in (
        "id",
        "fact_slot_id",
        "value",
        "valid_start",
        "valid_end",
        "recorded_start",
        "recorded_end",
        "change_reason",
        "evidence_refs",
        "commit_id",
        "canonical_accepted_at",
    ):
        assert pilot in body
    assert h.at(body["source_received_at"]) == h.at("2026-01-08T00:00:00Z")
    assert body["artifact_created_at"] and body["assertion_created_at"]
    temporal = body["temporal"]
    assert (
        temporal["valid_from"]["granularity"] == "DAY" and temporal["valid_from"]["zone"] == CHICAGO
    )
    assert temporal["valid_to_state"] == "BOUNDED"
    assert temporal["valid_from_basis"] == "TEMPLATE_FIELD"
    assert {"attested_from", "attested_through", "attested_to"} <= set(temporal)


async def test_s0006_ac6_default_coordinates_and_malformed_ones(world):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("9"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    assert amount(await w.read(slot)) == "9"  # both default to now
    before = w.counts()
    for params in ({"validAsOf": "not-a-date"}, {"knownAsOf": "2026-13-45"}):
        async with w.client(w.service) as client:
            response = await client.get(f"/facts/{slot}", params=params)
        assert response.status_code in (400, 422)
    assert w.counts() == before


async def test_s0006_ac7_revoked_grant_is_denied_at_every_coordinate(world):
    w = world
    slot = await _section_87(w)
    with Session(w.sync_engine) as session, session.begin():
        reader = fixtures.seed_principal(session, issuer="urn:f0008:test", subject=f"r-{uuid4()}")
        membership = fixtures.seed_grant(session, reader.id, *w.a.scope, "TenantMember")
    assert amount(await w.read(slot, "2026-05-15T12:00:00Z", NOW, principal=reader)) == "2000000"
    with Session(w.sync_engine) as session, session.begin():
        revoke_membership(
            session,
            membership,
            operator_id=fixtures.SYNTHETIC_OPERATOR,
            approval_ref=fixtures.FIXTURE_APPROVAL,
            at=datetime.now(UTC),
        )
    missing = await w.read(uuid4(), "2026-05-15T12:00:00Z", NOW, principal=reader)
    for valid, known in (
        ("2026-05-15T12:00:00Z", NOW),
        ("2026-06-05T12:00:00Z", "2026-06-05T12:00:00Z"),  # before the revocation
        ("2026-07-01T12:00:00Z", "2026-06-15T00:00:00Z"),
    ):
        denied = await w.read(slot, valid, known, principal=reader)
        assert denied.status_code == 404
        volatile = {"instance": None, "traceId": None}
        assert denied.json() | volatile == missing.json() | volatile


async def test_d4_attestation_dates_of_unreadable_documents_are_not_disclosed(world):
    """A reader who cannot read an attesting document gets the non-disclosing 404,
    never a redacted answer (ADR-0078 D4, SEC-F7-02)."""
    w = world
    slot = await w.slot()
    secret = w.evidence(("2026-06-01", "DAY"), classifications=("restricted",))
    assert (
        await w.commit_v1(slot, money("1"), start=bound("2026-01-01T06:00:00Z"), evidence=[secret])
    ).status_code == 201
    with Session(w.sync_engine) as session, session.begin():
        internal = fixtures.seed_principal(session, issuer="urn:f0008:test", subject=f"i-{uuid4()}")
        fixtures.seed_grant(
            session, internal.id, *w.a.scope, "TenantMember", classifications=("internal",)
        )
    denied = await w.read(slot, "2026-03-01T00:00:00Z", principal=internal)
    assert denied.status_code == 404
    assert "2026-06-01" not in denied.text
    assert (await w.read(slot, "2026-03-01T00:00:00Z")).status_code == 200


async def test_d4_committer_must_read_every_attesting_document(world):
    """S0002 interaction contract: a committer who cannot read an evidence document
    is denied before any temporal reason, so no refusal reveals its date."""
    w = world
    slot = await w.slot()
    secret = w.evidence(("2026-06-01", "DAY"), classifications=("restricted",))
    with Session(w.sync_engine) as session, session.begin():
        limited = fixtures.seed_principal(session, issuer="urn:f0008:test", subject=f"l-{uuid4()}")
        fixtures.seed_grant(
            session, limited.id, *w.a.scope, "ServicePrincipal", classifications=("internal",)
        )
    before = w.counts()
    for expected in ("2026-06-01", "2026-05-01"):
        response = await w.commit_v1(
            slot,
            money("1"),
            start=bound("2026-01-01T06:00:00Z"),
            evidence=[secret],
            expected={"attested_from": {"value": expected, "precision": "DAY"}},
            principal=limited,
        )
        assert response.status_code == 404 and response.json()["code"] == "not_found"
    assert w.counts() == before


async def test_legacy_slot_reads_keep_pilot_behaviour(world):
    """S0007 AC2/AC3: a legacy pilot slot keeps the pilot request and read shape."""
    w = world
    with Session(w.sync_engine) as session, session.begin():
        legacy = fixtures.seed_fact_slot(session, *w.a.scope)
    body = w.body({"amount": 1}, start=bound("2026-01-01T06:00:00Z"))
    del body["temporal"]
    body["valid_from"] = "2026-01-01T00:00:00Z"
    created = await w.post(legacy, body)
    assert created.status_code == 201, created.text
    read = await w.read(legacy, "2026-03-01T00:00:00Z")
    assert read.status_code == 200 and read.json()["temporal"] is None
    assert (await w.read(legacy, "2025-03-01T00:00:00Z")).status_code == 404
    # A temporal block is not accepted on a legacy slot.
    refused = await w.post(legacy, w.body({"amount": 2}, start=bound("2026-06-01T05:00:00Z")))
    assert refused.status_code == 400
