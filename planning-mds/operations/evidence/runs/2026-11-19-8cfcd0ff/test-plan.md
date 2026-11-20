# Test Plan — F0008 second remediation (run 2026-11-19-8cfcd0ff)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-19

The prior plans (`../2026-11-17-1a4ae2f0/test-plan.md` and `../2026-11-18-bce4909b/test-plan.md`) still apply. Every case is re-run in full.

## Additions

| Finding | Test |
|---|---|
| SEC-F8-NEW-01 | `test_temporal_reads.py::test_sec_f8_new_01_commit_refused_when_predecessor_dates_are_unreadable`: 404, body identical to a missing slot, no date, zero rows; a reader with access gets the full `versions[]` |
| SEC-F8-NEW-01 | `test_sec_f8_new_01_non_overlapping_commit_needs_no_predecessor_read`: the window limits the check |
| SEC-F8-NEW-01 | `test_sec_f8_new_01_unchecked_predecessor_is_a_retryable_conflict`: race path, 409 `stale_version`, zero rows |
| SEC-F8-NEW-01 | `test_temporal_service.py::test_sec_f8_new_01_disclosure_check_*` (ordering before any write; undated predecessors skipped) |
| CI coverage gate | `apps/api/tests/test_facts_temporal_helpers.py`: window, instant and ending-ref helpers; keeps the no-DB `brain_api` gate ≥ 80% |
