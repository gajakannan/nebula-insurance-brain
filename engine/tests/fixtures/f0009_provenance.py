"""F0009 QE fixtures: independently authored expectations and PostgreSQL helpers.

Expected edges are derived here with raw SQL from the *stored basis* column of
the assembly plan's Edge Semantics table, without importing the implementation's
traversal (S0006 AC5). The examples are synthetic development fixtures and stay
outside the frozen holdout.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import httpx2 as httpx
import psycopg
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.principal import Principal
from brain_domain.provenance import ProvenanceQuery, RecordRef
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.provenance import SqlAlchemyProvenanceRepository
from brain_provenance import ProvenanceReader
from brain_security.execution import AuthorizationExecution
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.app import create_app
from brain_api.deps import current_principal, get_content_store, get_db_session

Edge = tuple[str, tuple[str, str], tuple[str, str]]

# QE copy of the closed edge table (assembly plan, rework 2026-11-24-c32acf46).
EDGE_TABLE: dict[str, set[tuple[str, str]]] = {
    "corrected_from": {("assertion", "assertion")},
    "supported_by": {("assertion", "evidence"), ("fact_version", "evidence")},
    "ending_evidence": {("fact_version", "evidence")},
    "located_in": {("evidence", "content_artifact")},
    "interpreted_in": {("assertion", "interpretation_run")},
    "interprets": {("interpretation_run", "content_artifact")},
    "artifact_of": {("content_artifact", "document_version")},
    "version_of": {("document_version", "source_document")},
    "reviews": {("review_decision", "assertion"), ("review_attempt", "assertion")},
    "created_assertion": {("review_decision", "assertion")},
    "reserved_learning": {("review_decision", "learning_reservation")},
    "recorded_decision": {("fact_version", "review_decision")},
    "split_of": {("fact_version", "fact_version")},
    "changed_from": {("fact_change", "fact_version")},
    "changed_to": {("fact_change", "fact_version")},
    "attested_by": {("fact_version", "content_artifact")},
    "derived_from": {
        ("assertion", "derivation_reference"),
        ("fact_version", "derivation_reference"),
    },
}


def edge(kind: str, source: tuple[str, Any], target: tuple[str, Any]) -> Edge:
    assert (source[0], target[0]) in EDGE_TABLE[kind], (kind, source[0], target[0])
    return (kind, (source[0], str(source[1])), (target[0], str(target[1])))


def result_edges(result: Any) -> set[Edge]:
    return {
        (e.kind, (e.source.kind, str(e.source.id)), (e.target.kind, str(e.target.id)))
        for e in result.edges
    }


def result_refs(result: Any) -> set[tuple[str, str]]:
    return {(r.kind, str(r.id)) for r in result.records}


def _rows(url: str, sql: str, *params: Any) -> list[tuple[Any, ...]]:
    with psycopg.connect(url) as connection:
        return connection.execute(sql, params).fetchall()


def expected_source_chain(url: str, assertion_ids: Iterable[UUID]) -> set[Edge]:
    """Stored-basis edges for assertions: evidence, run, artifact, document."""
    edges: set[Edge] = set()
    artifacts: set[UUID] = set()
    for assertion_id in assertion_ids:
        ((run_id, original),) = _rows(
            url, "SELECT run_id, original_assertion_id FROM assertion WHERE id = %s", assertion_id
        )
        if original is not None:
            edges.add(edge("corrected_from", ("assertion", assertion_id), ("assertion", original)))
        if run_id is not None:
            ((run_artifact,),) = _rows(
                url, "SELECT artifact_id FROM semantic_interpretation_run WHERE id = %s", run_id
            )
            edges.add(
                edge("interpreted_in", ("assertion", assertion_id), ("interpretation_run", run_id))
            )
            edges.add(
                edge(
                    "interprets", ("interpretation_run", run_id), ("content_artifact", run_artifact)
                )
            )
            artifacts.add(run_artifact)
        for evidence_id, artifact_id in _rows(
            url,
            "SELECT id, artifact_id FROM assertion_evidence WHERE assertion_id = %s",
            assertion_id,
        ):
            edges.add(edge("supported_by", ("assertion", assertion_id), ("evidence", evidence_id)))
            edges.add(
                edge("located_in", ("evidence", evidence_id), ("content_artifact", artifact_id))
            )
            artifacts.add(artifact_id)
    edges |= expected_artifact_chain(url, artifacts)
    return edges


def expected_artifact_chain(url: str, artifacts: Iterable[UUID]) -> set[Edge]:
    edges: set[Edge] = set()
    for artifact_id in artifacts:
        ((version_id, document_id),) = _rows(
            url,
            "SELECT a.document_version_id, v.source_document_id FROM content_artifact a "
            "JOIN document_version v ON v.id = a.document_version_id WHERE a.id = %s",
            artifact_id,
        )
        edges.add(
            edge("artifact_of", ("content_artifact", artifact_id), ("document_version", version_id))
        )
        edges.add(
            edge("version_of", ("document_version", version_id), ("source_document", document_id))
        )
    return edges


def expected_review_history(url: str, assertion_ids: Iterable[UUID]) -> set[Edge]:
    """Stored-basis edges for decisions, attempts and reservations on the ancestry."""
    edges: set[Edge] = set()
    for assertion_id in assertion_ids:
        for decision_id, child in _rows(
            url,
            "SELECT d.id, d.corrected_assertion_id FROM review_decision d "
            "JOIN review_item i ON i.id = d.review_item_id WHERE i.assertion_id = %s",
            assertion_id,
        ):
            edges.add(
                edge("reviews", ("review_decision", decision_id), ("assertion", assertion_id))
            )
            if child is not None:
                edges.add(
                    edge(
                        "created_assertion", ("review_decision", decision_id), ("assertion", child)
                    )
                )
            for (reservation_id,) in _rows(
                url,
                "SELECT id FROM learning_candidate_reservation WHERE review_decision_id = %s",
                decision_id,
            ):
                edges.add(
                    edge(
                        "reserved_learning",
                        ("review_decision", decision_id),
                        ("learning_reservation", reservation_id),
                    )
                )
        for (attempt_id,) in _rows(
            url,
            "SELECT id FROM review_submission_attempt WHERE original_assertion_id = %s",
            assertion_id,
        ):
            edges.add(edge("reviews", ("review_attempt", attempt_id), ("assertion", assertion_id)))
    return edges


def _ancestry(url: str, assertion_id: UUID) -> list[UUID]:
    chain, current = [], assertion_id
    while current is not None:
        chain.append(current)
        ((current,),) = _rows(
            url, "SELECT original_assertion_id FROM assertion WHERE id=%s", current
        )
    return chain


def expected_version_edges(url: str, root_id: UUID) -> set[Edge]:
    """Stored-basis edges for a fact-version root (assembly plan Step 5): its own and
    its split ancestry's support/ending evidence and recorded decision, the direct
    changes into/out of the root with their endpoints (predecessor ancestry only),
    and `attested_by` for every included version that exposes attestation dates."""
    edges: set[Edge] = set()
    seeds: set[UUID] = set()
    artifacts: set[UUID] = set()

    def version(version_id: UUID, *, full: bool) -> None:
        ((refs_json, decision_id, split_of, contract, *attested),) = _rows(
            url,
            "SELECT evidence, review_decision_id, split_of_version_id, temporal_contract, "
            "attested_from_value, attested_through_value, attested_to_value "
            "FROM canonical_fact_version WHERE id=%s",
            version_id,
        )
        exposes = contract is not None and any(attested)
        if full or exposes:
            for kind, key in (("supported_by", "refs"), ("ending_evidence", "ending_refs")):
                for evidence_id in refs_json.get(key, []):
                    found = _rows(
                        url,
                        "SELECT assertion_id, artifact_id FROM assertion_evidence WHERE id=%s",
                        evidence_id,
                    )
                    if not found:
                        continue
                    ((assertion_id, artifact_id),) = found
                    edges.add(edge(kind, ("fact_version", version_id), ("evidence", evidence_id)))
                    edges.add(
                        edge(
                            "located_in",
                            ("evidence", evidence_id),
                            ("content_artifact", artifact_id),
                        )
                    )
                    artifacts.add(artifact_id)
                    if exposes:
                        edges.add(
                            edge(
                                "attested_by",
                                ("fact_version", version_id),
                                ("content_artifact", artifact_id),
                            )
                        )
                    if full:
                        seeds.add(assertion_id)
        if full and decision_id is not None:
            edges.add(
                edge(
                    "recorded_decision",
                    ("fact_version", version_id),
                    ("review_decision", decision_id),
                )
            )
            ((item_assertion,),) = _rows(
                url,
                "SELECT i.assertion_id FROM review_decision d JOIN review_item i "
                "ON i.id = d.review_item_id WHERE d.id=%s",
                decision_id,
            )
            seeds.add(item_assertion)
        if split_of is not None:
            edges.add(edge("split_of", ("fact_version", version_id), ("fact_version", split_of)))
            version(split_of, full=full)

    version(root_id, full=True)
    for change_id, source, target in _rows(
        url,
        "SELECT id, from_version_id, to_version_id FROM canonical_fact_change "
        "WHERE to_version_id=%s OR from_version_id=%s",
        root_id,
        root_id,
    ):
        for kind, endpoint in (("changed_from", source), ("changed_to", target)):
            if endpoint is None:
                continue
            edges.add(edge(kind, ("fact_change", change_id), ("fact_version", endpoint)))
            if endpoint != root_id:
                version(endpoint, full=False)
    ancestry = {a for seed in seeds for a in _ancestry(url, seed)}
    review = expected_review_history(url, ancestry)
    children = {target[1] for kind, _src, target in review if kind == "created_assertion"}
    everything = ancestry | {a for c in children for a in _ancestry(url, UUID(c))}
    edges |= review
    edges |= expected_source_chain(url, everything)
    edges |= expected_artifact_chain(url, artifacts)
    return edges


def snapshot(url: str, tables: Iterable[str]) -> dict[str, str]:
    """Byte-level digest of each table's rows in a stable order (S0006 AC1, S0003 AC7)."""
    digests = {}
    with psycopg.connect(url) as connection:
        for table in tables:
            rows = connection.execute(
                f"SELECT row_to_json(t)::text FROM {table} t ORDER BY row_to_json(t)::text"
            ).fetchall()
            digests[table] = hashlib.sha256("\n".join(r[0] for r in rows).encode()).hexdigest()
    return digests


def count(url: str, sql: str, *params: Any) -> int:
    return _rows(url, sql, *params)[0][0]


@asynccontextmanager
async def provenance(engine: Any, policy: Any):  # type: ignore[no-untyped-def]
    """The exported reader over one unit of work, exactly as `get_provenance_reader`
    composes it (no route registers it yet)."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), policy, policy.release
        )
        yield ProvenanceReader(SqlAlchemyProvenanceRepository(session), execution)


async def read_lineage(
    engine: Any,
    policy: Any,
    principal: Principal,
    root: tuple[str, UUID],
    anchor: tuple[ResourceType, UUID],
    *,
    trace_id: str | None = None,
):  # type: ignore[no-untyped-def]
    query = ProvenanceQuery(root=RecordRef(*root), anchor=ResourceKey(*anchor))
    async with provenance(engine, policy) as reader:
        return await reader.read(principal, query, trace_id=trace_id or f"f0009-{uuid4()}")


def review_client(engine: Any, principal: Principal, content_store: Any):  # type: ignore[no-untyped-def]
    app = create_app()

    async def session_override():  # type: ignore[no-untyped-def]
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[current_principal] = lambda: principal
    app.dependency_overrides[get_content_store] = lambda: content_store
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
