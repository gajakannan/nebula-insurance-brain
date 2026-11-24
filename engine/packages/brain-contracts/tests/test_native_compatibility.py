"""Fixed old-reader acceptance is separate from new portable conformance."""

from pathlib import Path

from scripts.contracts.native_compat_probe import run_cases


def test_native_datetime_number_and_version_boundaries_remain_compatible():
    root = Path(__file__).resolve().parents[4]
    results = run_cases(root / "scripts/contracts/native-cases.json")
    assert len(results) == 7
    assert all(result["matched"] for result in results), results
