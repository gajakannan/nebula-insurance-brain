# Security Review Report — F0007-factslot-model run 2026-11-09-81798e61

## Scope

- Feature ID: F0007; remediation of the seven independently reported audit findings.
- Run ID: 2026-11-09-81798e61; baseline fa8fc1d; branch fix/f0007-review-remediation.
- Date: 2026-11-10.
- Reviewer: Codex / independent Security Reviewer, not an implementation or test author.
- Independent source review, fresh raw scans and final engine runtime evidence were inspected before this verdict. No implementation or original completion evidence was modified by this reviewer.

## Reviewed Surfaces

Current raw diff/source in `brain_security/execution.py`, FactSlot answer policy/read helpers/service, HTTP facts route, bounded decimal normalization, new migration0013 and its original0012 predecessor; member/numeric, grouped-read and real PostgreSQL migration/authorization regressions; current authority persistence/revocation implementations; declared runtime preflight and manifest. The source assessment and exact line references are in `artifacts/security-source-review.md`. Relevant commands/raw excerpts use `artifacts/security-review-*.txt`.

## Threat Boundary

Verified principals cross the existing HTTP/application boundary to read slots and their evidence scopes or commit PRESENT values. The execution facade is the authority/audit boundary; PostgreSQL's current-authority locks and composite ownership keys are the persistence boundary. Migration operators may inspect malformed identities but do not gain an automatic evidence-repair path. No new identity, permission, endpoint, producer, external call or RLS bypass is introduced. STRIDE and all ten review dimensions are assessed in `artifacts/security-source-review.md`.

## Auth / Authz

Primary slot authorization precedes a single private payload load. `additional_reads(payload)` derives the exact returned scope, READ-authorizes it under the same UoW, rechecks primary/dependency decisions and retains current authority locks until the final commit. Scope denial remains a sanitized denial; no scope pages/blocks leave early. The PostgreSQL regression proves supported revocation waits for the grouped read's authority lock, then the subsequent read denies. New member mismatch validation follows existing evidence eligibility/entity-KB checks inside the already authorized commit path. The name display hook only returns PRESENT name fields, with existing per-slot READ enforcement.

## Validation

Canonical member equality now rejects a different member rather than changing its immutable identity. Decimal raw input and canonical output share a 64-character total bound including sign/point; size is computed before exponent-sized allocation. New0013 requires the complete legacy-or-v1 identity shape to be TRUE and rejects missing required fields, while retaining composite tenant/KB ownership and immutable identities. Existing malformed rows cause migration refusal with count and limited IDs; no data is deleted, fabricated or silently normalized.

## Audit / Logging

Grouped-read primary/dependency decisions share one final durable commit before return. Denied/failed dependencies audit the established failed-primary/denied-resource outcomes. Audit failure returns no private payload. Creation/commit audit semantics remain unchanged. Migration refusal reports counts and at most10 slot IDs, never fact values or excerpts.

## Secrets / Config

No new runtime secret, role, grant, public port or authentication setting was observed. Existing synthetic local database configuration is test infrastructure. The validation container mounts current product source read-only and writes only evidence outputs. Fresh secrets SARIF was inspected and contains zero results.

## Scan Disposition

The final manifest records all four classes as executed with resolvable raw artifacts and no waiver. Fresh scan scope includes the current protected-read, member, decimal and0013 source, and the two inherited post-CI Neuron test fixes omitted from the original inventory. A byte comparison confirms these files in the scanner snapshot equal current source (`artifacts/security-review-scan-scope.txt`). No prior-run artifact is substituted for a fresh result.

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|---|---|---|---|
| dependency | Yes |57 packages, zero vulnerability entries in this fresh audit result | `artifacts/security/dependency-engine.json` |
| secrets | Yes |Zero SARIF results | `artifacts/security/secrets.sarif` |
| sast | Yes |Two audit-rule results; both independently classified false positives, zero actionable findings | `artifacts/security/sast.sarif`; full disposition `artifacts/security/sast-triage.md` |
| dast | Yes |ZAP console113 PASS, zero WARN/FAIL; raw JSON includes two risk-code-0 informational alert types | `artifacts/security/dast/api-scan.json`; console `artifacts/security-dast.txt` |

SAST emits `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text` at migration0013 lines70 and73. Both SQL strings interpolate only `invalid`, defined at line69 from the literal module constant `IDENTITY_SHAPE` (lines43–61). No request, environment, command-line or database value enters either SQL string. One statement counts malformed rows and the other selects limited IDs for refusal; returned row values never become SQL. These are false positives for this static migration, not mitigated vulnerabilities or deferred recommendations. Raw results are retained and the manifest correctly says `findings`; no suppression was added. Detailed source trace and reasoning: `artifacts/security/sast-triage.md`.

DAST covers the fresh owned API's unauthenticated OpenAPI reach, including existing credential-denial/validation paths. It does not prove authenticated authorization. That boundary is covered here by source inspection and container/PostgreSQL HTTP/facade regressions, including exact selected scope and real revocation locking. The two risk-code-0 alert types identify client-error responses and session-management responses; neither is a WARN/FAIL result. Scanner versions/image identifiers and invocation output are preserved by QE; this report does not claim that a clean result proves absence of all vulnerabilities.

## OWASP Top 10 Coverage

| Category | Source assessment | Evidence / limit |
|---|---|---|
| A01 Broken Access Control | Corrected | Exact payload scope and current locks; denial/audit order; real PostgreSQL revocation regression |
| A02 Cryptographic Failures | Unchanged | No changed cryptographic or key-management path |
| A03 Injection | No new issue | Parameterized runtime access; migration interpolates static constants only |
| A04 Insecure Design | Corrected scoped gaps | Member identity and bounded canonicalization; no producer/permission expansion |
| A05 Security Misconfiguration | No new issue | No RLS bypass, grant or SECURITY DEFINER path; runtime preflight inspected |
| A06 Vulnerable / Outdated Components | No new issue in inspected scope | No runtime dependency change; fresh57-package dependency scan reports zero vulnerability entries |
| A07 Identification & Authentication | Unchanged | Existing verified-principal flow retained |
| A08 Software & Data Integrity | Corrected | Complete TRUE identity guard; immutable0012, refusal-only preflight, zero-write rejections |
| A09 Security Logging & Monitoring | No new issue | Single success audit commit; durable failure/denial behavior; no values in migration inventory |
| A10 Server-Side Request Forgery | Unchanged | No new external request target or call |

## Findings

No open security finding established: Critical0, High0, Medium0, Low0. Prior FR-M1 and FR-M2 are resolved in inspected source/regressions; FR-C1 and FR-H2 security implications are also addressed. The two SAST results are false positives with the explicit source-based disposition above. The existing downstream ownership of restriction re-derivation/RLS (F0018) and envelope database enforcement (F0008) remains explicit and is not expanded by this remediation.

Raw `artifacts/test-results/remediation.xml` independently confirms319 tests, zero failures/errors/skips, including exact selected scope, current grant revision, audit failure, member identity, numeric boundaries and real revocation locking. Summary: `artifacts/security-review-raw-runtime.txt`. The final full-engine XML independently confirms868 tests, zero failures/errors/skips (`artifacts/security-review-final-runtime.txt`, raw `artifacts/test-results/engine-full-final.xml`). Earlier backup/restore run failures were corrected in validation runtime setup before that final passing run; the reviewer does not substitute their earlier failing artifacts for the final result. Strict security planning-artifact check passes (`artifacts/security-review-artifact-audit.txt`). No broad scanner or full-runtime execution was duplicated by this reviewer.

## Recommendation Disposition

No open recommendation, risk waiver or mitigation acceptance is required for this scoped Security verdict. Fresh scan handoff was verified against raw outputs and current source; SAST false positives are retained with explicit triage. QE/DevOps and the primary coordinator own remaining non-security lifecycle evidence, Neuron regression disposition, tracker/signoff and final operator approval. This Security PASS does not itself authorize deployment, closeout or formal acceptance of Proposed ADRs.

## Result

PASS
