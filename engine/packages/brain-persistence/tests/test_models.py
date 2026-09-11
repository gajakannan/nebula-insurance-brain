from __future__ import annotations

from uuid import uuid4

import pytest
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    ContentArtifact,
    DocumentVersion,
    SemanticInterpretationRun,
    SourceDocument,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from sqlalchemy import select


@pytest.fixture
async def session_factory():
    engine = make_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=sqlite_test_tables())
    yield make_session_factory(engine)
    await engine.dispose()


async def test_full_row_graph_persists_and_relates(session_factory) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id, run_id, assertion_id = uuid4(), uuid4(), uuid4()

    async with session_scope(session_factory) as session:
        source = SourceDocument(
            tenant_id=tenant_id, knowledge_base_id=kb_id, source_sha256="a" * 64
        )
        session.add(source)
        await session.flush()

        version = DocumentVersion(source_document_id=source.id)
        session.add(version)
        await session.flush()

        artifact = ContentArtifact(
            id=artifact_id,
            document_version_id=version.id,
            artifact_sha256="b" * 64,
            page_count=1,
            extraction_status="complete",
        )
        session.add(artifact)
        await session.flush()

        run = SemanticInterpretationRun(
            id=run_id,
            artifact_id=artifact.id,
            profile_id="gl-limits-a",
            profile_version="1",
            status="complete",
            counters={"model_calls": 1},
            run_configuration={"model_id": "microsoft/Phi-4-mini-instruct"},
        )
        session.add(run)
        await session.flush()

        assertion = Assertion(
            id=assertion_id,
            run_id=run.id,
            subject_type="Policy",
            slot_type="each_occurrence_limit",
            value={"value": "$1,000,000"},
            model_confidence=None,
            interpretation_basis="EXPLICIT",
        )
        session.add(assertion)
        await session.flush()

        session.add(
            AssertionEvidence(
                assertion_id=assertion.id,
                artifact_id=artifact.id,
                block_id="text-2",
                page=1,
                bbox={"page": 1, "x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                char_start=555,
                char_end=564,
                precision="span",
            )
        )

    async with session_scope(session_factory) as session:
        fetched_run = await session.get(SemanticInterpretationRun, run_id)
        assert fetched_run is not None
        assert fetched_run.artifact_id == artifact_id

        evidence_rows = (
            (
                await session.execute(
                    select(AssertionEvidence).where(AssertionEvidence.assertion_id == assertion_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(evidence_rows) == 1
        assert evidence_rows[0].precision == "span"


async def test_source_document_identity_is_unique_per_tenant_kb_hash(session_factory) -> None:
    tenant_id, kb_id = uuid4(), uuid4()

    async with session_scope(session_factory) as session:
        session.add(
            SourceDocument(tenant_id=tenant_id, knowledge_base_id=kb_id, source_sha256="c" * 64)
        )

    with pytest.raises(Exception):  # noqa: B017 — IntegrityError subclass varies by dialect
        async with session_scope(session_factory) as session:
            session.add(
                SourceDocument(tenant_id=tenant_id, knowledge_base_id=kb_id, source_sha256="c" * 64)
            )
