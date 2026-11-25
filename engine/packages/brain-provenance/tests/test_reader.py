"""ProvenanceReader orchestration (S0001 AC5/AC6, S0004 AC1): discovery before
authorization of sources, materialization only after, output contract guard."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.provenance import (
    LineageUnavailable,
    ProvenanceContractError,
    ProvenanceEdge,
    ProvenanceQuery,
    ProvenanceRecord,
    ProvenanceResult,
    RecordRef,
)
from brain_provenance import ProvenancePlan, ProvenanceReader

T, K = uuid4(), uuid4()
SLOT = ResourceKey(ResourceType.FACT_SLOT, uuid4())
ARTIFACT = ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4())
ROOT = RecordRef("fact_version", uuid4())
EVIDENCE = RecordRef("evidence", uuid4())
NOW = datetime(2026, 11, 24, tzinfo=UTC).isoformat()


def _version_data() -> dict:
    return {
        "id": str(ROOT.id),
        "fact_slot_id": str(SLOT.id),
        "value": {"amount": "1000000", "currency": "USD"},
        "valid_start": NOW,
        "valid_end": None,
        "recorded_start": NOW,
        "recorded_end": None,
        "change_reason": None,
        "evidence_refs": [str(EVIDENCE.id)],
        "commit_id": str(uuid4()),
        "canonical_accepted_at": NOW,
        "review_decision_id": None,
        "source_received_at": NOW,
        "artifact_created_at": NOW,
        "assertion_created_at": NOW,
    }


def _evidence_data() -> dict:
    return {
        "assertion_id": str(uuid4()),
        "artifact_id": str(ARTIFACT.id),
        "block_id": None,
        "page": 1,
        "bbox": None,
        "char_start": None,
        "char_end": None,
        "precision": "page",
        "created_at": NOW,
        "stored_content_record": None,
    }


def _result(version_data: dict | None = None) -> ProvenanceResult:
    return ProvenanceResult.assemble(
        root=ROOT,
        tenant_id=T,
        knowledge_base_id=K,
        records=[
            ProvenanceRecord("fact_version", ROOT.id, version_data or _version_data()),
            ProvenanceRecord("evidence", EVIDENCE.id, _evidence_data()),
        ],
        edges=[ProvenanceEdge("supported_by", ROOT, EVIDENCE)],
        gaps=[],
    )


class FakeRepository:
    def __init__(self, events: list[str], result: ProvenanceResult | None = None) -> None:
        self.events = events
        self.result = result or _result()
        self.plan = ProvenancePlan(
            root=ROOT,
            anchor=SLOT,
            tenant_id=T,
            knowledge_base_id=K,
            record_refs=(EVIDENCE, ROOT),
            source_keys=tuple(sorted({SLOT, ARTIFACT})),
            metadata_fingerprint="f" * 64,
        )

    async def discover(self, query):  # type: ignore[no-untyped-def]
        self.events.append("discover")
        return self.plan

    async def materialize(self, plan):  # type: ignore[no-untyped-def]
        self.events.append("materialize")
        assert plan is self.plan
        return self.result


class FakeExecution:
    """Mimics the facade order: anchor decision, prepare, authorize, load."""

    def __init__(self, events: list[str], *, deny: set[ResourceKey] | None = None) -> None:
        self.events = events
        self.deny = deny or set()
        self.authorized: list[ResourceKey] = []

    async def read(  # type: ignore[no-untyped-def]
        self, principal, key, action, *, trace_id, load, requested, prepare_reads
    ):
        self.events.append(f"anchor:{key.type}")
        keys = await prepare_reads()
        self.events.append("authorize")
        self.authorized = list(keys)
        if self.deny & set(keys):
            raise PermissionError("denied")
        return await load(None)


def _principal() -> Principal:
    return Principal(uuid4(), PrincipalKind.USER, "https://issuer", "s", PrincipalStatus.ACTIVE)


QUERY = ProvenanceQuery(root=ROOT, anchor=SLOT)


async def test_discovery_and_authorization_precede_materialization() -> None:
    events: list[str] = []
    execution = FakeExecution(events)
    result = await ProvenanceReader(FakeRepository(events), execution).read(
        _principal(), QUERY, trace_id="t"
    )
    assert events == ["anchor:fact_slot", "discover", "authorize", "materialize"]
    # The anchor was decided first and is not re-decided with the sources.
    assert execution.authorized == [ARTIFACT]
    assert result.completeness == "COMPLETE"


async def test_denied_source_means_zero_materialize_calls() -> None:
    events: list[str] = []
    with pytest.raises(PermissionError):
        await ProvenanceReader(FakeRepository(events), FakeExecution(events, deny={ARTIFACT})).read(
            _principal(), QUERY, trace_id="t"
        )
    assert "materialize" not in events


async def test_plan_for_a_different_root_is_unavailable() -> None:
    events: list[str] = []
    repository = FakeRepository(events)
    repository.plan = replace(repository.plan, root=RecordRef("fact_version", uuid4()))
    with pytest.raises(LineageUnavailable):
        await ProvenanceReader(repository, FakeExecution(events)).read(
            _principal(), QUERY, trace_id="t"
        )
    assert "materialize" not in events


async def test_materialized_records_must_equal_the_plan() -> None:
    events: list[str] = []
    repository = FakeRepository(events)
    repository.plan = replace(repository.plan, record_refs=(ROOT,))
    with pytest.raises(LineageUnavailable):
        await ProvenanceReader(repository, FakeExecution(events)).read(
            _principal(), QUERY, trace_id="t"
        )


async def test_output_contract_violation_returns_no_partial_graph() -> None:
    events: list[str] = []
    bad = _version_data()
    bad["valid_start"] = "yesterday"  # not an RFC 3339 instant
    repository = FakeRepository(events, _result(bad))
    with pytest.raises(LineageUnavailable):
        await ProvenanceReader(repository, FakeExecution(events)).read(
            _principal(), QUERY, trace_id="t"
        )


async def test_invalid_query_contract_is_refused_before_any_read() -> None:
    events: list[str] = []
    query = ProvenanceQuery(root=ROOT, anchor=SLOT)
    object.__setattr__(query, "contract", "provenance-query/v9")
    with pytest.raises(ProvenanceContractError):
        await ProvenanceReader(FakeRepository(events), FakeExecution(events)).read(
            _principal(), query, trace_id="t"
        )
    assert events == []
