"""F0009 temporal lineage on PostgreSQL over the shipped F0008 split fixture.

EX-PROV-003 (S0003 AC1-AC7) and EX-PROV-004 mixed access (S0004 AC1-AC3/AC7).
Expected edges come from `qe.expected_version_edges` (stored-basis SQL).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import psycopg
import pytest
from brain_domain.authx import ResourceType
from brain_domain.principal import PrincipalKind
from brain_domain.provenance import LineageNotFound
from brain_security.execution import AuthorizationDenied
from brain_testing import fixtures
from engine.tests.fixtures import f0009_provenance as qe
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import CHICAGO, bound, money
from sqlalchemy.orm import Session

_clean_fact_tables = h._clean_fact_tables
database = h.database
world = h.world

NOT_FOUND = (AuthorizationDenied, LineageNotFound)
CANONICAL = ("canonical_fact_version", "canonical_fact_change", "canonical_commit", "outbox_event")


async def split_fixture(w, *, note_restrictions=None):  # type: ignore[no-untyped-def]
    """F0008 S0002 AC7 sequence: V1 then a later commit that splits V1 into a
    bounded remainder R and a new version V2 with an UNKNOWN end and ending note."""
    slot = await w.slot()
    positive = w.evidence(("2026-06-01", "DAY"))
    note = w.evidence(("2026-08-02", "DAY"), **(note_restrictions or {}))
    first = await w.commit_v1(
        slot,
        money("2000000"),
        start=bound("2026-01-01T06:00:00Z"),
        evidence=[positive],
        received="2026-01-08T15:00:00Z",
    )
    assert first.status_code == 201, first.text
    (v1,) = first.json()["fact_version_ids"]
    second = await w.commit_v1(
        slot,
        money("5000000"),
        start=bound("2026-03-01T06:00:00Z"),
        evidence=[positive],
        end_state="UNKNOWN",
        attestation_zone=CHICAGO,
        ending=[note],
    )
    assert second.status_code == 201, second.text
    remainder, v2 = second.json()["fact_version_ids"]
    return slot, UUID(v1), UUID(remainder), UUID(v2), positive, note


async def test_ex_prov_003_remainder_names_its_predecessor_and_changes(world, database):
    """S0003 AC1/AC2/AC3/AC7."""
    w = world
    slot, v1, remainder, v2, positive, note = await split_fixture(w)
    before = qe.snapshot(w.url, CANONICAL)
    result = await qe.read_lineage(
        w.engine, w.policy, w.service, ("fact_version", remainder), (ResourceType.FACT_SLOT, slot)
    )
    assert qe.result_edges(result) == qe.expected_version_edges(w.url, remainder)
    edges = qe.result_edges(result)
    assert qe.edge("split_of", ("fact_version", remainder), ("fact_version", v1)) in edges
    records = {(r.kind, r.id): r for r in result.records}
    rem, pred = records[("fact_version", remainder)].data, records[("fact_version", v1)].data
    # AC2: the remainder keeps its predecessor's payload, evidence and receipt.
    assert rem["value"] == pred["value"] and rem["evidence_refs"] == pred["evidence_refs"]
    assert rem["source_received_at"] == pred["source_received_at"]
    assert rem["temporal"]["split_of_version_id"] == str(v1)
    assert rem["temporal"]["valid_to_state"] == "BOUNDED"
    # AC1: exact coordinates of the requested version, never the current one.
    assert result.root.id == remainder and records[("fact_version", remainder)].id == remainder
    # AC3: the stored change link and reason; no new vocabulary.
    changes = [r for r in result.records if r.kind == "fact_change"]
    assert {
        (c.data["reason"], c.data["from_version_id"], c.data["to_version_id"]) for c in changes
    } == {("split", str(v1), str(remainder))}
    assert ("assertion", "corrected_from") not in {(k, k) for k, *_ in edges}
    assert not any(kind == "corrected_from" for kind, *_ in edges)
    # Legacy v1 evidence assertions are authorized, then honestly labelled.
    assert result.completeness == "INCOMPLETE"
    assert {g.record.kind for g in result.gaps} >= {"assertion"}
    assert not any(g.record.kind == "fact_version" for g in result.gaps)
    # AC7: a read changes no canonical row.
    assert qe.snapshot(w.url, CANONICAL) == before


async def test_supporting_and_ending_evidence_stay_distinct(world, database):
    """S0003 AC4: ending evidence is never relabelled as support; both need READ."""
    w = world
    slot, v1, remainder, v2, positive, note = await split_fixture(w)
    result = await qe.read_lineage(
        w.engine, w.policy, w.service, ("fact_version", v2), (ResourceType.FACT_SLOT, slot)
    )
    edges = qe.result_edges(result)
    assert edges == qe.expected_version_edges(w.url, v2)
    assert qe.edge("supported_by", ("fact_version", v2), ("evidence", positive)) in edges
    assert qe.edge("ending_evidence", ("fact_version", v2), ("evidence", note)) in edges
    assert qe.edge("supported_by", ("fact_version", v2), ("evidence", note)) not in edges
    note_artifact = w.artifact_of(note)
    assert (
        qe.edge("attested_by", ("fact_version", v2), ("content_artifact", note_artifact)) in edges
    )


def limited_reader(w):  # type: ignore[no-untyped-def]
    """Slot and ordinary source READ, but not the `acl-secret` source ACL."""
    with Session(w.sync_engine) as session, session.begin():
        principal = fixtures.seed_principal(
            session, issuer="urn:f0009:test", subject=f"limited-{uuid4()}", kind=PrincipalKind.USER
        )
        fixtures.seed_grant(
            session, principal.id, *w.a.scope, "TenantMember", source_acl_ids=("acl-public",)
        )
    return principal


async def test_ex_prov_004_one_denied_source_refuses_the_whole_history(world, database, caplog):
    """S0004 AC1/AC2/AC3/AC7: losing one ending/attestation source refuses the entire
    explanation, including an older version whose change endpoint exposes it."""
    w = world
    slot, v1, remainder, v2, positive, note = await split_fixture(
        w, note_restrictions={"source_acl_ids": ("acl-secret",)}
    )
    limited = limited_reader(w)
    # The limited principal does hold root fact access: an unrelated slot is readable.
    other = await w.slot()
    clean = await w.commit_v1(
        other, money("100"), start=bound("2026-01-01T06:00:00Z"), evidence=[w.evidence()]
    )
    (clean_version,) = clean.json()["fact_version_ids"]
    ok = await qe.read_lineage(
        w.engine,
        w.policy,
        limited,
        ("fact_version", UUID(clean_version)),
        (ResourceType.FACT_SLOT, other),
    )
    assert ok.root.id == UUID(clean_version)
    # V2 carries the secret ending source; V1's outgoing change endpoint V2 exposes
    # its attestation date, so both are refused as a whole.
    for root in (v2, v1):
        with pytest.raises(NOT_FOUND) as refused:
            await qe.read_lineage(
                w.engine, w.policy, limited, ("fact_version", root), (ResourceType.FACT_SLOT, slot)
            )
        assert str(note) not in str(refused.value) and "5000000" not in str(refused.value)
    # The remainder's lineage never touches the secret source: it stays readable and
    # contains no trace of it (refusal is scoped exactly, not by slot).
    rem = await qe.read_lineage(
        w.engine, w.policy, limited, ("fact_version", remainder), (ResourceType.FACT_SLOT, slot)
    )
    assert ("evidence", str(note)) not in qe.result_refs(rem)
    assert ("content_artifact", str(w.artifact_of(note))) not in qe.result_refs(rem)
    assert "5000000" not in caplog.text and str(note) not in caplog.text
    # The fully authorized principal still reads the same history.
    full = await qe.read_lineage(
        w.engine, w.policy, w.service, ("fact_version", v2), (ResourceType.FACT_SLOT, slot)
    )
    assert full.root.id == v2


async def test_cross_kb_anchor_and_spoofed_slot_are_non_disclosing(world, database):
    """S0003 AC6, S0004 AC2/AC5: a root outside the anchor's slot or KB is a miss."""
    w = world
    slot, v1, remainder, v2, *_ = await split_fixture(w)
    from brain_testing.factslots import AGGREGATE_LIMIT

    created = await w.resolve(
        w.key(w.b, AGGREGATE_LIMIT, subject=w.entity(w.b)), owner=w.b, principal=w.service_b
    )
    other_slot = created.slot_id
    with pytest.raises(NOT_FOUND):
        await qe.read_lineage(
            w.engine,
            w.policy,
            w.service_b,
            ("fact_version", v2),
            (ResourceType.FACT_SLOT, other_slot),
        )
    with pytest.raises(NOT_FOUND):  # no KB-B grant at all
        await qe.read_lineage(
            w.engine,
            w.policy,
            w.service,
            ("fact_version", v2),
            (ResourceType.FACT_SLOT, other_slot),
        )
    same_kb_other = await w.slot()
    with pytest.raises(NOT_FOUND):
        await qe.read_lineage(
            w.engine,
            w.policy,
            w.service,
            ("fact_version", v2),
            (ResourceType.FACT_SLOT, same_kb_other),
        )


async def test_broken_split_and_cross_scope_links_cannot_be_stored(world, database):
    """S0003 AC6: even with the elevated application role, the database refuses a
    cross-slot split predecessor and a cross-KB change endpoint."""
    w = world
    slot, v1, remainder, v2, *_ = await split_fixture(w)
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
            "value, valid, recorded, evidence, commit_id, source_received_at, "
            "artifact_created_at, assertion_created_at, canonical_accepted_at, "
            "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
            "valid_from_basis, valid_to_state, split_of_version_id) "
            "SELECT gen_random_uuid(), %s, tenant_id, knowledge_base_id, value, valid, "
            "recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, temporal_contract, temporal_kind, "
            "valid_from_granularity, valid_from_zone, valid_from_basis, valid_to_state, %s "
            "FROM canonical_fact_version WHERE id = %s",
            (await w.slot(), v1, v1),
        )
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.ForeignKeyViolation):
        connection.execute(
            "INSERT INTO canonical_fact_change (id, reason, from_version_id, to_version_id, "
            "tenant_id, knowledge_base_id) VALUES (%s, 'superseded', %s, %s, %s, %s)",
            (uuid4(), v1, v2, w.b.tenant_id, w.b.knowledge_base_id),
        )


async def test_current_grant_governs_a_historical_coordinate(world, database):
    """S0004 AC3: a prior successful read never reinstates a later-revoked grant."""
    w = world
    slot, v1, remainder, v2, *_ = await split_fixture(w)
    reader = limited_reader(w)
    first = await qe.read_lineage(
        w.engine, w.policy, reader, ("fact_version", v1), (ResourceType.FACT_SLOT, slot)
    )
    assert first.root.id == v1
    from datetime import UTC, datetime

    from brain_persistence.grants import revoke_membership
    from brain_persistence.models import MembershipRow
    from sqlalchemy import select

    with Session(w.sync_engine) as session, session.begin():
        memberships = list(
            session.scalars(select(MembershipRow).where(MembershipRow.principal_id == reader.id))
        )
        for membership in memberships:
            revoke_membership(
                session,
                membership.id,
                operator_id=fixtures.SYNTHETIC_OPERATOR,
                approval_ref=fixtures.FIXTURE_APPROVAL,
                at=datetime.now(UTC),
            )
    with pytest.raises(NOT_FOUND):
        await qe.read_lineage(
            w.engine, w.policy, reader, ("fact_version", v1), (ResourceType.FACT_SLOT, slot)
        )


async def test_concurrent_change_between_discovery_and_load_is_unavailable(
    world, database, monkeypatch
):
    """S0004 AC6 (assembly plan Step 4.6): a version appended after discovery is
    never silently reselected; the read refuses and audits, returning nothing."""
    from brain_domain.provenance import LineageUnavailable
    from brain_persistence.provenance import SqlAlchemyProvenanceRepository

    w = world
    slot = await w.slot()
    positive = w.evidence(("2026-06-01", "DAY"))
    first = await w.commit_v1(
        slot, money("2000000"), start=bound("2026-01-01T06:00:00Z"), evidence=[positive]
    )
    (v1,) = first.json()["fact_version_ids"]
    original = SqlAlchemyProvenanceRepository.discover

    async def discover_then_race(self, query):  # type: ignore[no-untyped-def]
        plan = await original(self, query)
        racing = await w.commit_v1(
            slot,
            money("3000000"),
            start=bound("2026-03-01T06:00:00Z"),
            evidence=[positive],
            expected_current=UUID(v1),
        )
        assert racing.status_code == 201, racing.text
        return plan

    monkeypatch.setattr(SqlAlchemyProvenanceRepository, "discover", discover_then_race)
    with pytest.raises(LineageUnavailable):
        await qe.read_lineage(
            w.engine,
            w.policy,
            w.service,
            ("fact_version", UUID(v1)),
            (ResourceType.FACT_SLOT, slot),
            trace_id="race",
        )
    outcomes = qe._rows(
        w.url,
        "SELECT operation_outcome FROM audit_event WHERE trace_id='race' "
        "AND event_type='authorization_decision'",
    )
    assert outcomes and all(row[0] == "failed" for row in outcomes)
