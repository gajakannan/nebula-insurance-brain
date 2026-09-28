# Security Review Report — F0002 run 2026-09-27-bb7c8d1d

## Scope

- Feature ID: F0002
- Run ID: 2026-09-27-bb7c8d1d
- Date: 2026-09-28
- Reviewer: Security Reviewer (agents/security/SKILL.md)

## Reviewed Surfaces

Credential verification and identity profile; principal resolution and aliases; current grant slices and authority revisions; trusted resource hydration and restriction evaluation; delegation issuance and use; the execution facade's transaction and audit ordering; the authentication-event sink; the three API consumers, the commit service, and the F0005 worker adapter; migrations 0005/0006; the reconciliation, delegation, and revocation scripts; the non-secret identity profile.

## Threat Boundary

| Subject | Resource | Operation | Trust decision point |
|---|---|---|---|
| Unauthenticated caller | any protected route | any | `deps.current_principal`: verify before any storage read; rejected → durable authentication event only |
| Verified user/service/agent | content_artifact, review_task, fact_slot | read / annotate / commit | `AuthorizationExecution` → `evaluate` over trusted slices, envelope, and dependencies; audit before release |
| Agent executing for a user | ceiling resource | ceiling actions | Delegation bound to executor, window, and revision; intersected with the actor's current grants |
| Worker job step | content_artifact | ingest / interpret | `DocumentJobAuthorization.decide`: same evaluator; lease scope must equal the hydrated scope |
| Operator (OS/DB access) | registries, grants, restrictions, delegations, policy release | provision / change / revoke | Trusted scripts with approval reference and expected revision; every change audited |

## Auth / Authz

- **No new pilot grant or role.** policy.csv and model.conf are byte-identical. Principal kind is never a grant. Reviewer-only has no content read, and annotation never implies commit (EX-AUTHX-013/016 observed).
- **Verification.** The profile's algorithm allow-list wins over the token `alg`; HS256 and none are refused at profile load. Issuer, audience, and required claims are enforced; claim types are checked; unknown `typ` is rejected; non-JWS input is `malformed`. No principal, membership, or resource read happens before verification, proven with captured SQL across 10 credential variants.
- **Identity.** The `(issuer, subject)` alias is exact and case-sensitive; there is no email linking. Only listed human clients self-provision, and they get no grants. Unknown service/agent clients are refused rather than becoming USER. Linking requires an approval reference and never merges histories. Disabled principals get the generic 401.
- **Scope.** The whole-slice conjunction is enforced, with no mixed slices. Filters only narrow; business valid/known time never authorizes; sibling-KB and cross-tenant grants are irrelevant.
- **Resources.** Envelopes are hydrated only from `resource_access` and verified against the record's own owner. Missing or disagreeing metadata denies. Classification is mandatory, with no default label. Evidence dependencies are bounded (64/8), cycle-safe, and cross-tenant-denied.
- **Delegation.** Issuance cannot exceed current authority. The executor must be an AGENT/SERVICE; there is no onward delegation (an agent cannot be acting) and the window is finite. At use it is re-intersected with current grants and rechecked immediately before the effect.
- **Denial semantics.** Denied and nonexistent resources return a byte-identical 404 body apart from the per-request trace and path. The reason stays in audit only.

## Validation

Every public input is a typed FastAPI/Pydantic model or path UUID, unchanged. No endpoint accepts the internal schema; request headers, query, or body cannot set principal, kind, role, acting user, classification, or delegation (EX-AUTHX-006/011 observed). The trusted scripts validate their mapping and digest, UUIDs, action enums, and expiry bounds. SQL identifiers built from constants in the reconcile script pass an explicit allow-list; values are always bound.

## Audit / Logging

- Every protected read, deny, and mutation writes a schema-valid `Decision` to append-only `audit_event`, with a decision ID, policy hash and release, authority revision, trace, and outcome. It contains no token, bytes, or fact value (EX-AUTHX-017).
- Read audit commits before any payload is returned. Mutations commit with their decision atomically. Failed or denied mutations roll back and are audited in a fresh transaction. Audit failure returns a sanitized 503 with no payload and no effect, proven by injecting failure on the real insert for content, commit, and review (EX-AUTHX-018).
- Rejected credentials go to `authentication_event` through a separate write-only session: null principal, route template, reason, no token. The process-log line correlates via `event_trace_id`.
- Operational changes (grants, revocations, restrictions, identities, delegations, policy activation, reconciliation) are audited with the operator, before/after revision, approval reference, and input digest.
- The 48 legacy audit rows are unchanged; the restore drill digest is identical before and after migration.

## Secrets / Config

No secret was introduced. `config/authx-identity-profile.yaml` is non-secret (issuer, audience, algorithms, client IDs). Gitleaks found no leaks across the branch commits and all source roots. The model/inference data policy is unchanged, and no identity reaches the model.

## Scan Disposition

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|-------|-----|--------------------------|---------------------------|
| dependency | yes | PASS: engine 57 and neuron 177 dependencies, 0 known vulnerabilities (pip-audit) | artifacts/security/g2-engine-pip-audit.json |
| secrets | yes | PASS: 0 leaks (gitleaks, branch commits and filesystem) | artifacts/security/g2-gitleaks-branch.json |
| sast | yes | PASS WITH RECOMMENDATIONS: 1 pre-existing WARNING outside F0002 (scripts/dev/seed_principals.py:37, dynamic urllib in a dev verifier); the in-run dynamic-SQL findings were fixed before the re-scan | artifacts/security/g2-semgrep-report.json |
| dast | yes | PASS WITH RECOMMENDATIONS: ZAP API scan 0 FAIL / 116 PASS; 2 pre-existing header WARNs on /health and /openapi.json | artifacts/security/g2-zap-report.json |

Neuron dependency audit: artifacts/security/g2-neuron-pip-audit.json
G1 pre-change baselines:

artifacts/security/g1-semgrep-report.json
artifacts/security/g1-zap-report.json

## OWASP Top 10 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | Addressed | Conjunctive current authorization at every consumer; tested independently per restriction; 404 non-disclosure |
| A02 Cryptographic Failures | Addressed | Asymmetric-only algorithm allow-list; no key material stored; hashes are SHA-256 |
| A03 Injection | Addressed | ORM/bound parameters; reconcile identifiers allow-listed; SAST clean for F0002 code |
| A04 Insecure Design | Addressed | Fail closed on stale policy, missing authority/metadata, and audit failure; no grant cache |
| A05 Security Misconfiguration | Addressed | API refuses to start if the issuer is absent from the profile; unsafe profiles are rejected at load |
| A06 Vulnerable Components | Addressed | pip-audit clean |
| A07 Identification and Authentication Failures | Addressed | Verify-before-read, typed claims, disabled principals, no email linking, concurrency-safe first sight |
| A08 Software and Data Integrity Failures | Addressed | Immutable policy release identity; reconciliation digest binding; ID/ownership checksums |
| A09 Security Logging and Monitoring Failures | Addressed | Durable decision and authentication audit; audit failure blocks success |
| A10 SSRF | N/A | No new outbound fetch; the JWKS URL comes from trusted config |

## Findings

- Critical: none
- High: none
- [medium] Each unauthenticated request now causes one durable `authentication_event` insert. Without edge rate limiting this is a storage-amplification vector. Mitigate with rate limiting at the BFF/edge (F0021) and retention in production hardening (F0026). — owner: DevOps / F0026 owner; follow-up: deferred-no-followup
- [low] `audit_event` and `authentication_event` are append-only by service contract; the database does not yet block UPDATE/DELETE. This is part of the BLUEPRINT §4.11 immutability safeguards carried as a follow-up. — owner: Architect; follow-up: deferred-no-followup
- [low] JWKS unavailability yields a 401 deny (correct per plan: deny without fallback), indistinguishable in metrics from bad credentials. Add a distinct operational metric when observability lands. — owner: DevOps; follow-up: deferred-no-followup

## Recommendation

Approve. There are no critical or high findings; the medium finding has an owner and a mitigation path.

Result: PASS WITH RECOMMENDATIONS
