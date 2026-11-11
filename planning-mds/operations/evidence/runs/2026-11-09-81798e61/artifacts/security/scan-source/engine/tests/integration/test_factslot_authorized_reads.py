"""F0007 T-08 regressions: exact payload authorization and revocation locking.

Each test owns a migrated PostgreSQL database through the existing harness.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.principal import PrincipalKind
from brain_factslots.answers import FactAnswerReader
from brain_factslots.names import NameFactReader
from brain_factslots.resolution import FactSlotResolver
from brain_factslots.service import AuthorizedFactSlots, SlotNotFound
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
from brain_persistence.grants import revoke_membership
from brain_security.execution import AuthorizationExecution
from brain_testing import fixtures
from brain_testing.factslots import AGGREGATE_LIMIT
from engine.tests.fixtures.factslots import harness
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
slot_world = harness.slot_world


async def _scoped_answer(w):  # type: ignore[no-untyped-def]
    slot = (await w.resolve(w.key(w.a, AGGREGATE_LIMIT))).slot_id
    secret = w.artifact(w.a, classifications=("restricted",))
    envelope = {
        "answer_contract": "fact-answer/v1",
        "state": "NOT_FOUND",
        "scope": {
            "content_artifact_id": str(secret),
            "profile_release_ref": "profile/1",
            "pages": [7, 8],
        },
    }
    response = await w.commit(slot, envelope)
    assert response.status_code == 201, response.text
    return slot, secret, envelope


def _reader(w, *, broad: bool):  # type: ignore[no-untyped-def]
    with Session(w.sync_engine) as session, session.begin():
        reader = fixtures.seed_principal(
            session, issuer="urn:f0007:read", subject=uuid4().hex, kind=PrincipalKind.USER
        )
        fixtures.seed_grant(
            session, reader.id, *w.a.scope, "TenantMember", classifications=("internal",)
        )
        broad_grant = (
            fixtures.seed_grant(session, reader.id, *w.a.scope, "TenantMember") if broad else None
        )
    return reader, broad_grant


async def test_http_authorizes_the_scope_of_the_exact_selected_payload(slot_world, monkeypatch):
    w = slot_world
    slot, secret, envelope = await _scoped_answer(w)
    reader, _ = _reader(w, broad=False)
    # Simulate a pre-query seeing an earlier, readable scope while the selected
    # HTTP version contains the restricted scope. No pre-query is authoritative.
    earlier = {
        **envelope,
        "scope": {**envelope["scope"], "content_artifact_id": str(w.a.artifact_id)},
    }

    async def earlier_answer(self, slot_id, *, valid_at, known_at):
        return earlier

    monkeypatch.setattr(SqlAlchemyFactSlotStore, "answer_at", earlier_answer)
    response = await w.get(slot, principal=reader)
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert str(secret) not in response.text
    assert (
        w.scalar(
            "SELECT count(*) FROM audit_event WHERE actor_principal_id = %s "
            "AND resource_id = %s AND action = 'read' AND operation_outcome = 'denied'",
            reader.id,
            secret,
        )
        == 1
    )


async def test_revocation_waits_for_slot_scope_and_payload_read_to_commit(slot_world):
    w = slot_world
    slot, secret, envelope = await _scoped_answer(w)
    reader, broad_grant = _reader(w, broad=True)
    revision = w.scalar(
        "SELECT revision FROM principal_authority WHERE principal_id = %s", reader.id
    )
    selected = asyncio.Event()
    attempted = asyncio.Event()
    selections = []

    class PausingAnswerStore(SqlAlchemyFactSlotStore):
        async def answer_at(self, slot_id, *, valid_at, known_at):
            stored = await super().answer_at(slot_id, valid_at=valid_at, known_at=known_at)
            selections.append(slot_id)
            if len(selections) == 1:
                selected.set()
                await attempted.wait()
            return stored

    def revoke(*, timeout: bool) -> bool:
        try:
            with Session(w.sync_engine) as session, session.begin():
                if timeout:
                    session.execute(text("SET LOCAL lock_timeout = '300ms'"))
                revoke_membership(
                    session,
                    broad_grant,
                    operator_id=fixtures.SYNTHETIC_OPERATOR,
                    approval_ref=fixtures.FIXTURE_APPROVAL,
                    at=datetime.now(UTC),
                )
        except OperationalError as exc:
            if timeout and getattr(exc.orig, "sqlstate", None) == "55P03":
                return True
            raise
        return False

    async def concurrent_revoke():
        await selected.wait()
        try:
            return await asyncio.to_thread(revoke, timeout=True)
        finally:
            attempted.set()

    async def read():
        now = datetime.now(UTC)
        async with AsyncSession(w.engine, expire_on_commit=False) as session:
            store = PausingAnswerStore(session)
            service = AuthorizedFactSlots(
                AuthorizationExecution(
                    SqlAlchemyAuthorityStore(session), w.policy, w.policy.release
                ),
                FactSlotResolver(w.registry, store),
                NameFactReader(store),
                FactAnswerReader(store),
            )
            return await service.read_answer(
                reader, slot, valid_at=now, known_at=now, trace_id="f0007-group-read"
            )

    answer, revocation_blocked = await asyncio.wait_for(
        asyncio.gather(read(), concurrent_revoke()), timeout=10
    )
    assert revocation_blocked is True
    assert selections == [slot]
    assert answer.to_json() == envelope
    decisions = w.rows(
        "SELECT resource_id, grant_revision, operation_outcome FROM audit_event "
        "WHERE trace_id = 'f0007-group-read' AND event_type = 'authorization_decision'"
    )
    assert {d[0] for d in decisions} == {slot, secret}
    assert {d[1] for d in decisions} == {revision}
    assert {d[2] for d in decisions} == {"succeeded"}
    # After the protected read releases its locks, supported revocation succeeds.
    assert await asyncio.to_thread(revoke, timeout=False) is False
    now = datetime.now(UTC)
    async with w.slots() as service:
        with pytest.raises(SlotNotFound):
            await service.read_answer(
                reader, slot, valid_at=now, known_at=now, trace_id="after-revocation"
            )
    assert (await w.get(slot, principal=reader)).status_code == 404
