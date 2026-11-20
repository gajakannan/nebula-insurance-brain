# Feature Code Review Report

Feature: F0008 — Bitemporal canonical facts, review remediation (run `2026-11-18-bce4909b`)

- Role: Code Reviewer
- Reviewer: Claude (Opus 5.5) / Code Reviewer
- Date: 2026-11-18
- Result: APPROVED
- Base: `origin/main` 339c920 (PR #55); head: `fix/F0008-review-remediation` working tree

## Summary

- Assessment: APPROVED
- Production files changed: 5
  - `engine/packages/brain-domain/src/brain_domain/facts.py`
  - `engine/packages/brain-temporal/src/brain_temporal/commit.py`
  - `engine/apps/api/src/brain_api/schemas/facts.py`
  - `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py`
  - (no route change)
- Contracts changed: `canonical-commit-response.schema.json`, `brain-api.yaml`
- Open issues: Critical 0, High 0, Medium 0, Low 0

## Disposition of the review findings

| Finding | Status | Verification |
|---|---|---|
| CR-F8-01 (Critical): commit response lacked S0002 AC7 metadata | Fixed | `CommitResult.version_temporals` is filled on the v1 path, in `fact_version_ids` order, for remainders and the new version. `CommitResponseOut.versions[]` carries each `temporal` block, and a legacy remainder entry omits it. A legacy pilot response keeps its three fields. S0007 AC6 is amended (operator, 2026-11-18). Tests: `test_s0002_ac7_commit_response_returns_temporal_metadata` (response equals the read's temporal block), `test_legacy_slot_reads_keep_pilot_behaviour` (pilot shape), `test_runtime_commit_response_validates_for_v1_and_legacy` (schema). |
| FR-ARCH-M1: legacy read returned `"temporal": null` | Fixed | A wrap `model_serializer` omits `temporal` when absent. The legacy test now asserts absence; the old test had asserted `None`. |
| QE-M1: S0004 AC1 "no audit row" | Amended, with a test | AC1 reworded (operator, 2026-11-18). The race test asserts that failed decisions equal the losers, and that there are exactly two successes. |
| FR-ARCH-L2: lineage not bound to its slot | Fixed | Migration 0015 adds a BEFORE INSERT trigger with a refusing preflight and a downgrade that drops only its own objects. Tests: `test_fr_arch_l2_split_lineage_cannot_cross_slots`, `test_0015_preflight_refuses_cross_slot_lineage_and_cycles_cleanly`. |
| FR-ARCH-L1: ADR prose | Fixed | ADR-0078 D4 (clear semantics) and D5 (three source timestamps plus a new acceptance) now match the code and the ACs. |
| PM-M1, PM-L1, PM-L2, SEC-L1, QE-L1 | Fixed | F0018 README and KG shard handoff; S0005 deferral note; `prior-run-errata.md`; STATUS date; raw repeat and no-DB gate outputs kept. |

## Pattern Compliance

- The serializer omits only fields that the contract marks as absent; it does not apply a global `exclude_none`, so pilot fields such as `valid_end: null` keep their meaning.
- `CommitResult.version_temporals` defaults to `()`, so legacy callers and the in-memory fake are unaffected.
- Migration 0015 is `SECURITY INVOKER` with a pinned `search_path`. Its trigger name sorts after 0014's insert guard, so the existing error precedence holds.

## Acceptance Criteria

All 46 ACs as amended (S0004 AC1, S0007 AC6) have observed evidence (`test-execution-report.md`).

## Recommendation

APPROVE.
