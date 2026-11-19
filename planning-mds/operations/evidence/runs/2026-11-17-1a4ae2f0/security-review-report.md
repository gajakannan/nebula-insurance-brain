# Feature Security Review Report

Feature: F0008 — Bitemporal canonical facts (run `2026-11-17-1a4ae2f0`)

- Role: Security Reviewer
- Reviewer: Claude (Opus 5.5) / Security
- Date: 2026-11-17 (DAST and verdict finalized 2026-11-18)
- Result: PASS WITH RECOMMENDATIONS

## Summary

- Assessment: PASS WITH RECOMMENDATIONS
- Findings: Critical 0, High 0, Medium 0, Low 2 (SEC-F8-01 fixed; SEC-F8-02 deferred to F0018/F0026), Informational 2

## Scope

The Phase B risk list:

- attestation-date disclosure (T-08);
- close-only triggers under application roles;
- non-disclosing refusals;
- revoked-grant historical reads.

Also in scope:

- the new request parsing (zone names, bounds);
- the 23P01 mapping;
- the four scan classes.

## Control Checks

| Control | Result | Evidence |
|---|---|---|
| Authorization before any reason (commit) | PASS. `fact_slot:commit` and the source READ decisions are taken in `mutate` before the operation runs. Every temporal reason is raised inside the operation, after the F0006 source check. | `test_temporal_reads.py::test_d4_committer_must_read_every_attesting_document`; unit `test_d8_source_refusal_precedes_a_temporal_refusal` |
| T-08 at commit: no date of an unreadable document is revealed | PASS. The attesting documents (evidence and ending evidence) now join the same-UoW READ checks even for legacy evidence. A restricted document gives the non-disclosing 404 for both a matching and a mismatching `expected_attestation`, with nothing written. | same test |
| T-08 at read: attestation dates disclosed only with READ on the documents | PASS. Whole-read 404, never a redacted answer (D4, SEC-F7-02). | `test_d4_attestation_dates_of_unreadable_documents_are_not_disclosed` |
| Validity-unknown discloses no value | PASS. `FactValidityUnknown` carries no `value` (schema R03, read tests B/C, EX-SEM-004). | `test_temporal_reads.py`, `test_contract_examples.py` |
| Historical reads under current grants (ADR-0053) | PASS. A revoked reader is denied at every coordinate, including ones before the revocation, and the body matches a non-existent slot apart from volatile fields. | `test_s0006_ac7_*` |
| Immutability whatever the client role | PASS. Proven as the database owner role: every non-recorded column UPDATE, reopen, move, DELETE and TRUNCATE is refused, and `canonical_fact_change` is append-only. The functions are `SECURITY INVOKER` with a pinned `search_path`. No `SECURITY DEFINER`, `BYPASSRLS`, role or grant is added. | `test_temporal_immutability.py`; migration snapshot of `role_table_grants` and `pg_roles` unchanged |
| Envelope backstop and cross-scope rows | PASS | `test_s0004_ac5_*`, `test_s0004_ac6_*` (including the split-lineage self-FK) |
| Input validation | PASS. Zones come from an allowlist of real IANA keys with a 64-character cap, so no file path or abbreviation (such as `../../etc/passwd` or `CDT`) is accepted. Malformed instants are 400s with a generic message. 422 responses carry the code only. | `test_bounds.py` |
| Error leakage | PASS after the fix. See SEC-F8-01. | `test_other_integrity_errors_do_not_echo_database_text` |
| Audit of mutations and refusals | PASS. Each winning commit writes one succeeded decision. Each refusal writes a failed decision and no fact, change, commit or outbox row. Persisting a per-refusal reason code is deferred to F0018 (G0 reconciliation 5, ADR-0078 D8 note). | `test_s0005_ac3_*`, `test_s0004_ac1_*` |
| Secrets/config | PASS. No secret, environment variable or credential is added. | gitleaks |

## Scan Verdicts (`security_scans{}`)

| Class | Ran | Result | Artifact | Verdict |
|---|---|---|---|---|
| dependency | yes | clean: 35 locked packages, 0 known vulnerabilities; F0008 changes no dependency | `artifacts/security/dependency-engine.json` | Accepted |
| secrets | yes | clean: gitleaks found no leaks in the 50 changed paths | `artifacts/security/secrets/secrets-gitleaks-20261117-052326.sarif` | Accepted |
| sast | yes | 7 findings, all `python.sqlalchemy.security.audit.avoid-sqlalchemy-text` in migration 0014. Each `text()`/`op.execute` interpolates only module constants (table, column, constraint and trigger names, and the envelope predicate) and takes no request or row data. This is the same pattern as migration 0013. Triaged as false positives. | `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` | Accepted (triaged) |
| dast | yes | clean: ZAP API scan of the booted `brain_api` OpenAPI, FAIL-NEW 0, WARN-NEW 0, PASS 113 | `artifacts/security/dast/api-scan.json` (`api-scan.html`, `zap.out`, `run-dast.sh`, `run-dast.log`) | Accepted |

The first SAST attempt (`sast-semgrep-20261117-052012.*`; its empty, invalid-root SARIF was deleted at the operator's request on 2026-11-18, and its `commands.log` entry is kept as append-only history) and the first gitleaks attempt (`…-052305.*`) are superseded. The SAST attempt failed with an invalid scanning root, because zsh does not word-split a variable. The gitleaks attempt recorded no exit code, because `docker.exe` read the rest of the script from stdin. Both scans were re-run, and the `052326` artifacts are the record.

**DAST:** The first attempt was blocked: the auto-mode safety classifier refused to start a local test server on `0.0.0.0`. The operator approved the scan on 2026-11-18. `run-dast.sh` then:

1. booted `brain_api` with `uvicorn` on port 8768 against an owned throwaway database at head;
2. probed reachability from a container, with `host.docker.internal` returning 200;
3. ran the ZAP API scan from the OpenAPI document;
4. stopped the server (the port was confirmed closed) and dropped the database.

No credentials are configured, so protected routes are exercised on the unauthenticated 401 path plus request validation. F0008 adds no authentication surface. Its authorization behaviour is proven at the HTTP layer by the integration suites above.

## Findings

- Critical: none
- High: none
- Medium: none
- Low:
  - **SEC-F8-01 (fixed).** The commit route echoed `str(IntegrityError)` in the 409 `concurrent_commit` detail. PostgreSQL CHECK and trigger messages can include "Failing row contains (…)" with the row's values. The detail is now null. Regression test added.
  - **SEC-F8-02 (deferred, non-blocking).** In local and CI topology the API connects as `brain`, a superuser. A superuser can set `session_replication_role = replica` and skip the D5 triggers, which is exactly how the test cleanup works. The triggers hold for every non-superuser role. Running the application as a non-superuser role is F0018 (application role and RLS) and F0026 (production host). Severity is Low because the application never issues that statement and the condition already exists for every 0007 trigger.
    - Owner: Architect with DevOps.
    - Follow-up: F0018 application role.
    - PM acceptance is requested at G4.
- Informational:
  - **SEC-F8-I1.** A validity-unknown read reveals that some version exists in that window, and its attestation dates, under READ on the slot and on the attesting documents. It does not reveal the value or any absence-scope artifact. This is consistent with the approved ADR-0078 D9.
  - **SEC-F8-I2.** The tzdata versions differ (PostgreSQL 2025b, Python 2026e). The database is authoritative and fails closed. See CR-I3.

## Recommendations

Only one deferred item remains. It does not block closeout: the operator accepted it at G4 on 2026-11-18 (`gate-decisions.md`), and the PM acceptance line is in `pm-closeout.md`.

- [low] SEC-F8-02 — owner: Architect + DevOps; follow-up: F0018 non-superuser application role (and F0026 production host)

## Verdict

APPROVE. There is no Critical or High finding, and all four scan classes ran clean or were triaged.

- **SEC-F8-01** (Low) is fixed and re-verified.
- **SEC-F8-02** (Low) is deferred, non-blocking:
  - Owner: Architect with DevOps.
  - Follow-up: the F0018 application role.
  - It needs named PM acceptance at G4 for the `WITH RECOMMENDATIONS` verdict to close.
