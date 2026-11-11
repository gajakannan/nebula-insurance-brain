# Security Review Report — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Security Reviewer
- Reviewer: Claude (Opus 5.5) / Security
- Date: 2026-11-09
- Independence: the same agent session implemented the feature (see `code-review-report.md`). The operator decides at G4 whether that is sufficient.

## Scope

The F0007 change set, `security_sensitive_scope=true`, covers:

- tenant/KB ownership keys and immutability triggers on `fact_slot` and the new `fact_slot_qualifier`;
- derived `resource_access` restrictions for new slots;
- the authorization order for slot resolution (INTERPRET over source artifacts), for answer commits (`fact_slot:commit` plus READ of scope and name-evidence artifacts) and for answer reads;
- non-disclosure (T-08) and the RLS handoff to F0018.

## Reviewed Surfaces

- `brain_factslots/service.py`, `resolution.py`, `answers.py` (authorization order, savepoint rollback, reasons);
- `brain_persistence/fact_slots.py` (projection-only reads before authorization, derived access, audit payload);
- `engine/apps/api/src/brain_api/routes/facts.py`, `errors.py`, `deps.py`;
- migration `0012` (constraints, triggers, privileges);
- `scripts/ops/verify_content.py` (column projection).

## Threat Boundary

| Actor | Threat considered |
|---|---|
| Authenticated principals in other KBs or tenants | Existence or content disclosure |
| Principals in the same KB with narrower classifications | T-08: scope pages and blocks of a restricted artifact |
| Database-level writers bypassing the service | Cross-owner child rows, identity rewrites |

## Auth / Authz

- **Resolution.** It runs as the `operation` of `AuthorizationExecution.mutate` over the source CONTENT_ARTIFACT keys with INTERPRET. Source artifacts from more than one owner are rejected as `SUBJECT_NOT_FOUND`. `authorized_scope` comes only from decisions, and a `tenant_id` in the payload is rejected.
- **Commits.** The existing `fact_slot:commit` is joined by READ of the absence-scope artifact and of the name-evidence artifacts in the same unit of work. The F0006 source proof is issued only from evidence-derived reads (G0 reconciliation 2).
- **Reads.** `GET /facts/{id}`, `read_answer` and the name hook use `fact_slot:read`. Since the G3 fix, they also READ the scope artifact of an identity-v1 answer. Every denial maps to the 404 `not_found` already used for a missing resource.
- **No new authority.** No grant, role, Casbin row or route.

## Validation

All validation is server-side and deterministic, and every rejection writes zero rows:

- predicate grammar and pinned release;
- declared, typed qualifiers, with explicit null rejected;
- exact decimals, with JSON numbers refused for money;
- a pinned ISO 4217 list;
- scheme-scoped identifiers;
- names that require admitted same-KB F0006 v2 evidence.

422 responses carry only the lowercase reason code and no detail text.

## Audit / Logging

- **Slot creation.** Each creation writes one `fact_slot_created` or `fact_slot_member_created` event. The payload holds IDs and versions only: tenant, KB, slot, parent, predicate key, cardinality, fingerprint version and authorization decision ID. It never holds values.
- **Commit audit.** Unchanged.
- **Durable decisions.** Every authorization decision, including the new scope and evidence READs, is recorded through the existing facade.

## Secrets / Config

No secret, credential or environment variable was added. Gitleaks found no leaks across all 75 changed files.

## Scan Disposition

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|---|---|---|---|
| dependency | yes | clean: pip-audit, 0 known vulnerabilities in the locked engine set. F0007 adds no third-party package. | `artifacts/security/dependency-engine.json` |
| secrets | yes | clean: gitleaks over every changed file, final code | `artifacts/security/secrets/` (latest `secrets-gitleaks-*.sarif`) |
| sast | yes | clean: semgrep `p/python`, `p/security-audit`, `p/secrets`; 237 rules, 33 files, 0 findings, final code | `artifacts/security/sast/` (latest `sast-semgrep-*.sarif`) |
| dast | yes | clean: ZAP API scan from the live OpenAPI, 113 rules passed, 0 warn, 0 fail. Unauthenticated reach only; authenticated denial and non-disclosure are proven by the HTTP integration tests. | `artifacts/security/dast/api-scan.json`, `run-dast.sh` |

## OWASP Top 10 Coverage

| Category | Assessment |
|---|---|
| A01 Broken Access Control | Reviewed in depth. Two defects were found and fixed (below). Cross-KB and cross-tenant negatives pass, both at the facade and as direct-SQL constraint negatives. |
| A03 Injection | Parameterized SQLAlchemy and psycopg throughout; no string-built SQL from input. Migration SQL is static. |
| A04 Insecure Design | A fingerprint collision never merges slots. Identity is immutable by trigger. A legacy row cannot gain an identity. |
| A05 Misconfiguration | No RLS change: no `BYPASSRLS`, no `SECURITY DEFINER`, no `GRANT` in 0012. The trigger functions run with invoker rights. |
| A08 Integrity | Qualifier rows are append-only. A deferred integrity trigger guards member and qualifier parents. |
| A09 Logging | Creation audit present; no values or content in the payloads. |

The other categories (cryptography for auth, vulnerable components, SSRF, authentication) are unchanged by this feature. The dependency scan is clean.

## Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| SEC-F7-01 | Medium | Resolving a name member checked the evidence assertion's eligibility without READ-authorizing its source artifacts, and the new member's restrictions omitted those artifacts. A reader could create a member derived from evidence they cannot read and learn eligibility of an assertion ID. | **Fixed:** the evidence artifacts join `additional_reads` before any reason, and the member's derived restrictions include them. Test: `test_g3_name_member_evidence_is_read_authorized_before_any_reason`. |
| SEC-F7-02 | Medium | T-08 on the read path. `GET /facts/{id}` and the internal reader returned the absence scope's pages and block IDs to a slot reader who could not read the scope's artifact (S0003 AC6). | **Fixed:** the scope artifact is READ-authorized before the slot read, and a denial is the standard 404. Test: `test_s0003_ac6_reads_never_expose_a_scope_the_reader_cannot_read`. |
| SEC-F7-03 | Low | After the SEC-F7-01 fix, an assertion ID from another tenant or KB produced 404 (READ denied) while an unknown ID produced 422, a UUID-gated existence oracle. | **Fixed:** the evidence artifact lookup is scoped to the slot's KB, so a foreign assertion behaves exactly like a missing one. Asserted in `test_s0005_ac4_kb_a_trade_name_is_invisible_in_kb_b`. |

Open findings after the fixes: Critical 0, High 0, Medium 0, Low 0.

S0006 AC5 check: 0012 creates no policy, role, grant, `BYPASSRLS` attribute or `SECURITY DEFINER` function. The RLS inventory (`fact_slot`, `fact_slot_qualifier`) is recorded in the feature's GETTING-STARTED and the assembly plan for F0018.

Residual risk, already accepted in ADR-0077 and owned by F0018: slot restrictions are fixed from the creating sources. A later commit whose name evidence lies in a more restricted artifact does not tighten the slot. Re-derivation is F0018 policy. This is not a new finding.

## Recommendation Disposition

No open recommendation. All three findings were fixed and re-tested in this review cycle; the final-code scans are listed above.

## Result

PASS
