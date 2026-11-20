# Feature Security Review Report

Feature: F0008 — Bitemporal canonical facts, second remediation (run `2026-11-19-8cfcd0ff`)

- Role: Security Reviewer
- Reviewer: Claude (Opus 5.5) / Security
- Date: 2026-11-19
- Result: PASS WITH RECOMMENDATIONS

## Summary

- Assessment: PASS WITH RECOMMENDATIONS
- SEC-F8-NEW-01 (High): fixed and re-verified.
- New findings: 0. Carried: SEC-F8-02 (Low, deferred to F0018).

## SEC-F8-NEW-01 analysis

Before this run, a remainder's `temporal` block repeated its predecessor's `attested_from`, `attested_through` and `attested_to`, and the commit response returned it. The commit READ-checked only the proposal's documents. A committer with `fact_slot:commit` and no READ on a predecessor's document could therefore learn that document's selected date, which breaks T-08.

The prior run's review wrongly judged this safe (`prior-run-errata.md`).

The fix follows ADR-0078 D4: deny the whole operation rather than return a redacted answer.

1. **Up front.** The documents behind the dates of every current temporal-v1 version that the proposal could split join the same-UoW READ checks. A denial makes `mutate` refuse with the standard 404, and the body is identical to the body for a missing slot (asserted).
2. **After the lock.** `disclosure_check` maps the returned predecessors' evidence to artifacts and requires each to be among the allowed READ decisions. Anything else can only be a version committed concurrently after step 1, so the commit gets a retryable 409 `stale_version` and returns no date.

## Control Checks

| Control | Result | Evidence |
|---|---|---|
| Unreadable predecessor document | PASS: 404 `not_found`, identical to a missing slot; no date in the body; zero rows written | `test_sec_f8_new_01_commit_refused_when_predecessor_dates_are_unreadable` |
| Readable predecessor | PASS: full `versions[]` with the predecessor's dates | same test |
| Non-overlapping proposal | PASS: no predecessor READ required, no predecessor date returned | `test_sec_f8_new_01_non_overlapping_commit_needs_no_predecessor_read` |
| Race | PASS: 409 `stale_version`, no date, zero rows written | `test_sec_f8_new_01_unchecked_predecessor_is_a_retryable_conflict` |
| Ordering | PASS: the check precedes every write | unit `test_sec_f8_new_01_disclosure_check_sees_dated_predecessors_before_any_write` |
| Earlier T-08 controls | PASS: unchanged; the full regression includes them | `test_d4_*` |

## Scan Verdicts

| Class | Ran | Result | Artifact | Verdict |
|---|---|---|---|---|
| dependency | yes | clean: 35 packages, 0 vulnerabilities; `uv.lock` unchanged | `artifacts/security/dependency-engine.json` | Accepted |
| secrets | yes | 5 `generic-api-key` hits, all in the review hash manifest (`2026-11-19-b21ec2de/artifacts/review/protected-input-hashes.json`): 194 SHA-256 values and no other strings. Triaged as false positives. | `artifacts/security/secrets/secrets-gitleaks-20261119-222657.sarif` | Accepted (triaged) |
| sast | yes | 0 findings | `artifacts/security/sast/sast-semgrep-20261119-222657.sarif` | Accepted |
| dast | yes | ZAP: FAIL-NEW 0, WARN-NEW 0, PASS 113 | `artifacts/security/dast/api-scan.json` | Accepted |

## Findings

- Critical: none
- High: none open (SEC-F8-NEW-01 fixed)
- Medium: none
- Low: SEC-F8-02, carried (see Recommendations)

## Recommendations

The single carried item does not block. It was operator-accepted, it is recorded on F0018, and the PM acceptance line is in `pm-closeout.md`.

- [low] SEC-F8-02 — owner: Architect + DevOps; follow-up: F0018 non-superuser application role (and F0026 production host)

## Verdict

APPROVE.
