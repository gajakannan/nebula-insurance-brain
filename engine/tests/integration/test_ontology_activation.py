"""F0012-S0006 on PostgreSQL: impact report, review, gated activation and rollback
(AC1-AC7), EX-ONT-003/004, the split scenario and scope across two tenants."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from brain_domain.ontology import OntologyReason, OntologyRefused
from brain_security.execution import AuthorizationDenied
from engine.tests.fixtures import ontology as fx
from engine.tests.fixtures.factslots.harness import _clean_fact_tables, database
from engine.tests.integration.test_temporal_kind_activation import (
    ETERNAL,
    commit,
    entity,
    key,
    present,
    resolve,
)

onto_world = fx.onto_world
builder = fx.builder
__all__ = ["_clean_fact_tables", "database"]


async def refused(coro: Any) -> OntologyReason:
    with pytest.raises(OntologyRefused) as exc:
        await coro
    return exc.value.reason


def relabelled(version: int = 2) -> dict[str, Any]:
    module = fx.foundation_module()
    module["module"]["version"] = version
    module["terms"][0]["labels"] = {"en-US": "Thing (renamed)"}
    return module


async def test_first_release_report_review_activate(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    report, review = await w.approve(release)
    body = report.report
    assert body["predecessor"] is None and report.status == "complete"
    assert body["candidate"]["release_ref"] == release.ref
    assert {c["class"] for c in body["changes"]} == {"additive"} and len(body["changes"]) == 53
    assert body["inference"]["result"] == "no_change_within_scope"
    assert [u["owner"] for u in body["unexamined"]] == ["F0015", "F0065", "F0034"]
    assert all(r["affected"] == 0 for r in body["reach"])
    selection = await w.activate(release, review)
    assert selection.sequence == 1 and selection.action == "activate"
    history = await w.run(lambda s: s.history(w.member, w.a.scope, trace_id="t"))
    assert [(h.sequence, h.action, h.release_ref) for h in history] == [
        (1, "activate", release.ref)
    ]
    stored = w.rows(
        "SELECT r.status, v.decision, v.reviewer_principal_id FROM ontology_impact_report r "
        "JOIN ontology_release_review v ON v.report_id = r.id"
    )
    assert stored == [("complete", "approve", w.steward.id)]
    assert [e[0] for e in w.audit_events("ontology_release_activate")] == ["selected"]


async def test_report_is_deterministic_and_stored_once(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    one = await w.run(lambda s: s.report(w.steward, w.a.scope, release.ref, trace_id="t"))
    two = await w.run(lambda s: s.report(w.steward, w.a.scope, release.ref, trace_id="t"))
    assert one.report_digest == two.report_digest and one.id == two.id
    assert w.table_counts()["ontology_impact_report"] == 1


async def test_activation_refusals(onto_world: Any, builder: Any, tmp_path: Any) -> None:
    """AC5: each refusal reason, each audited as a refusal with no selection."""
    w = onto_world
    first = fx.foundation()
    second = builder.build("foundation", 2, {"foundation": relabelled()}, predecessor="../1")
    await w.install(first)
    await w.install(second)
    scope = w.a.scope

    async def act(release: Any, review: Any) -> OntologyReason:
        return await refused(
            w.run(lambda s: s.activate(w.steward, scope, release.ref, review, trace_id="t"))
        )

    assert await act(first, uuid4()) is OntologyReason.ACTIVATION_REPORT_REQUIRED
    _, review_first = await w.approve(first)
    _, review_second_early = await w.approve(second)  # predecessor = no head yet
    assert await act(second, review_first) is OntologyReason.REPORT_DIGEST_MISMATCH
    _, rejected = await w.approve(first, decision="reject")
    assert await act(first, rejected) is OntologyReason.REVIEW_REJECTED
    assert (
        await refused(
            w.run(
                lambda s: s.activate(
                    w.steward, scope, "ontrel:sha256-" + "9" * 64, review_first, trace_id="t"
                )
            )
        )
        is OntologyReason.RELEASE_NOT_INSTALLED
    )
    await w.activate(first, review_first)
    assert await act(second, review_second_early) is OntologyReason.PREDECESSOR_MISMATCH
    assert await act(first, review_first) is OntologyReason.SELECTION_CONFLICT
    assert (
        await refused(w.run(lambda s: s.rollback(w.steward, scope, second.ref, trace_id="t")))
        is OntologyReason.ROLLBACK_TARGET_NEVER_ACTIVE
    )
    assert (
        await refused(
            w.run(lambda s: s.review(w.steward, scope, uuid4(), "approve", "r", trace_id="t"))
        )
        is OntologyReason.REPORT_NOT_FOUND
    )

    # An incomplete report: a release installed without its predecessor's term.
    module = fx.foundation_module()
    module["module"]["version"] = 3
    module["terms"] = [t for t in module["terms"] if t["id"] != "foundation.measurement"]
    dropped = fx.ReleaseBuilder(tmp_path / "nohistory", with_history=False).build(
        "foundation", 3, {"foundation": module}
    )
    await w.install(dropped)
    report, review = await w.approve(dropped)
    assert report.status == "incomplete" and report.report["unresolved"]
    assert await act(dropped, review) is OntologyReason.REPORT_INCOMPLETE

    assert w.table_counts()["ontology_release_selection"] == 1
    outcomes = [e[0] for e in w.audit_events("ontology_release_activate")]
    assert outcomes.count("selected") == 1
    for reason in (
        "ACTIVATION_REPORT_REQUIRED",
        "REPORT_DIGEST_MISMATCH",
        "REVIEW_REJECTED",
        "PREDECESSOR_MISMATCH",
        "SELECTION_CONFLICT",
        "REPORT_INCOMPLETE",
        "RELEASE_NOT_INSTALLED",
    ):
        assert reason in outcomes, reason


async def test_grants_are_enforced_and_audited(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    for call in (
        lambda s: s.report(w.member, w.a.scope, release.ref, trace_id="t"),
        lambda s: s.report(w.service, w.a.scope, release.ref, trace_id="t"),
        lambda s: s.activate(w.service, w.a.scope, release.ref, uuid4(), trace_id="t"),
        lambda s: s.rollback(w.member, w.a.scope, release.ref, trace_id="t"),
        lambda s: s.report(w.steward_c, w.a.scope, release.ref, trace_id="t"),
    ):
        with pytest.raises(AuthorizationDenied):
            await w.run(call)
    with pytest.raises(AuthorizationDenied):
        await w.run(lambda s: s.history(w.service_c, w.a.scope, trace_id="t"))
    assert w.table_counts()["ontology_impact_report"] == 0
    assert [e[0] for e in w.audit_events("ontology_release_report")] == [
        "denied",
        "denied",
        "denied",
    ]


async def test_concurrent_activation_one_winner(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    _, review = await w.approve(release)
    results = await asyncio.gather(
        w.activate(release, review), w.activate(release, review), return_exceptions=True
    )
    winners = [r for r in results if not isinstance(r, BaseException)]
    losers = [r for r in results if isinstance(r, OntologyRefused)]
    assert len(winners) == 1 and len(losers) == 1
    assert losers[0].reason is OntologyReason.SELECTION_CONFLICT
    assert w.table_counts()["ontology_release_selection"] == 1


async def test_rollback_history_and_no_rewrite(onto_world: Any, builder: Any) -> None:
    """AC6: append-only selections; release rows and slot pins never change."""
    w = onto_world
    first = fx.foundation()
    second = builder.build("foundation", 2, {"foundation": relabelled()}, predecessor="../1")
    await w.install(first)
    await w.install(second)
    _, r1 = await w.approve(first)
    await w.activate(first, r1)
    slot = (await resolve(w, key(w, fx_org(), first.ref))).slot_id
    releases_before = w.rows(
        "SELECT id, release_ref, manifest_digest FROM ontology_release ORDER BY id"
    )
    _, r2 = await w.approve(second)
    await w.activate(second, r2)
    back = await w.run(lambda s: s.rollback(w.steward, w.a.scope, first.ref, trace_id="t"))
    assert back.sequence == 3 and back.action == "rollback"
    history = await w.run(lambda s: s.history(w.member, w.a.scope, trace_id="t"))
    assert [(h.sequence, h.action, h.release_ref) for h in history] == [
        (1, "activate", first.ref),
        (2, "activate", second.ref),
        (3, "rollback", first.ref),
    ]
    assert (
        w.rows("SELECT id, release_ref, manifest_digest FROM ontology_release ORDER BY id")
        == releases_before
    )
    assert w.scalar("SELECT predicate_release_ref FROM fact_slot WHERE id = %s", slot) == first.ref


def fx_org() -> str:
    return "fnd:accountOrganization@v1"


async def test_selection_guard_is_the_database_backstop(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    release_id = w.scalar("SELECT id FROM ontology_release")
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO ontology_release_selection (id, tenant_id, "
            "knowledge_base_id, sequence, action, "
            "release_id, review_id, actor_principal_id, decision_id, selected_at) "
            "VALUES (%s, %s, %s, 1, 'rollback', %s, NULL, %s, %s, now())",
            (uuid4(), w.a.tenant_id, w.a.knowledge_base_id, release_id, w.steward.id, uuid4()),
        )
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO ontology_release_selection (id, tenant_id, "
            "knowledge_base_id, sequence, action, "
            "release_id, review_id, actor_principal_id, decision_id, selected_at) "
            "VALUES (%s, %s, %s, 5, 'rollback', %s, NULL, %s, %s, now())",
            (uuid4(), w.a.tenant_id, w.a.knowledge_base_id, release_id, w.steward.id, uuid4()),
        )


async def test_ex_ont_003_and_004_reported(onto_world: Any, builder: Any) -> None:
    w = onto_world
    first = fx.foundation()
    await w.install(first)
    _, review = await w.approve(first)
    await w.activate(first, review)

    additive = fx.foundation_module()
    additive["module"]["version"] = 2
    ownership = next(t for t in additive["terms"] if t["id"] == "foundation.ownership-interest")
    ownership["parents"] = ["foundation.agreement", "foundation.thing"]
    ex003 = builder.build("foundation", 2, {"foundation": additive}, predecessor="../1")
    await w.install(ex003)
    report = (await w.run(lambda s: s.report(w.steward, w.a.scope, ex003.ref, trace_id="t"))).report
    assert report["status"] == "complete"
    change = next(
        c for c in report["changes"] if c["term_iri"].endswith("foundation.ownership-interest")
    )
    assert change["class"] == "additive"
    assert report["inference"]["result"] == "changes_detected"
    assert {
        "subject": "urn:nebula:ont:foundation.ownership-interest",
        "relation": "subClassOf",
        "object": "urn:nebula:ont:foundation.agreement",
    } in report["inference"]["added"]

    tightened = fx.foundation_module()
    tightened["module"]["version"] = 3
    tightened["constraints"].append(
        {
            "id": "foundation.constraint.status-required",
            "construct": "minCardinality",
            "subject": "foundation.account",
            "property": "foundation.account.status",
            "value": 1,
            "stage": "canonical-admission",
            "consumer": "F0017/F0018 canonical admission",
            "applicability": "every account at one valid/known coordinate",
            "severity": "violation",
            "on_nonconformance": "refuse the commit",
            "data_basis": "asserted",
        }
    )
    ex004 = builder.build("foundation", 3, {"foundation": tightened}, predecessor="../1")
    await w.install(ex004)
    report = (await w.run(lambda s: s.report(w.steward, w.a.scope, ex004.ref, trace_id="t"))).report
    assert report["inference"]["result"] == "no_change_within_scope"
    assert report["constraints"] == [
        {
            "constraint_id": "foundation.constraint.status-required",
            "consumer": "F0017/F0018 canonical admission",
            "change": "added",
            "detail": "new minCardinality at canonical-admission",
        }
    ]
    assert any(c["class"] == "constraint_tightening" for c in report["changes"])


async def test_split_scenario_end_to_end(onto_world: Any, builder: Any) -> None:
    """AC7 / master blueprint §112: split a foundation property; existing data keeps
    @1; rollback returns new work to @1; both releases and all selections remain."""
    w = onto_world
    first = fx.foundation()
    await w.install(first)
    _, r1 = await w.approve(first)
    await w.activate(first, r1)
    place = w.entity(w.a)
    slot = await resolve(w, key(w, "fnd:operatesAt@v1", first.ref, object_entity_id=str(place)))
    ok = await commit(
        w,
        slot.slot_id,
        present(entity(place)),
        {
            "contract": "fact-temporal/v1",
            "valid_from": {
                "instant": "2026-01-01T00:00:00+00:00",
                "granularity": "DAY",
                "zone": "UTC",
            },
            "valid_from_basis": "TEMPLATE_FIELD",
            "valid_to_state": "OPEN",
        },
    )
    assert ok.status_code == 201, ok.text

    module = fx.foundation_module()
    module["module"]["version"] = 2
    old = next(t for t in module["terms"] if t["id"] == "foundation.organization.operates-at")
    module["terms"].remove(old)
    for suffix, local in (("premises", "operatesAtPremises"), ("office", "operatesAtOffice")):
        term = {
            **old,
            "id": f"foundation.organization.operates-at-{suffix}",
            "predicate": {"local_name": local, "major": 1},
        }
        term["labels"] = {"en-US": f"Operates at {suffix}"}
        term["definition"] = (
            f"A {suffix} at which the organization operates during the valid period."
        )
        module["terms"].append(term)
    module["projection"] = [p for p in module["projection"] if p["property"] != old["id"]] + [
        {
            "property": f"foundation.organization.operates-at-{s}",
            "disposition": "edge",
            "label": f"OPERATES_AT_{s.upper()}",
            "direction": "subject-to-object",
        }
        for s in ("premises", "office")
    ]
    split = {
        "class": "split",
        "source_iris": ["urn:nebula:ont:foundation.organization.operates-at"],
        "replacement_iris": [
            "urn:nebula:ont:foundation.organization.operates-at-office",
            "urn:nebula:ont:foundation.organization.operates-at-premises",
        ],
        "rationale": "Separate premises from offices for property and liability lines.",
    }
    second = builder.build(
        "foundation", 2, {"foundation": module}, changes=[split], predecessor="../1"
    )
    await w.install(second)
    report, r2 = await w.approve(second)
    body = report.report
    classes = {c["term_iri"].removeprefix("urn:nebula:ont:"): c["class"] for c in body["changes"]}
    assert classes["foundation.organization.operates-at"] == "split"
    assert classes["foundation.organization.operates-at-premises"] == "split"
    reach = {
        (r["population"], r["predicate_key"]): (r["affected"], r["denominator"])
        for r in body["reach"]
    }
    assert reach[("fact_slot", "fnd:operatesAt@v1")] == (1, 1)
    assert reach[("assertion", "fnd:operatesAt@v1")] == (0, 0)
    assert report.status == "complete"
    await w.activate(second, r2)
    # Existing data still resolves foundation@1.
    again = await resolve(w, key(w, "fnd:operatesAt@v1", first.ref, object_entity_id=str(place)))
    assert again.outcome == "RESOLVED" and again.slot_id == slot.slot_id
    assert (
        w.scalar("SELECT predicate_release_ref FROM fact_slot WHERE id = %s", slot.slot_id)
        == first.ref
    )
    await w.run(lambda s: s.rollback(w.steward, w.a.scope, first.ref, trace_id="t"))
    head = (await w.run(lambda s: s.history(w.member, w.a.scope, trace_id="t")))[-1]
    assert head.release_ref == first.ref and head.action == "rollback"
    assert (
        w.table_counts()["ontology_release"] == 2
        and w.table_counts()["ontology_release_selection"] == 3
    )


async def test_scope_across_two_tenants(onto_world: Any) -> None:
    """ADR-0045 scope case: installs, reports, reach and selections are per tenant/KB."""
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    await w.install(release, principal=w.service_c, owner=w.c)
    slot = (await resolve(w, key(w, fx_org(), release.ref))).slot_id
    assert (await commit(w, slot, present(entity(w.entity(w.a))), ETERNAL)).status_code == 201
    report_c, review_c = await w.approve(release, owner=w.c)
    reach = {(r["population"], r["predicate_key"]): r for r in report_c.report["reach"]}
    assert reach[("fact_slot", fx_org())]["affected"] == 0
    assert reach[("fact_slot", fx_org())]["denominator"] == 0
    await w.activate(release, review_c, owner=w.c)
    a_history = await w.run(lambda s: s.history(w.member, w.a.scope, trace_id="t"))
    assert a_history == []
    assert w.scalar("SELECT count(*) FROM ontology_release") == 2
    assert w.scalar("SELECT count(DISTINCT knowledge_base_id) FROM ontology_term") == 2
