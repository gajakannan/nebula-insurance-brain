from __future__ import annotations

import pytest
from brain_interpretation.counters import CounterAccumulator, ReparseDetected, assert_no_reparse
from brain_interpretation.result import Counters


def test_assert_no_reparse_passes_when_zero() -> None:
    assert_no_reparse(Counters(conversion_calls=0, ocr_calls=0))


def test_assert_no_reparse_raises_on_conversion_call() -> None:
    with pytest.raises(ReparseDetected):
        assert_no_reparse(Counters(conversion_calls=1, ocr_calls=0))


def test_assert_no_reparse_raises_on_ocr_call() -> None:
    with pytest.raises(ReparseDetected):
        assert_no_reparse(Counters(conversion_calls=0, ocr_calls=1))


def test_counter_accumulator_records_model_calls() -> None:
    accumulator = CounterAccumulator()

    accumulator.record_model_call(prompt_tokens=100, completion_tokens=20)
    accumulator.record_model_call(prompt_tokens=50, completion_tokens=10)
    counters = accumulator.freeze()

    assert counters.model_calls == 2
    assert counters.prompt_tokens == 150
    assert counters.completion_tokens == 30
    assert counters.conversion_calls == 0
    assert counters.ocr_calls == 0
