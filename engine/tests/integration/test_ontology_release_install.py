"""F0012 install on PostgreSQL: S0004 AC2/AC6/AC7, S0002 AC2/AC6, S0003 AC6, S0007 AC4.

Every persistence assertion is a fresh-session query.
"""

from __future__ import annotations

import asyncio
import copy
from typing import Any

import psycopg
import pytest
from alembic import command
from brain_domain.authx import Action, ResourceKey, ResourceType
from brain_domain.ontology import OntologyReason, OntologyRefused
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.ontology_releases import OntologyReleaseStore
from brain_security.execution import AuthorizationDenied, AuthorizationExecution
from engine.tests.fixtures import ontology as fx
from engine.tests.fixtures.factslots.harness import _clean_fact_tables, database
from sqlalchemy.ext.asyncio import AsyncSession

onto_world = fx.onto_world
builder = fx.builder
__all__ = ["_clean_fact_tables", "database"]


async def test_install_writes_one_immutable_release(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    canonical_before = w.table_counts(fx.CANONICAL_TABLES)
    result = await w.install(release)
    assert result.status == "installed" and result.release_ref == release.ref
    counts = w.table_counts()
    assert counts["ontology_release"] == 1
    assert counts["ontology_module_version"] == 1
    assert counts["ontology_release_module"] == 1
    assert counts["ontology_term"] == 53
    assert counts["ontology_change_record"] == 0
    # S0004 AC7: install never activates; no canonical write (zero parses/model calls).
    assert counts["ontology_release_selection"] == 0
    assert w.table_counts(fx.CANONICAL_TABLES) == canonical_before
    stored = w.rows(
        "SELECT release_ref, manifest_digest, installed_by FROM "
        "ontology_release WHERE knowledge_base_id = %s",
        w.a.knowledge_base_id,
    )
    assert stored == [(release.ref, release.manifest["manifest_digest"], w.service.id)]
    predicates = w.rows(
        "SELECT predicate_key, temporal_kind FROM ontology_term WHERE "
        "predicate_key IS NOT NULL ORDER BY 1"
    )
    assert len(predicates) == 15 and ("fnd:accountOrganization@v1", "ETERNAL") in predicates
    events = w.audit_events("ontology_release_install")
    assert len(events) == 1 and events[0][0] == "installed" and release.ref in events[0][2]
    decision = w.rows(
        "SELECT decision, operation_outcome FROM audit_event WHERE "
        "event_type = 'authorization_decision' "
        "AND decision_id = %s",
        events[0][3],
    )
    assert decision == [(True, "succeeded")]


async def test_reinstall_is_idempotent(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    before = w.table_counts()
    again = await w.install(release)
    assert again.status == "already_installed"
    assert w.table_counts() == before


async def test_concurrent_install_gives_one_set_of_rows(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    results = await asyncio.gather(w.install(release), w.install(release))
    assert sorted(r.status for r in results) == ["already_installed", "installed"]
    assert w.table_counts()["ontology_release"] == 1
    assert w.table_counts()["ontology_term"] == 53


async def test_failure_mid_install_leaves_no_rows(
    onto_world: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    w = onto_world
    original = OntologyReleaseStore.install

    async def broken(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        await original(self, *args, **kwargs)
        raise RuntimeError("injected failure after all release rows were written")

    monkeypatch.setattr(OntologyReleaseStore, "install", broken)
    with pytest.raises(RuntimeError):
        await w.install(fx.foundation())
    assert set(w.table_counts().values()) == {0}
    failed = w.rows(
        "SELECT operation_outcome FROM audit_event WHERE event_type = 'authorization_decision' "
        "AND action = 'install'"
    )
    assert failed == [("failed",)]


@pytest.mark.parametrize("table", fx.ONTOLOGY_TABLES[:4])
async def test_installed_rows_are_immutable(onto_world: Any, table: str) -> None:
    w = onto_world
    await w.install(fx.foundation())
    for statement in (f"UPDATE {table} SET tenant_id = tenant_id", f"DELETE FROM {table}"):
        with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(statement)
    assert w.table_counts()["ontology_term"] == 53


@pytest.mark.parametrize("table", fx.ONTOLOGY_TABLES)
async def test_truncate_refused_on_every_table(onto_world: Any, table: str) -> None:
    w = onto_world
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(f"TRUNCATE {table} CASCADE")


async def test_digest_mismatch_refused_before_any_row(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    tampered = copy.deepcopy(release.manifest)
    tampered["sequence"] = 9
    with pytest.raises(OntologyRefused) as refused:
        await w.install(fx.Release(tampered, release.normalized, release.directory))
    assert refused.value.reason is OntologyReason.MANIFEST_DIGEST_MISMATCH
    normalized = copy.deepcopy(release.normalized)
    normalized["terms"][0]["term"]["definition"] = "Tampered definition text for the test."
    with pytest.raises(OntologyRefused) as refused:
        await w.install(fx.Release(release.manifest, normalized, release.directory))
    assert refused.value.reason is OntologyReason.MANIFEST_DIGEST_MISMATCH
    invalid = copy.deepcopy(release.manifest)
    invalid["contract"] = "something-else"
    with pytest.raises(OntologyRefused) as refused:
        await w.install(fx.Release(invalid, release.normalized, release.directory))
    assert refused.value.reason is OntologyReason.MANIFEST_INVALID
    assert set(w.table_counts().values()) == {0}
    outcomes = [e[0] for e in w.audit_events("ontology_release_install")]
    assert outcomes == ["MANIFEST_DIGEST_MISMATCH", "MANIFEST_DIGEST_MISMATCH", "MANIFEST_INVALID"]


async def test_same_module_version_with_new_content_refused(onto_world: Any, tmp_path: Any) -> None:
    """S0004 AC2: a relabelled foundation@1 module (same definitions) is new content."""
    w = onto_world
    await w.install(fx.foundation())
    module = fx.foundation_module()
    module["terms"][0]["labels"] = {"en-US": "Anything"}
    variant = fx.ReleaseBuilder(tmp_path).build("foundation", 2, {"foundation": module})
    with pytest.raises(OntologyRefused) as refused:
        await w.install(variant)
    assert refused.value.reason is OntologyReason.MODULE_VERSION_IMMUTABLE
    assert w.table_counts()["ontology_release"] == 1


async def test_identity_reuse_refused_at_install(onto_world: Any, tmp_path: Any) -> None:
    """S0002 AC2 at install: history comes from installed rows, not the files."""
    w = onto_world
    await w.install(fx.foundation())
    module = fx.foundation_module()
    module["module"]["version"] = 2
    module["terms"][1]["definition"] = "A redefined party that would silently reuse the IRI."
    variant = fx.ReleaseBuilder(tmp_path, with_history=False).build(
        "foundation", 2, {"foundation": module}
    )
    with pytest.raises(OntologyRefused) as refused:
        await w.install(variant)
    assert refused.value.reason is OntologyReason.IDENTITY_REUSE_REJECTED
    assert w.table_counts()["ontology_release"] == 1


async def test_denied_install_is_audited_and_writes_nothing(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    for principal, owner in ((w.member, w.a), (w.steward, w.a), (w.service_c, w.a)):
        with pytest.raises(AuthorizationDenied):
            await w.install(release, principal=principal, owner=owner)
    assert set(w.table_counts().values()) == {0}
    events = w.audit_events("ontology_release_install")
    assert [e[0] for e in events] == ["denied", "denied", "denied"]
    assert all(release.ref in e[2] for e in events)
    denials = w.rows(
        "SELECT reason_code FROM audit_event WHERE event_type = "
        "'authorization_decision' AND action = 'install' "
        "ORDER BY occurred_at"
    )
    assert [r[0] for r in denials] == ["policy_denied", "policy_denied", "no_membership"]


async def test_unprovisioned_scope_fails_closed(onto_world: Any) -> None:
    """G0-5: without a trusted resource_access row the scope has no metadata."""
    w = onto_world
    unprovisioned = w.entity(w.a)  # an id that is not a provisioned knowledge base
    with pytest.raises(AuthorizationDenied) as denied:
        await w.install(
            fx.foundation(), owner=fx.Owner(w.a.tenant_id, unprovisioned, w.a.artifact_id)
        )
    assert denied.value.decision.reason_code.value == "missing_attributes"


async def test_tenant_extension_install_is_unsupported(onto_world: Any) -> None:
    """S0002 AC6: refused for every principal, audited, zero rows."""
    w = onto_world
    for principal in (w.service, w.member):
        with pytest.raises(OntologyRefused) as refused:
            await w.run(
                lambda s, p=principal: s.install_extension(
                    p, w.a.scope, "tenant-ext.yaml", trace_id="t"
                )
            )
        assert refused.value.reason is OntologyReason.TENANT_EXTENSION_UNSUPPORTED
    assert set(w.table_counts().values()) == {0}
    events = w.audit_events("ontology_release_install_extension")
    assert [e[0] for e in events] == ["TENANT_EXTENSION_UNSUPPORTED", "denied"]


async def test_vocabulary_grants_nothing(onto_world: Any) -> None:
    """S0003 AC6 / EX-PC-011: decisions on existing resources are identical before
    and after the foundation release is installed."""
    w = onto_world

    async def decisions() -> list[tuple[str, bool, str]]:
        out = []
        for principal in (w.member, w.steward, w.service, w.reader_b):
            for key, action in (
                (ResourceKey(ResourceType.CONTENT_ARTIFACT, w.a.artifact_id), Action.READ),
                (ResourceKey(ResourceType.CONTENT_ARTIFACT, w.a.artifact_id), Action.INTERPRET),
            ):
                async with AsyncSession(w.engine) as session:
                    execution = AuthorizationExecution(
                        SqlAlchemyAuthorityStore(session), w.policy, w.policy.release
                    )
                    try:
                        await execution.read(principal, key, action, trace_id="t", load=_none)
                        out.append((str(principal.id), True, action.value))
                    except AuthorizationDenied as denied:
                        out.append((str(principal.id), False, denied.decision.reason_code.value))
        return out

    before = await decisions()
    await w.install(fx.foundation())
    assert await decisions() == before


async def _none(_decision: Any) -> None:
    return None


async def test_downgrade_refused_after_install(onto_world: Any) -> None:
    """S0007 AC4: the Phase B rule is refuse; nothing is altered."""
    w = onto_world
    await w.install(fx.foundation())
    before = w.table_counts()
    with pytest.raises(RuntimeError, match="0017 downgrade refused"):
        command.downgrade(fx.configuration(), "0016")
    assert w.table_counts() == before
    assert w.scalar("SELECT version_num FROM alembic_version") == "0017"


def _recomputed(manifest: dict, normalized: dict) -> tuple[dict, dict]:
    """A hand-crafted, self-consistent release: every digest recomputed."""
    from brain_domain.ontology import (
        definition_digest,
        manifest_digest,
        release_ref_for,
        sha256_jcs,
    )

    for module in normalized["modules"]:
        module["normalized"]["terms"] = sorted(
            (r["term"] for r in normalized["terms"]), key=lambda t: t["iri"]
        )
        module["digest"] = sha256_jcs(module["normalized"])
    for row in normalized["terms"]:
        row["definition_digest"] = definition_digest(row["term"])
    manifest["modules"] = [
        {"id": m["id"], "version": m["version"], "digest": m["digest"]}
        for m in normalized["modules"]
    ]
    manifest["terms_digest"] = sha256_jcs(
        [[r["iri"], r["definition_digest"]] for r in normalized["terms"]]
    )
    digest = manifest_digest(manifest)
    manifest["manifest_digest"], manifest["release_ref"] = digest, release_ref_for(digest)
    return manifest, normalized


async def test_crafted_release_cannot_claim_reserved_or_mismatched_predicates(
    onto_world: Any,
) -> None:
    w = onto_world
    release = fx.foundation()
    manifest, normalized = copy.deepcopy(release.manifest), copy.deepcopy(release.normalized)
    row = next(
        r for r in normalized["terms"] if r["term"].get("predicate_key") == "fnd:accountStatus@v1"
    )
    row["term"]["predicate_key"] = "sys:hasLegalName@v1"
    entry = next(p for p in manifest["predicates"] if p["predicate_key"] == "fnd:accountStatus@v1")
    entry["predicate_key"] = "sys:hasLegalName@v1"
    crafted = fx.Release(*_recomputed(manifest, normalized), release.directory)
    with pytest.raises(OntologyRefused) as refused:
        await w.install(crafted)
    assert refused.value.reason is OntologyReason.MANIFEST_INVALID

    manifest, normalized = copy.deepcopy(release.manifest), copy.deepcopy(release.normalized)
    entry = next(p for p in manifest["predicates"] if p["predicate_key"] == "fnd:accountStatus@v1")
    entry["temporal_kind"] = "ETERNAL"  # manifest says ETERNAL, the installed term says STATE
    crafted = fx.Release(*_recomputed(manifest, normalized), release.directory)
    with pytest.raises(OntologyRefused) as refused:
        await w.install(crafted)
    assert refused.value.reason is OntologyReason.MANIFEST_DIGEST_MISMATCH
    assert set(w.table_counts().values()) == {0}
