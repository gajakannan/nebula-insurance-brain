# Feature Security Review Report

Feature: F0008 — Bitemporal canonical facts, review remediation (run `2026-11-18-bce4909b`)

- Role: Security Reviewer
- Reviewer: Claude (Opus 5.5) / Security
- Date: 2026-11-18
- Result: PASS WITH RECOMMENDATIONS

## Summary

- Assessment: PASS WITH RECOMMENDATIONS
- New findings in this change set: 0
- Carried: SEC-F8-02 (Low, deferred, operator-accepted at the prior G4). Its F0018 handoff is now recorded on the F0018 side.

## Control Checks

| Control | Result | Evidence |
|---|---|---|
| Commit-response disclosure | PASS. `versions[].temporal` holds the temporal blocks of versions this commit wrote. The committer already passed READ on every attesting document (the prior T-08 control), so the response reveals no date the caller could not read. Remainder blocks repeat their predecessor's attestation; those documents belong to the same slot, under the same commit authorization. | `test_s0002_ac7_*`; `test_d4_committer_must_read_every_attesting_document` (still passing) |
| Legacy read shape | PASS. Omitting `temporal` changes no authorization path. | `test_legacy_slot_reads_keep_pilot_behaviour` |
| Lineage integrity | PASS. Migration 0015 refuses cross-slot `split_of_version_id` for every client role. | `test_fr_arch_l2_*`, `test_0015_*` |
| Losing-commit audit | PASS. Each loser leaves exactly one `failed` decision, which is the F0002 guarantee. | `test_s0004_ac1_racing_commits_*` |

## Scan Verdicts

| Class | Ran | Result | Artifact | Verdict |
|---|---|---|---|---|
| dependency | yes | clean: 35 packages, 0 vulnerabilities; `uv.lock` unchanged | `artifacts/security/dependency-engine.json` | Accepted |
| secrets | yes | gitleaks found 3 `generic-api-key` hits, all in `runs/2026-11-18-d34a095e/artifacts/review/initial-canonical-hashes.json` (lines 39, 76, 124). They are SHA-256 file digests keyed by paths containing "api". No secret; no hit in code. Triaged as false positives. | `artifacts/security/secrets/secrets-gitleaks-20261118-225256.sarif` | Accepted (triaged) |
| sast | yes | 3 `avoid-sqlalchemy-text` hits in migration 0015. Module constants only, the same pattern as 0013/0014. Triaged as false positives. | `artifacts/security/sast/sast-semgrep-20261118-225256.sarif` | Accepted (triaged) |
| dast | yes | ZAP API scan of the remediated `brain_api`: FAIL-NEW 0, WARN-NEW 0, PASS 113 | `artifacts/security/dast/api-scan.json` | Accepted |

## Findings

- Critical: none
- High: none
- Medium: none
- Low: SEC-F8-02, carried (see Recommendations)

## Recommendations

The single carried item does not block closeout. It was operator-accepted at the prior G4 (2026-11-18), it is now recorded in F0018's README and KG shard, and the PM acceptance line is in `pm-closeout.md`.

- [low] SEC-F8-02 — owner: Architect + DevOps; follow-up: F0018 non-superuser application role (and F0026 production host)

## Verdict

APPROVE.
