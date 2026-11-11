"""F0007-S0005: name FactSlots (ADR-0066) with real F0006 v2 name evidence.

Uses the F0006 harness to publish immutable content and admit a v2 assertion, so
the evidence reference is the real admitted claim, not a stub. Expectations come
from the story ACs and EX-SEM-008 / EX-NAME-002.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from brain_domain.fact_slots import SlotReason, SlotRejected
from brain_domain.fact_values import ValueType
from brain_factslots.answers import FactAnswerReader
from brain_factslots.names import NameFactReader
from brain_factslots.predicates import SYSTEM_PREDICATES, StaticPredicateRegistry
from brain_factslots.resolution import FactSlotResolver
from brain_factslots.service import AuthorizedFactSlots
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
from brain_security.execution import AuthorizationExecution
from brain_testing import fixtures
from brain_testing.factslots import seed_subject, slot_key, test_registry
from engine.tests.fixtures.assertions import harness
from engine.tests.fixtures.factslots.harness import FactSlotWorld
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world_factory = harness.world_factory
world = harness.world

LEGAL, TRADE, FORMER, KNOWN_AS = SYSTEM_PREDICATES
ENVELOPE = "fact-answer/v1"


class Names:
    """F0006 world (KB A with admitted evidence) plus KB B in the same tenant."""

    def __init__(self, world) -> None:  # type: ignore[no-untyped-def]
        self.world = world
        self.tenant, self.kb_a = world.owner
        self.kb_b = uuid4()
        with Session(world.sync_engine) as session, session.begin():
            fixtures.seed_scope(session, self.tenant, self.kb_b)
            self.subject = seed_subject(session, self.tenant, [self.kb_a, self.kb_b])
            self.artifact_b = fixtures.seed_content_artifact(session, self.tenant, self.kb_b)
            self.service_b = fixtures.seed_principal(session, issuer="urn:f0007", subject="b")
            fixtures.seed_grant(
                session, self.service_b.id, self.tenant, self.kb_b, "ServicePrincipal"
            )
            fixtures.seed_grant(session, self.service_b.id, self.tenant, self.kb_b, "TenantMember")
        self.version = world.bundle.manifest.version_id
        # Reuse FactSlotWorld's HTTP and SQL helpers over the same database.
        self.http = FactSlotWorld.__new__(FactSlotWorld)
        self.http.url, self.http.engine = world.url, world.engine
        self.http.registry = test_registry()

    async def admitted(self) -> UUID:
        record = self.world.candidate()
        batch = await self.world.admit([record], delivery_key=str(uuid4()))
        assert len(batch.accepted) == 1
        return UUID(record["id"])

    def name(self, verbatim: str, assertion: UUID, version: UUID | None = None, **extra):  # type: ignore[no-untyped-def]
        return {
            "type": "name",
            "verbatim": verbatim,
            "evidence": {
                "assertion_id": str(assertion),
                "document_version_id": str(version or self.version),
            },
            **extra,
        }

    async def service(self):  # type: ignore[no-untyped-def]
        session = AsyncSession(self.world.engine, expire_on_commit=False)
        store = SqlAlchemyFactSlotStore(session)
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), self.world.policy, self.world.policy.release
        )
        return session, AuthorizedFactSlots(
            execution,
            FactSlotResolver(test_registry(), store),
            NameFactReader(store),
            FactAnswerReader(store),
        )

    async def resolve(self, predicate, *, member=None, principal=None, kb=None, artifact=None):  # type: ignore[no-untyped-def]
        key = slot_key(kb or self.kb_a, self.subject, predicate)
        if member is not None:
            key["member"] = member
        session, service = await self.service()
        async with session:
            return await service.resolve(
                principal or self.world.actor,
                key,
                source_artifact_ids=[artifact or self.world.bundle.key.artifact_id],
                trace_id="f0007-names",
            )

    async def names(self, principal, kb):  # type: ignore[no-untyped-def]
        now = datetime.now(UTC)
        session, service = await self.service()
        async with session:
            return await service.current_names(
                principal,
                knowledge_base_id=kb,
                entity_id=self.subject,
                valid_at=now,
                known_at=now,
                trace_id="f0007-names",
            )


@pytest.fixture
async def names(world):  # type: ignore[no-untyped-def]
    return Names(world)


def test_s0005_ac1_system_predicate_cardinalities():
    assert [(str(c.key), c.cardinality.value, c.value_type) for c in SYSTEM_PREDICATES] == [
        ("sys:hasLegalName@v1", "SINGLE", ValueType.NAME),
        ("sys:hasTradeName@v1", "MULTI", ValueType.NAME),
        ("sys:hasFormerName@v1", "MULTI", ValueType.NAME),
        ("sys:knownAs@v1", "MULTI", ValueType.NAME),
    ]
    from dataclasses import replace

    for contract in SYSTEM_PREDICATES:
        other = "MULTI" if contract.cardinality.value == "SINGLE" else "SINGLE"
        with pytest.raises(SlotRejected) as rejected:
            StaticPredicateRegistry([replace(contract, cardinality=other)])
        assert rejected.value.reason == SlotReason.CARDINALITY_CONFLICT


async def test_s0005_ac1_resolving_legal_name_as_multi_is_cardinality_conflict(names):
    legal = await names.resolve(LEGAL)
    assert legal.outcome == "CREATED" and legal.cardinality.value == "SINGLE"
    from dataclasses import replace

    from brain_domain.fact_slots import Cardinality

    alt = replace(
        LEGAL,
        release_ref="f0007-system-predicates/2",
        cardinality=Cardinality.MULTI,
        member_key_source="value",
    )
    registry = test_registry()
    registry._table[(alt.key, alt.release_ref)] = alt  # simulate a later conflicting release
    session = AsyncSession(names.world.engine, expire_on_commit=False)
    async with session:
        store = SqlAlchemyFactSlotStore(session)
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), names.world.policy, names.world.policy.release
        )
        service = AuthorizedFactSlots(
            execution,
            FactSlotResolver(registry, store),
            NameFactReader(store),
            FactAnswerReader(store),
        )
        key = slot_key(names.kb_a, names.subject, alt)
        key["member"] = names.name("Acme", await names.admitted())
        result = await service.resolve(
            names.world.actor,
            key,
            source_artifact_ids=[names.world.bundle.key.artifact_id],
            trace_id="t",
        )
    assert result.reason == SlotReason.CARDINALITY_CONFLICT


async def test_s0005_ac2_ex_sem_008_rename_is_a_new_version_in_the_same_slot(names):
    evidence = await names.admitted()
    first = await names.resolve(LEGAL)
    second = await names.resolve(LEGAL)
    assert first.slot_id == second.slot_id and second.outcome == "RESOLVED"
    slots_before = names.http.scalar("SELECT count(*) FROM fact_slot")
    start = datetime.now(UTC) - timedelta(days=60)
    old = await names.http.commit(
        first.slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": names.name("Acme Roofing Inc.", evidence),
        },
        principal=names.world.actor,
        valid_from=start,
    )
    assert old.status_code == 201, old.text
    renamed = await names.http.commit(
        first.slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": names.name("Acme Roofing & Restoration Inc.", evidence, name_kind="legal"),
        },
        principal=names.world.actor,
        valid_from=start + timedelta(days=30),
    )
    assert renamed.status_code == 201, renamed.text
    assert names.http.scalar("SELECT count(*) FROM fact_slot") == slots_before
    versions = names.http.rows(
        "SELECT value->'value'->>'verbatim', value->'value'->>'normalized' "
        "FROM canonical_fact_version WHERE slot_id = %s AND upper_inf(recorded) "
        "ORDER BY lower(valid)",
        first.slot_id,
    )
    assert versions == [
        ("Acme Roofing Inc.", "acme roofing inc."),
        ("Acme Roofing & Restoration Inc.", "acme roofing & restoration inc."),
    ]


async def test_s0005_ac3_name_without_admitted_evidence_is_rejected(names):
    legal = await names.resolve(LEGAL)
    before = names.http.counts()
    for value in (
        {"type": "name", "verbatim": "Acme"},
        names.name("Acme", uuid4()),
        names.name("Acme", await names.admitted(), version=uuid4()),
    ):
        response = await names.http.commit(
            legal.slot_id,
            {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value},
            principal=names.world.actor,
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "name_evidence_required"
    assert names.http.counts() == before
    member = await names.resolve(TRADE, member=names.name("Acme Storm", uuid4()))
    assert member.reason == SlotReason.NAME_EVIDENCE_REQUIRED
    assert names.http.counts() == before


async def test_trade_name_member_commit_keeps_its_normalized_identity(names):
    evidence = await names.admitted()
    member = await names.resolve(TRADE, member=names.name("Acme Restoration", evidence))
    before = names.http.counts()
    rejected = await names.http.commit(
        member.member_slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": names.name("Zed Services", evidence),
        },
        principal=names.world.actor,
    )
    assert rejected.status_code == 422 and rejected.json()["code"] == "member_value_mismatch"
    assert rejected.json()["detail"] is None
    assert names.http.counts() == before
    accepted = await names.http.commit(
        member.member_slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": names.name("  ACME   restoration ", evidence),
        },
        principal=names.world.actor,
    )
    assert accepted.status_code == 201, accepted.text
    shown = await names.http.get(member.member_slot_id, principal=names.world.actor)
    assert shown.status_code == 200
    assert shown.json()["value"]["value"]["normalized"] == "acme restoration"


async def test_s0005_ac4_kb_a_trade_name_is_invisible_in_kb_b(names):
    evidence = await names.admitted()
    trade = await names.resolve(TRADE, member=names.name("Acme Restoration", evidence))
    assert trade.member_created
    committed = await names.http.commit(
        trade.member_slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": names.name("Acme Restoration", evidence),
        },
        principal=names.world.actor,
    )
    assert committed.status_code == 201, committed.text
    seen_a = await names.names(names.world.actor, names.kb_a)
    assert [n.verbatim for n in seen_a] == ["Acme Restoration"]
    # KB B: the hook returns nothing, reads are not-found, and KB A evidence cannot
    # create a KB B member.
    assert await names.names(names.service_b, names.kb_b) == []
    assert await names.names(names.service_b, names.kb_a) == []
    denied = await names.http.get(trade.member_slot_id, principal=names.service_b)
    missing = await names.http.get(uuid4(), principal=names.service_b)
    assert denied.status_code == missing.status_code == 404
    # KB A evidence cited from KB B is indistinguishable from evidence that does
    # not exist: both are NAME_EVIDENCE_REQUIRED, with no KB A read attempted.
    results = [
        await names.resolve(
            TRADE,
            member=names.name("Acme Restoration", assertion),
            principal=names.service_b,
            kb=names.kb_b,
            artifact=names.artifact_b,
        )
        for assertion in (evidence, uuid4())
    ]
    assert [r.reason for r in results] == [SlotReason.NAME_EVIDENCE_REQUIRED] * 2


async def test_s0005_ac5_display_hook_is_precedence_free_and_creates_no_alias(names):
    evidence = await names.admitted()
    legal = await names.resolve(LEGAL)
    known = await names.resolve(KNOWN_AS, member=names.name("ACME", evidence))
    trade_b = await names.resolve(TRADE, member=names.name("Zeta Roofing", evidence))
    trade_a = await names.resolve(TRADE, member=names.name("Acme Storm Services", evidence))
    for slot, verbatim in (
        (legal.slot_id, "Acme Roofing Inc."),
        (known.member_slot_id, "ACME"),
        (trade_b.member_slot_id, "Zeta Roofing"),
        (trade_a.member_slot_id, "Acme Storm Services"),
    ):
        response = await names.http.commit(
            slot,
            {
                "answer_contract": ENVELOPE,
                "state": "PRESENT",
                "value": names.name(verbatim, evidence),
            },
            principal=names.world.actor,
        )
        assert response.status_code == 201, response.text
    facts = await names.names(names.world.actor, names.kb_a)
    assert [(f.predicate_key, f.verbatim) for f in facts] == [
        ("sys:hasLegalName@v1", "Acme Roofing Inc."),
        ("sys:hasTradeName@v1", "Acme Storm Services"),
        ("sys:hasTradeName@v1", "Zeta Roofing"),
        ("sys:knownAs@v1", "ACME"),
    ]
    assert all(f.slot_id for f in facts)
    tables = names.http.rows("SELECT to_regclass('entity_alias') IS NOT NULL")
    if tables[0][0]:
        assert names.http.scalar("SELECT count(*) FROM entity_alias") == 0
    created = names.http.scalar(
        "SELECT count(*) FROM audit_event WHERE event_type IN "
        "('fact_slot_created', 'fact_slot_member_created')"
    )
    assert created == 1 + 2 + 3  # legal; two headers; three members


async def test_g3_name_member_evidence_is_read_authorized_before_any_reason(names):
    """G3 security fix (SEC-F7-01): a name member's evidence artifacts are READ
    checks of the resolution, and they join the new member's restrictions."""
    from brain_security.execution import AuthorizationDenied

    evidence = await names.admitted()
    evidence_artifact = names.world.bundle.key.artifact_id
    with Session(names.world.sync_engine) as session, session.begin():
        public = fixtures.seed_content_artifact(
            session, names.tenant, names.kb_a, classifications=("public",)
        )
        limited = fixtures.seed_principal(session, issuer="urn:f0007", subject="public-only")
        fixtures.seed_grant(
            session,
            limited.id,
            names.tenant,
            names.kb_a,
            "ServicePrincipal",
            classifications=("public",),
        )
    before = names.http.counts()
    for assertion in (evidence, uuid4()):
        member = names.name("Acme Restricted", assertion)
        if assertion == evidence:
            with pytest.raises(AuthorizationDenied):
                await names.resolve(TRADE, member=member, principal=limited, artifact=public)
        else:  # an unknown assertion has no artifact to read: the reason is returned
            rejected = await names.resolve(TRADE, member=member, principal=limited, artifact=public)
            assert rejected.reason == SlotReason.NAME_EVIDENCE_REQUIRED
    assert names.http.counts() == before
    # A caller who can read the evidence creates the member, which depends on it.
    created = await names.resolve(
        TRADE, member=names.name("Acme Restricted", evidence), artifact=public
    )
    assert created.member_created
    rows = names.http.rows(
        "SELECT dependency_keys FROM resource_access WHERE resource_type = 'fact_slot' "
        "AND resource_id = %s",
        created.member_slot_id,
    )
    dependencies = rows[0][0]
    assert {"type": "content_artifact", "id": str(evidence_artifact)} in dependencies
    assert {"type": "content_artifact", "id": str(public)} in dependencies
