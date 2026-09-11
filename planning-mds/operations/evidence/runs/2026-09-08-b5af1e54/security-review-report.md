---
template: security-review
version: 2.0
applies_to: security
---

# Security Review Report — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

## Scope

- Feature ID: F0001
- Run ID: 2026-09-08-b5af1e54
- Date: 2026-09-10
- Reviewer: Security Reviewer pass

## Reviewed Surfaces

Credential verification (`brain_security.verification`), principal identity mapping
(`brain_security.principals`), authorization/scope enforcement
(`brain_security.authorization`, `casbin_adapter`), audit logging
(`brain_security.audit`), the bitemporal commit boundary
(`brain_temporal.commit` — who may write canonical truth), the review/approval boundary
(`brain_review.decisions` — who may adjudicate vs. commit), secrets handling
(`config/local.yaml`, `.env.example`, authentik blueprint), and the backup/restore drill
(`scripts/ops/`) as a data-exposure surface.

## Threat Boundary

| Subject | Resource | Operation | Enforcement |
|---|---|---|---|
| Anonymous / unverified bearer | any protected route | any | 401 before any read (`OidcJwksVerifier` runs before `PrincipalResolver`, which runs before the route body) |
| Verified principal, no matching membership | content artifact / review task / fact slot | read/annotate/commit | 404, never 403 — existence never disclosed (`AuthorizationService`'s structural tenant/KB conjunction denies before Casbin ever runs) |
| Verified principal, `TenantMember`/`Reviewer` role | `fact_slot:commit` | write canonical truth | Denied — only `ServicePrincipal` holds `fact_slot:commit` in `policy.csv` |
| Revoked membership | any resource in that tenant/KB | any | Denied on the very next request — measured 12.41ms, no cache to propagate through |

## Auth / Authz

- Policy surface: Casbin `model.conf`/`policy.csv` under `planning-mds/security/policies/`,
  three roles (`TenantMember`, `Reviewer`, `ServicePrincipal`), three resource types
  (`content_artifact`, `review_task`, `fact_slot`), actions `read`/`annotate`/`commit`.
- No new permissions were added beyond what S0004 already established; S0005/S0006 reused
  the existing three roles against the new `fact_slot` resource type.
- Tenant/knowledge-base scoping is enforced structurally (a Python conjunction check)
  before Casbin evaluates at all — a Casbin policy bug could at most produce a false
  `allow` within the caller's own tenant/KB, never across tenants.

## Validation

- Pydantic v2 models validate every request body (`CommitProposalIn`, `ReviewDecisionIn`,
  etc.); `extra="forbid"` on every schema.
- `CanonicalCommitService` rejects empty/inverted `valid` ranges before any write
  (`TimeRange.__post_init__`).
- `LocalFilesystemObjectStore._path_for()` rejects path traversal (`..`, leading `/`,
  escaping the configured root) — verified in `apps/api/tests/test_content.py::test_path_not_in_manifest_is_404`
  with a literal `../../etc/passwd` attempt.

## Audit / Logging

Every `AuthorizationService.authorize()` call writes an `audit_event` row with
`policy_hash`, `grant_revision`, actor, resource, action, `decision`, and `reason_code`
(`no_membership`, `policy_denied`, or `allowed`). The specific denial reason is recorded
in the audit event only — never returned to the caller (verified in
`engine/tests/security/test_credential_verification.py`, which asserts the internal
reason string does not appear in the HTTP response body/text).

## Secrets / Config

- No secrets are committed. `config/local.yaml` is committed and contains only non-secret
  local filesystem defaults (ADR-0059). `.env.example` documents the two authentik
  bootstrap variables with no real values.
- `AUTHENTIK_SECRET_KEY`/`AUTHENTIK_BOOTSTRAP_PASSWORD` are generated fresh per CI run
  (`python3 -c "import secrets; ..."`) and per local `.env` (gitignored, never committed).
- The inference service (vLLM) receives chunk text only — never a user token, principal
  id, or tenant identifier (verified by code inspection of `docling_graph_adapter.py`'s
  request construction).

## Scan Disposition

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|-------|-----|---------------------------|---------------------------|
| dependency | Yes | `engine`: 0 known vulnerabilities (`pip-audit --local`, 28 packages). `neuron`: 0 known vulnerabilities (`pip-audit --local`, 60 packages). `experience`: 0 vulnerabilities at `high` level (`pnpm audit --audit-level high`, 344 total deps). | `artifacts/security/engine-pip-audit.json` and `artifacts/security/neuron-pip-audit.json` and `artifacts/security/experience-pnpm-audit.json` |
| secrets | Yes | `gitleaks detect` in **git-history mode** (the authoritative scan — 12 commits, ~6MB scanned): **0 leaks**. A supplementary filesystem-mode scan (`--no-git`) flagged 6 findings, all in gitignored/untracked local artifacts never committed to the repo (a locally-generated `.env` with a random dev secret, and SHA-256 content-hash strings inside the framework's own `.kg-state/` gate-checkpoint cache misidentified as API keys by entropy heuristics) — verified via `git check-ignore -v` and `git ls-files` that none of the flagged paths are tracked. | `artifacts/security/gitleaks-report-git.json` (0 leaks); `artifacts/security/gitleaks-report.json` (filesystem-mode, false positives, retained for audit trail) |
| sast | Yes | `semgrep --config auto` (1074 community rules, 92 git-tracked files): 2 findings, both `package_managers.uv.uv-missing-dependency-cooldown` (medium) — `engine/pyproject.toml` and `neuron/pyproject.toml` lacked `[tool.uv] exclude-newer`, a supply-chain hardening setting. **Fixed** for `engine/` (added `exclude-newer = "7 days"`, re-verified `uv sync`/ruff/mypy/pytest all still pass). **Waived** for `neuron/`: adding it breaks resolution outright — `docling==2.126.0` (the deliberately pinned, live-verified version per `docker/DEPENDENCY-MATRIX.md`) was published within the cooldown window, so the constraint would force a downgrade away from the tested pin. Re-scan after the engine fix: 1 finding (neuron only), as expected. | `artifacts/security/semgrep-report.json` (before fix, 2 findings), `artifacts/security/semgrep-report-recheck.json` (after fix, 1 finding — the disclosed neuron waiver) |
| dast | Yes | OWASP ZAP baseline (passive scan, automation framework, 1-minute spider) against the running `brain_api` `/health` endpoint and its implicit root: 66 PASS, 0 FAIL, 1 WARN-NEW (`Storable and Cacheable Content` on three 404 responses — informational; the API serves no static/cacheable content and the 404s are for undefined paths, not a data-exposure finding). Scope is limited to the unauthenticated surface reachable by a passive spider in one minute; the protected routes (`/reviews`, `/content`, `/facts`) require a real bearer token the automation framework's default spider does not carry, so their authz behavior is instead covered by the live `engine/tests/security/` suite (credential verification, scope isolation), not by this DAST pass. | `artifacts/security/zap-report.json` and `artifacts/security/zap-report.html` |

## OWASP Top 10 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | OK | Structural tenant/KB conjunction + Casbin, denial-as-404, proven cross-resource in `test_scope_isolation.py` |
| A02 Cryptographic Failures | OK | No custom crypto; RS256 JWT verification via `PyJWKClient`; secrets never committed |
| A03 Injection | OK | SQLAlchemy parameterized queries throughout; `LocalFilesystemObjectStore` rejects path traversal |
| A04 Insecure Design | OK | Verify-before-read is structural (dependency order), not a convention; unresolved evidence blocks the decision rather than degrading it (ADR-0058) |
| A05 Security Misconfiguration | OK | No secrets committed; ZAP found no missing-header findings beyond the one informational cache warning |
| A06 Vulnerable/Outdated Components | OK | 0 known vulnerabilities across all three workspaces (see Scan Disposition); `engine/`'s uv dependency cooldown now closes the "newly-published-malicious-package" gap semgrep flagged |
| A07 Identification & Authentication | OK | Full edge-case coverage: expired/wrong-audience/wrong-issuer/wrong-signature/not-yet-valid/malformed all rejected before any read |
| A08 Software & Data Integrity | OK | `EXCLUDE USING gist` constraint at the DB level backstops the application-level row lock for concurrent commits; outbox replay is idempotent |
| A09 Security Logging & Monitoring | OK | Every authorization decision audited with policy hash, grant revision, reason code, trace id |
| A10 Server-Side Request Forgery | N/A | No user-controlled outbound URL fetch surface in this feature's scope |

## Findings

No blocking findings.

- [medium] `neuron/pyproject.toml` has no `[tool.uv] exclude-newer` dependency cooldown — waived (see Scan Disposition) because the deliberately pinned `docling==2.126.0` was published inside any reasonable cooldown window. Reassess when `neuron/`'s pins age past 7 days — owner: ai-engineer; follow-up: F0002.
- [low] ZAP's `Storable and Cacheable Content` warning on 404 responses — no data exposure (the API serves no static content); a global `Cache-Control: no-store` on error responses would silence it but is not required for this feature's scope — owner: backend-developer; follow-up: F0021 (whichever feature next touches `errors.py`'s response construction).

## Recommendation Disposition

- The `exclude-newer` finding: mitigated now for `engine/` (this run); deferred for
  `neuron/` with an explicit, documented reason (see Findings).
- The ZAP cache-header warning: accepted as residual — informational severity, no
  practical exposure given the API's response shapes.

## Result

PASS WITH RECOMMENDATIONS
