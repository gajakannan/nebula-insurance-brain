from __future__ import annotations

from typing import Protocol
from uuid import UUID, uuid4

from brain_interpretation.result import InterpretationResult


def new_run_id() -> UUID:
    return uuid4()


class InterpretationRunRecorder(Protocol):
    """Append-only recording port for `semantic_interpretation_run` (+ `assertion`,
    `assertion_evidence`) rows. Never deletes or overwrites a prior run (F0001-S0003
    logic flow step 5)."""

    async def record(self, result: InterpretationResult) -> None: ...


class InMemoryRunRecorder:
    """Recorder used by the proof harness and unit tests; the engine-side SQLAlchemy
    recorder (`brain_persistence`) implements the same port for the real Postgres path."""

    def __init__(self) -> None:
        self.results: list[InterpretationResult] = []

    async def record(self, result: InterpretationResult) -> None:
        self.results.append(result)
