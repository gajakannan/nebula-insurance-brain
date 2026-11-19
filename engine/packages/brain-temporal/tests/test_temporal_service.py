"""F0008 fact-temporal/v1 service and reader logic with the in-memory fake
(ADR-0078 D1, D3-D5, D8, D9). Fast, deterministic checks of the algorithm; the
PostgreSQL suites prove the same rules against the database and its triggers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.facts import ChangeReason, CommitProposal, FactVersion
from brain_domain.temporal import (
    DatePrecision,
    DocumentDate,
    EndState,
    StartBasis,
    TemporalReason,
    TemporalRejected,
)
from brain_temporal.commit import CanonicalCommitService, LegacyTemporalUnsupported
from brain_temporal.reader import NotProcessed, Resolved, TemporalFactReader, ValidityUnknown

CHI = "America/Chicago"


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def money(amount: str) -> dict:
    return {
        "answer_contract": "fact-answer/v1",
        "state": "PRESENT",
        "value": {"type": "money", "amount": amount, "currency": "USD"},
    }


def state(name: str) -> dict:
    return {"answer_contract": "fact-answer/v1", "state": name}


def block(
    start: str | None = "2026-01-01T06:00:00Z",
    *,
    basis: str | None = "TEMPLATE_FIELD",
    end_state: str = "OPEN",
    end: str | None = None,
    zone: str | None = None,
    ending: tuple[UUID, ...] = (),
) -> dict:
    temporal: dict = {"contract": "fact-temporal/v1", "valid_to_state": end_state}
    if start is not None:
        temporal["valid_from"] = {"instant": start, "granularity": "DAY", "zone": CHI}
        if basis is not None:
            temporal["valid_from_basis"] = basis
    if end is not None:
        temporal["valid_to"] = {"instant": end, "granularity": "DAY", "zone": CHI}
    if zone is not None:
        temporal["attestation_zone"] = zone
    if ending:
        temporal["ending_evidence_refs"] = [str(e) for e in ending]
    return temporal


def proposal(slot: UUID, value: dict, temporal: dict | None, **kw: object) -> CommitProposal:
    return CommitProposal(
        slot_id=slot,
        value=value,
        valid_from=kw.pop("valid_from", None),  # type: ignore[arg-type]
        valid_to=None,
        change_reason=None,
        evidence_refs=kw.pop("evidence", ()),  # type: ignore[arg-type]
        review_decision_id=None,
        source_received_at=utc(kw.pop("received", "2026-06-12T14:00:00Z")),  # type: ignore[arg-type]
        artifact_created_at=utc("2026-06-12T14:05:00Z"),
        assertion_created_at=utc("2026-06-12T14:10:00Z"),
        expected_current_version_id=None,
        idempotency_key="f0008-unit-0001",
        temporal=temporal,
    )


@pytest.fixture
def clock() -> list[datetime]:
    return [utc("2026-01-10T00:00:00Z")]


@pytest.fixture
def service(repository, clock) -> CanonicalCommitService:  # type: ignore[no-untyped-def]
    return CanonicalCommitService(repository, clock=lambda: clock[0])


@pytest.fixture
def v1_slot(repository) -> UUID:  # type: ignore[no-untyped-def]
    slot = uuid4()
    repository.seed_slot(slot, identity_v1=True)
    return slot


def current(repository, slot) -> list[FactVersion]:  # type: ignore[no-untyped-def]
    return sorted(
        (
            v
            for v in repository.versions.values()
            if v.fact_slot_id == slot and v.recorded_end is None
        ),
        key=lambda v: v.valid_start,
    )


async def commit(service, repository, slot, value, temporal, clock, at, **kw):  # type: ignore[no-untyped-def]
    clock[0] = utc(at)
    return await service.commit(
        proposal(slot, value, temporal, **kw),
        authorized_scope=repository.scope,
        authorization_decision_id=None,
    )


async def test_d5_retroactive_endorsement_remainders_carry_predecessor_data(
    service, repository, v1_slot, clock
):
    await commit(
        service,
        repository,
        v1_slot,
        money("2"),
        block(),
        clock,
        "2026-01-10T00:00:00Z",
        received="2026-01-08T00:00:00Z",
    )
    await commit(
        service,
        repository,
        v1_slot,
        money("5"),
        block("2026-06-01T05:00:00Z"),
        clock,
        "2026-06-14T00:00:00Z",
    )
    remainder, successor = current(repository, v1_slot)
    assert remainder.value == money("2") and remainder.change_reason is ChangeReason.SPLIT
    assert remainder.source_received_at == utc("2026-01-08T00:00:00Z")
    assert remainder.temporal is not None and remainder.temporal.valid_to_state is EndState.BOUNDED
    assert remainder.temporal.valid_to == successor.temporal.valid_from  # type: ignore[union-attr]
    assert repository.split_of[remainder.id] is not None
    reasons = sorted(c["reason"].value for c in repository.changes)
    assert reasons == ["split", "superseded", "superseded"]


async def test_d5_bounded_successor_leaves_a_right_remainder(service, repository, v1_slot, clock):
    await commit(service, repository, v1_slot, money("2"), block(), clock, "2026-01-10T00:00:00Z")
    await commit(
        service,
        repository,
        v1_slot,
        money("5"),
        block("2026-06-01T05:00:00Z", end_state="BOUNDED", end="2026-07-01T05:00:00Z"),
        clock,
        "2026-06-14T00:00:00Z",
    )
    left, middle, right = current(repository, v1_slot)
    assert (left.value, middle.value, right.value) == (money("2"), money("5"), money("2"))
    assert right.valid_start == utc("2026-07-01T05:00:00Z") and right.valid_end is None
    assert right.temporal is not None and right.temporal.valid_to_state is EndState.OPEN
    assert right.temporal.valid_from_basis is StartBasis.TEMPLATE_FIELD


async def test_d5_right_remainder_of_an_unknown_end_clips_its_window(
    service, repository, v1_slot, clock
):
    positive, ending = uuid4(), uuid4()
    repository.document_dates.update(
        {
            positive: DocumentDate("2026-03-01", DatePrecision.DAY),
            ending: DocumentDate("2026-08-02", DatePrecision.DAY),
        }
    )
    await commit(
        service,
        repository,
        v1_slot,
        money("2"),
        block(end_state="UNKNOWN", zone=CHI, ending=(ending,)),
        clock,
        "2026-08-05T00:00:00Z",
        evidence=(positive,),
    )
    await commit(
        service,
        repository,
        v1_slot,
        money("5"),
        block("2026-02-01T06:00:00Z", end_state="BOUNDED", end="2026-04-01T05:00:00Z"),
        clock,
        "2026-08-06T00:00:00Z",
    )
    right = current(repository, v1_slot)[-1]
    assert right.temporal is not None and right.temporal.valid_to_state is EndState.UNKNOWN
    assert right.temporal.validity_unknown_from == utc("2026-04-01T05:00:00Z")
    assert right.temporal.attested_to == DocumentDate("2026-08-02", DatePrecision.DAY)


async def test_d8_end_revision_replaces_whole_and_unanchored_succession_is_refused(
    service, repository, v1_slot, clock
):
    found, request = uuid4(), uuid4()
    repository.document_dates.update(
        {
            found: DocumentDate("2025-12-15", DatePrecision.DAY),
            request: DocumentDate("2026-05-15", DatePrecision.DAY),
        }
    )
    floor = block(None, basis=None, zone=CHI)
    await commit(
        service,
        repository,
        v1_slot,
        money("7"),
        floor,
        clock,
        "2026-03-20T00:00:00Z",
        evidence=(found,),
    )
    (opened,) = current(repository, v1_slot)
    assert opened.temporal is not None
    assert opened.temporal.valid_from_basis is StartBasis.ATTESTATION_FLOOR
    revision = block(None, basis=None, zone=CHI, end_state="UNKNOWN", ending=(request,))
    await commit(
        service,
        repository,
        v1_slot,
        money("7"),
        revision,
        clock,
        "2026-07-10T00:00:00Z",
        evidence=(found,),
    )
    (revised,) = current(repository, v1_slot)
    assert revised.temporal is not None and revised.temporal.valid_to_state is EndState.UNKNOWN
    with pytest.raises(TemporalRejected) as refused:
        await commit(
            service,
            repository,
            v1_slot,
            money("8"),
            revision,
            clock,
            "2026-07-11T00:00:00Z",
            evidence=(found,),
        )
    assert refused.value.code is TemporalReason.SUCCESSION_START_UNANCHORED


@pytest.mark.parametrize(
    ("before", "after", "outcome"),
    [
        (money("5"), state("NOT_FOUND"), TemporalReason.STATE_SUPERSESSION_REFUSED),
        (money("5"), state("EXPLICIT_NEGATIVE"), None),
        (money("5"), money("6"), None),
        (state("NOT_PROCESSED"), state("NOT_STATED"), None),
    ],
)
async def test_d8_state_guard(service, repository, v1_slot, clock, before, after, outcome):  # type: ignore[no-untyped-def]
    await commit(service, repository, v1_slot, before, block(), clock, "2026-01-10T00:00:00Z")
    run: Callable = lambda: commit(  # noqa: E731
        service,
        repository,
        v1_slot,
        after,
        block("2026-06-01T05:00:00Z"),
        clock,
        "2026-06-14T00:00:00Z",
    )
    if outcome is None:
        await run()
        assert len(current(repository, v1_slot)) == 2
    else:
        with pytest.raises(TemporalRejected) as refused:
            await run()
        assert refused.value.code is outcome
        assert len(repository.versions) == 1 and len(repository.commits) == 1


async def test_d8_source_refusal_precedes_a_temporal_refusal(service, repository, v1_slot, clock):
    repository.source_error = RuntimeError("ineligible")
    with pytest.raises(RuntimeError):
        await commit(
            service,
            repository,
            v1_slot,
            money("1"),
            block(None, basis=None, zone=CHI),
            clock,
            "2026-01-10T00:00:00Z",
            evidence=(uuid4(),),
        )
    repository.source_error = None
    with pytest.raises(TemporalRejected) as refused:
        await commit(
            service,
            repository,
            v1_slot,
            money("1"),
            block(None, basis=None, zone=CHI),
            clock,
            "2026-01-10T00:00:00Z",
            evidence=(uuid4(),),
        )
    assert refused.value.code is TemporalReason.START_UNATTESTED
    assert repository.versions == {}


async def test_d1_contract_binding(service, repository, v1_slot, clock):
    with pytest.raises(TemporalRejected) as refused:
        await commit(
            service,
            repository,
            v1_slot,
            money("1"),
            None,
            clock,
            "2026-01-10T00:00:00Z",
            valid_from=utc("2026-01-01T00:00:00Z"),
        )
    assert refused.value.code is TemporalReason.TEMPORAL_FIELDS_REQUIRED
    legacy = uuid4()
    repository.seed_slot(legacy)
    with pytest.raises(LegacyTemporalUnsupported):
        await commit(
            service, repository, legacy, {"amount": 1}, block(), clock, "2026-01-10T00:00:00Z"
        )
    with pytest.raises(TemporalRejected):
        await commit(
            service, repository, legacy, {"amount": 1}, None, clock, "2026-01-10T00:00:00Z"
        )


async def test_legacy_path_remainders_keep_predecessor_timestamps(service, repository, clock):
    legacy = uuid4()
    repository.seed_slot(legacy)
    await commit(
        service,
        repository,
        legacy,
        {"amount": 2},
        None,
        clock,
        "2026-01-10T00:00:00Z",
        valid_from=utc("2026-01-01T00:00:00Z"),
        received="2026-01-08T00:00:00Z",
    )
    await commit(
        service,
        repository,
        legacy,
        {"amount": 5},
        None,
        clock,
        "2026-06-14T00:00:00Z",
        valid_from=utc("2026-06-01T00:00:00Z"),
        received="2026-06-12T00:00:00Z",
    )
    remainder = next(
        v for v in repository.versions.values() if v.change_reason is ChangeReason.SPLIT
    )
    assert remainder.source_received_at == utc("2026-01-08T00:00:00Z")
    assert remainder.temporal is None and repository.split_of[remainder.id] is None


# --- D9 reader ---------------------------------------------------------------


class ReadRepository:
    def __init__(self, repository, identity: int | None) -> None:  # type: ignore[no-untyped-def]
        self._repository = repository
        self._identity = identity

    async def slot_identity_version(self, slot_id: UUID) -> int | None:
        return self._identity

    def _visible(self, slot_id: UUID, known: datetime) -> list[FactVersion]:
        return [
            v
            for v in self._repository.versions.values()
            if v.fact_slot_id == slot_id
            and v.recorded_start <= known
            and (v.recorded_end is None or known < v.recorded_end)
        ]

    async def resolve_at(self, slot_id, *, valid_as_of, known_as_of):  # type: ignore[no-untyped-def]
        hits = [
            v
            for v in self._visible(slot_id, known_as_of)
            if v.valid_start <= valid_as_of and (v.valid_end is None or valid_as_of < v.valid_end)
        ]
        assert len(hits) <= 1
        return hits[0] if hits else None

    async def next_version_after(self, slot_id, *, valid_after, known_as_of):  # type: ignore[no-untyped-def]
        later = [v for v in self._visible(slot_id, known_as_of) if v.valid_start > valid_after]
        return min(later, key=lambda v: v.valid_start) if later else None


async def test_d9_resolution_order(service, repository, v1_slot, clock):
    found, ending = uuid4(), uuid4()
    repository.document_dates.update(
        {
            found: DocumentDate("2025-12-15", DatePrecision.DAY),
            ending: DocumentDate("2026-05-15", DatePrecision.DAY),
        }
    )
    await commit(
        service,
        repository,
        v1_slot,
        money("7"),
        block(None, basis=None, zone=CHI, end_state="UNKNOWN", ending=(ending,)),
        clock,
        "2026-07-10T00:00:00Z",
        evidence=(found,),
    )
    reader = TemporalFactReader(ReadRepository(repository, 1))  # type: ignore[arg-type]
    known = utc("2026-07-11T00:00:00Z")
    inside = await reader.resolve(v1_slot, valid_at=utc("2025-12-15T18:00:00Z"), known_at=known)
    assert isinstance(inside, Resolved)
    window = await reader.resolve(v1_slot, valid_at=utc("2026-03-15T12:00:00Z"), known_at=known)
    assert isinstance(window, ValidityUnknown) and window.reason == "UNKNOWN_END_WINDOW"
    assert window.version_id == window.version.id and window.temporal.attested_to is not None
    before = await reader.resolve(v1_slot, valid_at=utc("2025-03-15T12:00:00Z"), known_at=known)
    assert isinstance(before, ValidityUnknown) and before.reason == "BEFORE_ATTESTATION_FLOOR"
    after = await reader.resolve(v1_slot, valid_at=utc("2026-07-15T12:00:00Z"), known_at=known)
    assert isinstance(after, NotProcessed)
    legacy = TemporalFactReader(ReadRepository(repository, None))  # type: ignore[arg-type]
    assert (
        await legacy.resolve(v1_slot, valid_at=utc("2026-07-15T12:00:00Z"), known_at=known) is None
    )
