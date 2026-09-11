from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from brain_interpretation.result import Counters, InterpretationResult, RunConfiguration
from brain_interpretation.runs import InMemoryRunRecorder, new_run_id


def _result() -> InterpretationResult:
    return InterpretationResult(
        run_id=new_run_id(),
        artifact_id=uuid4(),
        status="complete",
        entities=[],
        assertions=[],
        relationships=[],
        quality_signals={},
        warnings=[],
        failed_chunks=[],
        run_configuration=RunConfiguration(
            backend="openai_compatible",
            model_id="microsoft/Phi-4-mini-instruct",
            model_revision=None,
            endpoint_hash="a" * 64,
            prompt_hash="b" * 64,
            schema_hash="c" * 64,
            context_limit=4096,
            profile_id="gl-limits-a",
            profile_version="1",
        ),
        counters=Counters(),
        provenance_ledger_ref=None,
        created_at=datetime.now(UTC),
    )


def test_new_run_id_is_unique() -> None:
    assert new_run_id() != new_run_id()


def test_in_memory_recorder_appends_never_overwrites() -> None:
    recorder = InMemoryRunRecorder()
    first, second = _result(), _result()

    asyncio.run(recorder.record(first))
    asyncio.run(recorder.record(second))

    assert recorder.results == [first, second]
