# Code Review Report — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

**Reviewer:** Code Reviewer pass
**Date:** 2026-09-10

## Summary

- **Assessment:** APPROVED WITH RECOMMENDATIONS
- **Files reviewed:** 225 changed (per `scm.diff_artifact`; full diff `main...8eaee93,9de0c88,2bf69b4`)
- **Issues found:** 0 blocking; 3 medium, 2 low (see below)

## Reviewed Files

Full changed-file set: `git diff 33c8df0...17f752b --stat` (225 files, +21,432/-233).
Focused review depth on the architecturally load-bearing surfaces:

- `engine/packages/brain-temporal/src/brain_temporal/commit.py` (bitemporal commit algorithm)
- `engine/packages/brain-persistence/src/brain_persistence/{models,repositories}.py`
- `engine/packages/brain-security/src/brain_security/{authorization,verification,principals}.py`
- `engine/packages/brain-review/src/brain_review/{decisions,evidence}.py`
- `engine/apps/api/src/brain_api/{deps,errors,routes/*}.py`
- `engine/migrations/versions/0001-0003*.py`
- `scripts/ops/{backup.sh,restore.sh,verify_citations.py}`
- All six updated ADRs

## Validation Artifacts

`test-execution-report.md`, `coverage-report.md`, CI run `34554563562` (all green).

## Severity-Ranked Findings

No blocking findings.

- [medium] `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_adapter.py`'s live-only code paths (95 statements, 25% covered offline) have no offline-mockable unit test — coverage depends on a reachable vLLM endpoint at test time — owner: ai-engineer; follow-up: F0002.
- [medium] The scanned/OCR fixture path in `neuron/tests/integration/test_parse_once_reinterpret.py` is exercised only by a manual, one-off check recorded in ADR-0040, not by an automated assertion — owner: ai-engineer; follow-up: F0002.
- [medium] `BRAIN_GRANT_CACHE_SECONDS` is documented (S0002 onward) but has no cache implementation behind it — `PrincipalResolver.memberships()` queries Postgres on every request. This is a deliberate, disclosed decision (see `STATUS.md` Deferred Non-Blocking Follow-ups and ADR-0049's Results), not an oversight, but flagged here so a future cache implementation is measured against the 12.41ms baseline already recorded rather than assumed necessary — owner: architect; follow-up: F0002/F0026 if load requires it.

## Non-Blocking Recommendations With Owner/Follow-up

- [low] `engine/apps/api/routes/content.py`/`reviews.py`/`facts.py` have lower line coverage (73–87%) than the rest of the API layer, concentrated in infrastructure-failure exception branches — owner: quality-engineer; follow-up: F0021 or F0002, whichever adds broader negative-path API tests.
- [low] No Playwright E2E coverage for the Review Panel yet (11 Vitest/Testing-Library component tests only) — already tracked in `STATUS.md`; owner: quality-engineer; follow-up: F0021.

## Vertical-Slice Completeness

Each story is a genuine vertical slice for its proof scope: domain dataclasses →
application service → persistence adapter → API route → live test, end to end, for
facts (S0005), reviews (S0004), and content (S0003). No layer is stubbed. The one
explicitly incomplete seam — a `CORRECT` review decision does not yet call
`CanonicalCommitService.commit()` — is disclosed in ADR-0044's Results as F0002's
integration, not silently left dangling; the review/commit *boundary* itself (a reviewer
cannot commit) is what this feature proves, and that boundary is fully wired.

## AC / Test Adequacy

Every acceptance criterion listed in `test-plan.md`'s Story-to-AC Mapping has a named
test. No AC-without-test pairs found. One test-without-explicit-AC case: the "same
subject, different issuer" test in `brain-security/tests/test_principals.py` was added
during S0006/S0007 to close a real gap discovered while settling ADR-0049 rather than
being pre-specified as a numbered story AC — a legitimate strengthening, not scope creep.

## Architecture Compliance

- Clean/ports-and-adapters boundaries are respected throughout: `brain_domain` stays pure
  dataclasses with no I/O; `brain_persistence` is the only package touching SQLAlchemy;
  `brain_api` wires ports to adapters via FastAPI `Depends()`.
- `brain-temporal`'s `CanonicalCommitService` takes a `FactCommitRepository` protocol, not
  a concrete SQLAlchemy type — proven independently against an in-memory fake (algorithm
  correctness) and against live Postgres (constraint enforcement), which is the intended
  separation of concerns for this kind of database-level guarantee.
- One deviation from the original architecture proposal, disclosed rather than silent:
  ADR-0058's evidence locator ships as a single `nebula:BoxSelector` instead of the
  proposed W3C multi-selector model. Recorded as an ADR amendment with the narrower scope
  explicit — reviewed and accepted as the right v0.1A trade-off given the PDF-only proof
  corpus this feature actually has.
- No new cross-layer dependency violations found (`brain_domain` imports nothing from
  `brain_persistence`/`brain_security`/etc.; `neuron/` packages never import from
  `engine/`).

## Coverage Verification

`coverage-report.md`'s percentages were re-derived independently by re-running each
per-package command during this review (not merely copied) — all match.

## Result

APPROVED WITH RECOMMENDATIONS
