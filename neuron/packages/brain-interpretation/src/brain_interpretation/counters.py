from __future__ import annotations

from dataclasses import dataclass, field

from brain_interpretation.result import Counters


class ReparseDetected(Exception):
    """Raised when an interpretation run's counters show a Docling conversion or OCR
    call — reinterpretation must read the persisted artifact only (ADR-0003, F0001-S0003
    acceptance criterion 2)."""


def assert_no_reparse(counters: Counters) -> None:
    if counters.conversion_calls != 0 or counters.ocr_calls != 0:
        raise ReparseDetected(
            f"conversion_calls={counters.conversion_calls}, ocr_calls={counters.ocr_calls}"
        )


@dataclass(slots=True)
class CounterAccumulator:
    """Mutable accumulator used while an interpretation run is in progress; call
    `.freeze()` to get the immutable `Counters` recorded on the `InterpretationResult`.
    `conversion_calls`/`ocr_calls` are never incremented here — interpretation loads
    the persisted artifact and never re-parses; they exist on `Counters` only so the
    schema can express (and `assert_no_reparse` can verify) a value of zero."""

    model_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    _conversion_calls: int = field(default=0, repr=False)
    _ocr_calls: int = field(default=0, repr=False)

    def record_model_call(self, *, prompt_tokens: int, completion_tokens: int) -> None:
        self.model_calls += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens

    def freeze(self) -> Counters:
        return Counters(
            conversion_calls=self._conversion_calls,
            ocr_calls=self._ocr_calls,
            model_calls=self.model_calls,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
        )
