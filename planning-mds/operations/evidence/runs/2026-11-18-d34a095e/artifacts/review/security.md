### Security — security

Reviewer: Codex, independent feature-review lane. Scope: F0008's commit/read paths, evidence-date disclosure, migration invariants, errors, and the four manifest-cited security scan classes. Security verdict: **PASS WITH RECOMMENDATIONS**, with Critical 0, High 0, Medium 0, Low 1 new evidence-drift finding. This does not override the independent code/requirements completion blocker.

#### SEC-F8-L1 — Low — the manifest reports a clean SAST scan whose raw artifact contains seven triaged findings

- **Raw evidence:** `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:316` sets SAST `result: clean` at line 318. Its cited `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` has seven entries at `/runs/0/results`, all `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text`, pointing to migration 0014 lines 303, 309, 313, 343, 349, 353 and 357.
- **Judgment:** the raw calls interpolate module-owned table/predicate strings, not request values. Inspection of `engine/migrations/versions/0014_f0008_bitemporal_contract.py:59` and lines 299–359 agrees with the security report's false-positive triage. This is an evidence-description mismatch, not demonstrated SQL injection. `artifacts/review/security-raw-scan-summary.json` records the independent raw parsing.
- **Impact / scenario:** a consumer relying solely on `result: clean` loses the distinction between no scanner hits and reviewer-triaged hits. No exploitable application path was established from these seven hits.
- **Owner / route:** **security** owns the finding. Have the canonical evidence owner accurately record the accepted triage outcome under the allowed manifest schema, and keep the seven-hit raw artifact and reasoning. Target: next owning-role evidence correction/review; this audit does not invent an accepted calendar deadline or repair evidence.

#### Control and threat checks

| Dimension | Raw check and outcome |
|---|---|
| Injection | New ORM queries use SQLAlchemy parameters. Dynamic migration statements use module constants; all seven SAST hits were inspected and triaged as above. No new shell or external-call surface. |
| Authentication | Changed fact routes retain `current_principal` dependencies and use the existing facade; no token/session behavior or grant was added. |
| Authorization / ownership | `routes/facts.py:138` invokes `execution.read` with `additional_reads=scope_reads`; line 234 invokes `execution.mutate` with source reads. `repositories.py:530` filters evidence/document selections by authorized tenant and KB; line 597 resolves evidence artifact resources under the same scope. The commit service checks its locked slot against `authorized_scope`. |
| Sensitive date/value disclosure | `scope_reads` in `routes/facts.py` rechecks attesting artifacts for both resolved and unknown reads. UNKNOWN response at `schemas/facts.py:108` has no value field. `test_temporal_reads.py:248` checks unreadable attestation is a non-disclosing 404; line 268 tests matching/mismatching expected dates cannot reveal an unreadable document date. |
| Security configuration | Migration functions are SECURITY INVOKER with pinned search_path; no new role, grant or SECURITY DEFINER function. Test-only replica mode is an explicit reconciliation, not ordinary application SQL. |
| Components | Manifest-cited `dependency-engine.json`: 35 dependencies, zero listed vulnerabilities at scan time; no dependency changed in F0008. This is not a claim that a fresh vulnerability database was queried. |
| Audit / repudiation | Commit effects remain inside the authorization mutation UoW with transactional outbox. `_persist_fresh` records FAILED authorization outcomes after rollback; durable business refusal reason is an explicitly deferred F0018 item. Existing immutable-event guards remain, and 0014 adds close-only/version/change guards. |
| Secrets | Manifest-cited final gitleaks SARIF contains zero results. Source changes introduce no production secret. Synthetic local test configuration is not represented as production credential management. |
| Abuse / resilience | Slot locks serialize commits, exclusion protects overlapping valid/recorded ranges, stale requests fail; enums, IANA-zone allowlist, timezone length cap and UUID parsing constrain added input. No new public producer or rate-control surface is introduced. |
| Failure safety | `routes/facts.py:256` maps temporal exclusion conflicts and drops non-exclusion IntegrityError text. `bounds.py:147` rejects malformed inputs with generic range errors; no new database text is echoed. |

STRIDE assessment: spoofing/elevation rely on verified principals, current grants and scoped source READ checks; tampering is constrained by the retained GiST exclusion, composite ownership keys and new close-only/delete/truncate guards; repudiation uses immutable authorization/commit audit; information disclosure is checked for current and historical reads plus attesting documents; DoS has no new external dispatch surface and added parsing is bounded by the existing request boundary. No independently established High/Critical exploit emerged in this scoped review.

#### Raw scanner evidence and limits

- Dependency: `artifacts/security/dependency-engine.json` — 35 packages, no listed vulnerability.
- Secrets: `artifacts/security/secrets/secrets-gitleaks-20261117-052326.sarif` — zero results.
- SAST: `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` — seven constant-SQL warnings, individually triaged as above.
- DAST: `artifacts/security/dast/api-scan.json` — only riskcode 0 informational alert categories (client-error responses and session-management identification); no higher-risk alert. Its protected commit route observations are 401 responses, so it does not prove authenticated business authorization. `test_temporal_reads.py:221` tests current-grant revocation across historical coordinates, while lines 251 and 273 test attestation access. QE owns verification that those cases executed in the cited JUnit.

Accepted residual **SEC-F8-02** remains: the local/CI application role is a superuser and can bypass ordinary triggers with replica mode. `pm-closeout.md:30` names Architect + DevOps and F0018/F0026; `pm-closeout.md:41` and `gate-decisions.md:13` explicitly record operator acceptance of this deferred non-blocking Low. This audit records the residual without silently reopening an accepted scope decision or claiming the feature is production-hardened. The missing durable business reason is likewise explicit in the G0 reconciliation, separate from authorization outcome persistence.

#### FR3 self-review and limitations

SEC-F8-L1 is grounded in the raw manifest field, actual SARIF result array and seven concrete source locations; severity reflects accurate triage and no demonstrated injection. Skipped full scanner reruns are intentional for this read-only closeout audit: the required four recorded raw outputs were inspected; no output is overwritten in the canonical feature run. Authenticated DAST is explicitly not claimed. No frontend rendering, model prompt, remote integration or new authentication implementation changed. Production privilege/RLS and business-reason persistence have explicit later-feature ownership, so they are disclosed scope boundaries rather than silently skipped checks. All new evidence is under this review run or /tmp.
