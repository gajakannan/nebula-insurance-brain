# Independent Security Source Review — F0007 remediation

Reviewer: Codex / independent Security Reviewer. Date: 2026-11-10.
Candidate run: `2026-11-09-81798e61`; baseline `fa8fc1d`; branch `fix/f0007-review-remediation`.

## Source assessment

No new Critical/High/Medium/Low security finding established in the inspected remediation source. Final fresh scan handoff and current-source snapshot comparison were subsequently assessed; `security-review-report.md` records PASS with no open security findings. These notes preserve the original source assessment and its explicit evidence boundaries.

The reviewer did not author the implementation or tests and did not repair source or original evidence. Commands and exact source excerpts are logged under this run with `security-review-*` artifact names. Broad runtime suites and scanners are primary QE ownership and were not duplicated by this reviewer.

## Previously reported security-relevant findings

- **FR-M1, scoped-read revocation/selection race:** corrected at `brain_security/execution.py:356`–`:419`, `brain_factslots/service.py:115`–`:136`, and `brain_api/routes/facts.py:79`–`:96`. The primary resource is authorized/locked before private load; the payload is loaded once; the callback derives keys from that exact payload; all dependencies are READ-authorized and rechecked in the same UoW; decisions are audited and one commit completes before return. On denied primary no payload or scope discovery occurs. Scope denial uses the existing sanitized denial path. `brain_persistence/authx.py:159` takes the principal authority row FOR SHARE; supported revocation at `brain_persistence/grants.py:126` takes the corresponding update lock. The real PostgreSQL regression deliberately times out revocation while the protected read holds its transaction, then proves revocation succeeds and the following read is denied. A revocation after the completed protected transaction does not retroactively invalidate that already linearized response (ADR-0062).
- **FR-M2, expansion before size validation:** corrected at `brain_domain/fact_values.py:137` onward. Raw input length is bounded, digits are handled exactly, canonical length including sign/point is computed before zero padding, and output shares the schema's 64-character bound. Constructor and intermediate digit work remain bounded by the input limit. No new floating-point authoritative path was introduced. Current production registration remains the four NAME predicates; no new numeric public route or registry activation was added.
- **FR-C1, member identity consistency:** `brain_factslots/answers.py:102`–`:110` compares a PRESENT value's canonical member key with the immutable stored key under the pinned contract. Existing name-evidence eligibility and entity/KB checks run first (`:113`–`:123`), and outer commit source/authority checks remain before application details. Thus the new named mismatch rejection does not become a pre-authorization detail oracle. API regressions cover zero canonical rows on rejected entity/name/identifier values and preserve authorized canonical equivalents.
- **FR-H2, SQL NULL identity shape:** new migration `0013_f0007_identity_guard.py` leaves shipped0012 unchanged. It holds ACCESS EXCLUSIVE through the inventory and atomic constraint replacement, uses the complete legacy-or-v1 shape `IS TRUE`, explicitly guards required nullable fields, and refuses malformed preexisting identities using count plus at most10 slot IDs. It neither logs fact values nor deletes/fabricates identity evidence. Existing tenant/KB composite FKs and immutable identity triggers are retained. Downgrade restores the exact original0012 expression without altering rows. The stronger table lock is an explicit deployment/migration consequence, not a new tenant authority or bypass.

## Assets, actors and trust boundaries

| Asset / operation | Actor and boundary | Control inspected |
|---|---|---|
| Canonical FactSlot answer/scope read | Verified principal → API/application → current authority store | Primary and actual scope authorization inside one transaction; dependency denial before payload release |
| PRESENT member commit | Existing authorized service/reviewer → commit UoW → typed policy | Source READ + slot COMMIT authority precede typed/member/evidence checks; zero canonical effects on rejection |
| Slot identity rows | Application writer or migration operator → PostgreSQL | Composite owner keys, immutable identity trigger, complete new CHECK; refusal-only malformed-data preflight |
| Audit decisions | Execution facade → append-only audit store | Success only after durable commit; failures/denials take the established sanitized failure path |
| Numeric carrier | Typed application input → exact canonical representation | Common total-size limit, bounded work, deterministic canonicalization |

## STRIDE review

| Category | Assessment |
|---|---|
| Spoofing | No identity/grant or authentication behavior changed; existing verified-principal resolution retained |
| Tampering | Member-value equality and complete SQL identity shape close documented integrity gaps; migration refuses repair rather than rewriting evidence |
| Repudiation | Each primary/dependency decision is durably audited in the protected read's single transaction; failure paths release no successful result |
| Information disclosure | Actual returned scope is authorized under current locks; denial remains non-disclosing; preflight reports IDs/counts only |
| Denial of service | Decimal exponent expansion now bounded before allocation; migration's exclusive lock is explicitly scoped to operator rollout |
| Elevation of privilege | No roles, grants, permission rows, RLS bypass or SECURITY DEFINER path added |

## Ten review dimensions

| Dimension | Source assessment |
|---|---|
| Injection resistance | Runtime DB access remains parameterized;0013 SQL strings interpolate only static migration constants, not request data |
| Authentication robustness | No changed token/session/verifier path; existing current principal flow retained |
| Access control correctness | Primary+actual payload dependency decisions share locks/rechecks/commit; supported revocation serializes on principal authority |
| Sensitive data exposure | Scope details cannot leave before dependency authorization; no new response fields; migration inventory omits values |
| Security configuration | No changed CORS, cookies, grants, TLS or public ports; validation container uses current source read-only with evidence output writable |
| Component risk | No runtime dependency/lockfile change in remediation; fresh dependency/SAST/DAST/secrets artifacts subsequently reviewed in the final handoff section |
| Observability/auditability | Both successful grouped decisions and denied/failed outcomes are persisted through the existing facade; audit failure returns no private payload |
| Secrets/key management | No source secret addition seen; local synthetic DB fixture configuration remains existing test infrastructure; fresh secrets SARIF has zero results |
| Abuse/resilience | Bounded numeric work and identity consistency checks; no new endpoint/producer or permission introduced |
| Error/failure safety | Slot/scope denials map to existing sanitized responses; named 422 mismatch comes only after authority/evidence checks; migration refusal is atomic and does not repair data |

## Caller routing and limits

KG `lookup.py --defines AuthorizationExecution` and `--callers-only ...authorization-execution.read` were inspected, and raw source calls were checked because the graph is a routing aid. The changed HTTP and internal typed-answer callers pass payload-derived scope callbacks. The name display hook only returns PRESENT name fields (not absence-scope pages/blocks), and retains per-slot READ enforcement. The graph's new call/test bindings remain part of the primary Architect's normal reconciliation stage; no unprotected changed caller was established by source inspection.

The reviewer read the candidate manifest before selecting raw sources and exact relevant test/evidence paths. Raw `artifacts/test-results/remediation.xml` was independently parsed:319 tests, zero failures/errors/skips, including the member, numeric-boundary, exact selected-payload and real revocation-locking regressions. The summary is preserved in `artifacts/security-review-raw-runtime.txt`. Final full-engine XML was then independently parsed:868 tests, zero failures/errors/skips (`artifacts/security-review-final-runtime.txt`). Earlier backup/restore runtime failures were resolved before that final passing run. This review does not imply new deployment approval or formal acceptance of Proposed ADRs.

## Final scan handoff and SAST disposition

All four final manifest scan entries are populated with resolvable fresh artifacts and no waiver. Independent raw inspection (`artifacts/security-review-raw-scans.txt`) finds57 dependency packages with zero vulnerability entries, zero secrets SARIF results, two SAST audit-rule results and two risk-code-0 informational DAST alert types. The ZAP console reports113 PASS and zero WARN/FAIL. DAST is unauthenticated OpenAPI reach only; authenticated behavior is assessed through source and real PostgreSQL HTTP/facade regression evidence.

The SAST rule `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text` reports0013 lines70/73. Both SQL strings interpolate only `invalid`, defined from frozen literal `IDENTITY_SHAPE`, with no request, environment, command-line or database value becoming SQL text. They are false positives, not deferred vulnerabilities. The raw manifest correctly remains `result: findings`; no suppression or waiver was added. Full rationale is in `artifacts/security/sast-triage.md`. This section is the source-based disposition referenced by the manifest's triage_artifact.

Byte comparisons confirm the relevant protected-read/member/numeric/migration source and both inherited Neuron post-CI test files in the scan snapshot match current files (`artifacts/security-review-scan-scope.txt`). Final report: `security-review-report.md`; result PASS, with no open security recommendations.
