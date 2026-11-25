# Code Review Report — F0009-provenance-and-human-correction-lineage run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / Code Reviewer
Date: 2026-11-24
Base: `3729dbee528ce27a3a939b24abe5b8efca3aeb9e`; head: working tree of `feature/f0009-provenance-and-human-correction-lineage`

## Summary

- Assessment: APPROVED
- Files reviewed: 15 changed or new runtime source files (including migration 0016), 13 test and fixture files, and the CI workflow, contract inventory and case files.
- Issues found: 0 critical, 0 high, 0 medium, 1 low (closed during review).

## Reviewed Files

- **Domain:** `brain_domain/provenance.py`.
- **Application:** `brain_provenance/{__init__,ports,service}.py`.
- **Infrastructure:**
  - `brain_persistence/{provenance,provenance_models,lineage_contracts}.py`;
  - `models.py` (marker column, owner key);
  - `repositories.py` (`save_decision` timestamp; the reservation, attempt, lock and source-key changes; the refusal audit).
- **Review service:** `brain_review/decisions.py` (stale retention, reservation call, `preflight_batch`, `RefusedBatch`, `ReviewLineageChanged`).
- **Security:** `brain_security/execution.py` (`prepare_reads`, `_authorize_more`, the post-load recheck).
- **API:** `routes/reviews.py` (preflight, post-lock source recheck, refusal recording, 422/503 mapping), `schemas/review.py` (legacy stale masking), `deps.py` (`get_provenance_reader`).
- **Migration:** `migrations/versions/0016_f0009_provenance_hooks.py`.
- **Contracts and CI:** `scripts/contracts/sources.yaml`, `cases.json`, `case-provenance.json`, `planning-mds/schemas/provenance-result-v1.schema.json`, `.github/workflows/ci-gates.yml`.

## Validation Artifacts

[test-execution-report.md](test-execution-report.md), [coverage-report.md](coverage-report.md), [deployability-check.md](deployability-check.md), [g2-self-review.md](g2-self-review.md), `artifacts/security/scan-summary.json`, and the CR-L1 re-verification in [g3-cr-l1-fix.txt](artifacts/test-results/g3-cr-l1-fix.txt).

## Severity-Ranked Findings

### CR-F0009-L1 (low) — CLOSED: Assertion-root discovery expanded the closure before proving the anchor.

`_Walker.assertion_root` walked evidence, artifacts and review history, then checked that the anchor lies on the root's chain. Nothing leaked: an owner mismatch already refused, non-disclosingly, before materialization. But metadata of an unrelated lineage was read before the association was proven, contrary to plan Step 4.3's order.

Fix: walk only the ancestry, prove the anchor, then expand. Re-verified: the F0009 integration suites pass 30/30 ([g3-cr-l1-fix.txt](artifacts/test-results/g3-cr-l1-fix.txt)); ruff and format are clean.

### Informational notes (no action required)

- **Query count.** Discovery issues one metadata query per visited row (N+1). Fixed limits bound it (256 links, 2048 records, 8192 edges), and there is no route today. F0020 should measure it before any public exposure; the plan already assigns F0020 public provenance APIs.
- **Audit meaning of a refused batch.** The facade records the `review_task:annotate` authorization as `succeeded`, because authorization did succeed. The business refusal is the separate `review_submission_refused` / `failed` event that carries the attempt id. This matches the plan's Step 3.5 audit design.
- **Naive timestamps.** Naive F0001 timestamps are serialized as UTC instants. This depends on the established `audit_timestamp` and UTC-database convention, which `brain_f0009` and CI follow.

## Recommendations

None blocking. Merge after G4.

## Vertical-Slice Completeness

- [x] Backend complete. The internal reader and factory are exported; the review route behavior is complete. No new endpoint is in scope.
- [x] Frontend: not applicable. Only regenerated contract copies; lint, Vitest and build pass.
- [x] AI layer: not applicable.
- [x] Tests complete: unit, PostgreSQL integration, migration, contract conformance, installed smoke.
- [x] Can be deployed independently: additive migration with a guarded downgrade; no new service.

## AC / Test Adequacy

The 41 ACs map to named passing tests ([test-plan.md](test-plan.md)). Expected edges are derived independently with stored-basis SQL, and the reader agrees edge-for-edge on all five EX-PROV examples. Negative, race (concurrent commit; source-set drift), rollback (injected reservation failure), limit+1 and non-disclosure cases are present. Every persistence assertion is a fresh-session query.

## Architecture Compliance

- [x] Clean architecture. Domain carriers do no I/O. The application depends inward only. Persistence implements the port. There is no brain-review ↔ brain-provenance cycle: the reservation methods stay on the review repository port.
- [x] SOLID. The facade extension is additive and opt-in, so existing callers and signatures are unchanged.
- [x] SOLUTION-PATTERNS: ProblemDetails, durable authorization audit, append-only history, structural tenant/KB ownership.
- [x] Test coverage ≥ 80% for feature logic: 94.41% of changed lines.
- [x] Shared semantics. The schema nullability fix and the attempt-authorization binding are Architect-recorded (g2-self-review.md, test-execution-report.md). No canonical vocabulary or authority semantics changed.

## Coverage Verification

Changed executable lines: 912 of 966 covered (94.41%). Per-package gates: brain_provenance 100%, brain_domain 91.11%, brain_review 98.73%, brain_security 93.09%.

## Result

Result: APPROVED
