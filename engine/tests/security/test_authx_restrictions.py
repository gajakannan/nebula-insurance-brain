"""F0002-S0004 through the existing content, fact and review consumers on PostgreSQL.

EX-AUTHX-010 (each restriction independently), -011 (source ACL; forged request
attributes; missing metadata), -012 (derived resource with a denied evidence
dependency), -013 (reviewer annotation; revocation before submit; annotation never
grants commit), plus S0004 AC6 (restriction change between display and submit)
and AC7 (no protected bytes before the allow; denied == nonexistent externally).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from brain_domain.authx import (
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopedKind,
    Selector,
    SelectorMode,
)
from brain_persistence import fixtures
from brain_persistence.grants import revoke_membership
from brain_persistence.tenancy import change_resource_restrictions
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text

from .conftest import (
    bearer,
    decisions_for,
    run_sync,
    seed_content_artifact,
    seed_fact_slot,
    seed_grant,
    seed_principal,
    seed_review_item_in_batch,
)

ACCOUNT_OK, ACCOUNT_OTHER = uuid4(), uuid4()


def _account_selectors(account):
    return tuple(
        Selector(ScopedKind.ACCOUNT, SelectorMode.ONLY, frozenset({account}))
        if kind == ScopedKind.ACCOUNT
        else Selector(kind, SelectorMode.ALL)
        for kind in ScopedKind
    )


async def _reader(client, subject, tenant, kb, **slice_fields):
    principal = await seed_principal(client.session_factory, subject=subject)
    await seed_grant(
        client.session_factory, principal, tenant_id=tenant, knowledge_base_id=kb, **slice_fields
    )
    return principal


async def _count(client, sql, **params):
    async with client.session_factory() as session:
        return (await session.execute(text(sql), params)).scalar_one()


async def test_each_restriction_denies_independently_with_equivalent_404(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-010/011 / S0004 AC1/AC2/AC7: each conjunct alone denies while all
    others allow; denied and nonexistent are indistinguishable; no bytes opened."""
    tenant, kb = uuid4(), uuid4()
    await _reader(
        client,
        "restricted",
        tenant,
        kb,
        selectors=_account_selectors(ACCOUNT_OK),
        classifications=["internal"],
        source_acl_ids=["acl-portal"],
    )
    headers = bearer(rsa_key, "restricted")
    permitted = dict(
        parent_chain=[ScopedId(ScopedKind.ACCOUNT, ACCOUNT_OK)],
        classifications=["internal"],
        source_acl_ids=["acl-portal"],
    )
    cases = {
        "allowed": ({}, 200, "allowed"),
        "parent": (
            {"parent_chain": [ScopedId(ScopedKind.ACCOUNT, ACCOUNT_OTHER)]},
            404,
            "parent_denied",
        ),
        "classification": (
            {"classifications": ["internal", "loss-notes"]},
            404,
            "classification_denied",
        ),
        "source": ({"source_acl_ids": ["acl-claims"]}, 404, "source_denied"),
    }
    missing = await client.get(f"/content/{uuid4()}/files/source.pdf", headers=headers)
    for label, (override, status, reason) in cases.items():
        artifact = await seed_content_artifact(
            client.session_factory,
            tenant_id=tenant,
            knowledge_base_id=kb,
            **{**permitted, **override},
        )
        reads_before = len(client.content_store.file_reads)
        response = await client.get(f"/content/{artifact}/files/source.pdf", headers=headers)
        assert response.status_code == status, label
        assert (await decisions_for(client.session_factory, artifact))[-1]["reason_code"] == reason
        if status == 404:
            assert len(client.content_store.file_reads) == reads_before  # never opened
            assert response.json().keys() == missing.json().keys()
            assert response.json()["code"] == missing.json()["code"] == "not_found"


async def test_only_server_hydrated_attributes_count_and_missing_metadata_fails_closed(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-011 / S0004 AC3."""
    tenant, kb = uuid4(), uuid4()
    await _reader(client, "forger", tenant, kb, classifications=["internal"])
    headers = bearer(rsa_key, "forger")
    secret = await seed_content_artifact(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        classifications=["loss-notes"],
    )
    forged = await client.get(
        f"/content/{secret}",
        headers={**headers, "X-Classification": "internal"},
        params={"classification": "internal", "parent_chain": "", "source_acl_ids": ""},
    )
    assert forged.status_code == 404

    visible = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    assert (await client.get(f"/content/{visible}", headers=headers)).status_code == 200
    async with client.session_factory() as session:
        await session.execute(
            text("DELETE FROM resource_access WHERE resource_id = :r"), {"r": visible}
        )
        await session.commit()
    assert (await client.get(f"/content/{visible}", headers=headers)).status_code == 404
    last = (await decisions_for(client.session_factory, visible))[-1]
    assert last["reason_code"] == "missing_attributes" and last["scope"] is None

    moved = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    other_kb = uuid4()
    await run_sync(client.session_factory, lambda s: fixtures.seed_scope(s, tenant, other_kb))
    async with client.session_factory() as session:
        # Metadata that disagrees with the record's own ownership is never trusted.
        await session.execute(
            text("UPDATE resource_access SET knowledge_base_id = :kb WHERE resource_id = :r"),
            {"kb": other_kb, "r": moved},
        )
        await session.commit()
    assert (await client.get(f"/content/{moved}", headers=headers)).status_code == 404


async def test_derived_resource_needs_every_evidence_dependency(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-012 / S0004 AC4: visible entity alone is insufficient."""
    tenant, kb = uuid4(), uuid4()
    await _reader(client, "underwriter", tenant, kb, classifications=["internal"])
    headers = bearer(rsa_key, "underwriter")
    policy_doc = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb, classifications=["internal"]
    )
    loss_note = await seed_content_artifact(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        classifications=["loss-notes"],
    )
    other_policy_doc = await seed_content_artifact(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        classifications=["internal"],
    )

    def deps(*ids):
        return [ResourceKey(ResourceType.CONTENT_ARTIFACT, i) for i in ids]

    derived = await seed_fact_slot(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        dependency_keys=deps(policy_doc, loss_note),
    )
    fully_visible = await seed_fact_slot(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        dependency_keys=deps(policy_doc, other_policy_doc),
    )
    assert (await client.get(f"/facts/{derived}", headers=headers)).status_code == 404
    assert (await decisions_for(client.session_factory, derived))[-1]["reason_code"] == (
        "dependency_denied"
    )
    # All dependencies permitted -> only the independently permitted action (read)
    # proceeds; the slot has no version yet, so the read itself is a sanitized 404.
    response = await client.get(f"/facts/{fully_visible}", headers=headers)
    assert (await decisions_for(client.session_factory, fully_visible))[-1]["allowed"] is True
    assert response.status_code == 404
    # Evidence visibility is not a content read permission for a Reviewer-only principal.
    reviewer = await seed_principal(client.session_factory, subject="reviewer-only")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    assert (
        await client.get(f"/content/{policy_doc}", headers=bearer(rsa_key, "reviewer-only"))
    ).status_code == 404


async def test_reviewer_annotation_is_rechecked_at_submission_and_never_commits(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-013 / S0004 AC5/AC6."""
    tenant, kb = uuid4(), uuid4()
    reviewer = await seed_principal(client.session_factory, subject="rosa-f0002")
    membership = await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    item, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    item2, _ = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
        batch_id=batch,
    )
    item3, _ = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
        batch_id=batch,
    )
    headers = bearer(rsa_key, "rosa-f0002")

    def body(review_item):
        return {
            "decisions": [
                {"review_item_id": str(review_item), "action": "ACCEPT", "assertion_version": 1}
            ]
        }

    assert (await client.get(f"/reviews/{item}", headers=headers)).status_code == 200
    accepted = await client.post(
        f"/reviews/batches/{batch}/decisions", headers=headers, json=body(item)
    )
    assert accepted.status_code == 200
    decision_id = accepted.json()["decision_ids"][0]
    async with client.session_factory() as session:
        row = (
            await session.execute(
                text("SELECT reviewer_principal_id FROM review_decision WHERE id = :d"),
                {"d": decision_id},
            )
        ).one()
        linked = (
            await session.execute(
                text(
                    "SELECT a.decision_id, a.policy_hash, a.grant_revision FROM audit_event a "
                    "WHERE a.event_type = 'review_decision_recorded' "
                    "AND a.payload->>'review_decision_id' = :d"
                ),
                {"d": decision_id},
            )
        ).one()
    assert row.reviewer_principal_id == reviewer
    authz = (await decisions_for(client.session_factory, item))[-1]
    assert authz["action"] == "annotate" and authz["operation_outcome"] == "succeeded"
    assert str(linked.decision_id) == authz["decision_id"]
    assert (linked.policy_hash, linked.grant_revision) == (
        authz["policy_hash"],
        authz["grant_revision"],
    )

    # A restriction change between display and submission is observed (AC6).
    await run_sync(
        client.session_factory,
        lambda s: change_resource_restrictions(
            s,
            ResourceKey(ResourceType.REVIEW_TASK, item2),
            expected_revision=1,
            actor_id=fixtures.SYNTHETIC_OPERATOR,
            at=datetime.now(UTC),
            classifications=["loss-notes"],
            approval_ref="RECLASS-1",
        ),
    )
    # Narrow the reviewer to `internal` only: add the restricted slice, then revoke
    # the original unrestricted one, so the reclassified task is no longer admitted.
    await seed_grant(
        client.session_factory,
        reviewer,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="Reviewer",
        classifications=["internal"],
    )
    await run_sync(
        client.session_factory,
        lambda s: revoke_membership(
            s,
            membership,
            operator_id=fixtures.SYNTHETIC_OPERATOR,
            approval_ref="REV-2",
            at=datetime.now(UTC),
        ),
    )
    reclassified = await client.post(
        f"/reviews/batches/{batch}/decisions", headers=headers, json=body(item2)
    )
    assert reclassified.status_code == 404
    assert (await decisions_for(client.session_factory, item2))[-1]["reason_code"] == (
        "classification_denied"
    )
    decided = await _count(
        client, "SELECT count(*) FROM review_decision WHERE review_item_id = :i", i=item2
    )
    assert decided == 0

    # Annotation never grants fact_slot:commit, and no canonical state appears.
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
    commit = await client.post(
        f"/facts/{slot}/commits",
        headers=headers,
        json={
            "value": {"amount": "1"},
            "valid_from": "2026-01-01T00:00:00Z",
            "evidence_refs": [str(uuid4())],
            "source_received_at": "2026-01-10T00:00:00Z",
            "artifact_created_at": "2026-01-10T00:00:00Z",
            "assertion_created_at": "2026-01-10T00:00:00Z",
            "idempotency_key": "rev-commit-1",
        },
    )
    assert commit.status_code == 404
    assert (
        await _count(
            client, "SELECT count(*) FROM canonical_fact_version WHERE slot_id = :s", s=slot
        )
        == 0
    )
    # Fully revoked reviewer: the next submission is denied and writes nothing.
    await run_sync(client.session_factory, _revoke_all(reviewer))
    revoked = await client.post(
        f"/reviews/batches/{batch}/decisions", headers=headers, json=body(item3)
    )
    assert revoked.status_code == 404
    assert (
        await _count(
            client, "SELECT count(*) FROM review_decision WHERE review_item_id = :i", i=item3
        )
        == 0
    )


def _revoke_all(principal_id):
    def revoke(session):
        from brain_persistence.models import MembershipRow
        from sqlalchemy import select

        ids = session.scalars(
            select(MembershipRow.id).where(
                MembershipRow.principal_id == principal_id, MembershipRow.revoked_at.is_(None)
            )
        ).all()
        for membership_id in ids:
            revoke_membership(
                session,
                membership_id,
                operator_id=fixtures.SYNTHETIC_OPERATOR,
                approval_ref="REV-ALL",
                at=datetime.now(UTC),
            )

    return revoke


async def test_denied_and_nonexistent_are_byte_for_byte_indistinguishable(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """S0004 AC7: apart from the per-request trace ID and path, the denial body for an
    existing-but-forbidden artifact equals the body for an ID that does not exist."""
    tenant, kb = uuid4(), uuid4()
    await seed_principal(client.session_factory, subject="probe-outsider")
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    headers = bearer(rsa_key, "probe-outsider")
    denied = (await client.get(f"/content/{artifact}", headers=headers)).json()
    missing = (await client.get(f"/content/{uuid4()}", headers=headers)).json()
    for body in (denied, missing):
        body.pop("traceId")
        body.pop("instance")
    assert denied == missing


async def test_stale_review_reopens_a_task_that_inherits_its_restrictions(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """A stale annotation re-opens a review task for the newer assertion version; the
    engine-created task carries the original's security metadata (no default)."""
    tenant, kb = uuid4(), uuid4()
    reviewer = await seed_principal(client.session_factory, subject="stale-reviewer")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    item, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
        classifications=["internal", "claims"],
    )
    async with client.session_factory() as session:
        await session.execute(
            text(
                "UPDATE assertion SET version = 2 WHERE id = "
                "(SELECT assertion_id FROM review_item WHERE id = :i)"
            ),
            {"i": item},
        )
        await session.commit()
    response = await client.post(
        f"/reviews/batches/{batch}/decisions",
        headers=bearer(rsa_key, "stale-reviewer"),
        json={
            "decisions": [{"review_item_id": str(item), "action": "ACCEPT", "assertion_version": 1}]
        },
    )
    assert response.status_code == 200 and response.json()["stale"] == 1
    async with client.session_factory() as session:
        reopened = (
            await session.execute(
                text(
                    "SELECT r.classifications, r.tenant_id, r.knowledge_base_id "
                    "FROM resource_access r JOIN review_item i ON i.id = r.resource_id "
                    "WHERE i.assertion_version = 2 AND i.assertion_id = "
                    "(SELECT assertion_id FROM review_item WHERE id = :i)"
                ),
                {"i": item},
            )
        ).one()
    assert reopened.classifications == ["claims", "internal"]
    assert (reopened.tenant_id, reopened.knowledge_base_id) == (tenant, kb)
