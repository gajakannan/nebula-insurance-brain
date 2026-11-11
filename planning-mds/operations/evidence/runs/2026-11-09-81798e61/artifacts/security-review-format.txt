---
template: security-review
version: 2.0
applies_to: security
---

# Security Review Report — F####-{slug} run {run-id}

> File name in feature evidence package: `security-review-report.md`. Required when `security_sensitive_scope = true` or Security Reviewer is required in `STATUS.md` per §10. Security-owned. Broader release/program security reviews remain under `planning-mds/security/reviews/`.

## Scope

- Feature ID: F####
- Run ID: {run-id}
- Date: YYYY-MM-DD
- Reviewer: <Security Reviewer name>

## Reviewed Surfaces

Enumerate the surfaces in scope for this review: auth/authz code paths, identity boundaries, secrets handling, audit logging, PII/sensitive data flow, external integrations, dependency / container vulnerability exposure.

## Threat Boundary

Where the new code intersects trust boundaries. Diagram or table of subject → resource → operation.

## Auth / Authz

Confirm the policy surface used (permission keys, role gates, tenant scoping). Note any new permissions added.

## Validation

Input validation rules added or changed. Note where validators are missing or relaxed.

## Audit / Logging

What events are emitted, where they're persisted, who can read them. Confirm no secrets leak into logs.

## Secrets / Config

How secrets are stored and accessed in dev / preview / prod. Confirm secrets are not committed.

## Scan Disposition

For a `security_sensitive_scope` feature, account for every scan class from the
manifest `security_scans{}` block — `dependency`, `secrets`, `sast`, `dast`. For
each: cite the `artifacts/security/` output path (validator checks it resolves)
or state the waiver and reason. A scanner that did not run is disclosed here as a
waiver, never silently omitted.

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|-------|-----|--------------------------|---------------------------|
| dependency | | | |
| secrets | | | |
| sast | | | |
| dast | | | |

## OWASP Top 10 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | OK / Issue / N/A | |
| A02 Cryptographic Failures | | |
| A03 Injection | | |
| A04 Insecure Design | | |
| A05 Security Misconfiguration | | |
| A06 Vulnerable / Outdated Components | | |
| A07 Identification & Authentication | | |
| A08 Software & Data Integrity | | |
| A09 Security Logging & Monitoring | | |
| A10 Server-Side Request Forgery | | |

## Findings

Findings ranked by severity (`low`/`medium`/`high`/`critical`). Blocking findings yield `FAIL`. Deferred findings as recommendations use §15 canonical bullet:

```text
- [severity] <finding text> — owner: <name-or-role>; follow-up: <ticket-id-or-deferred-no-followup>
```

`high`/`critical` recommendations require explicit PM mitigation in `pm-closeout.md` per §15 PM Acceptance Line Format.

## Recommendation Disposition

For each recommendation, the disposition (mitigated now / deferred to ticket / accepted as residual).

## Result

One of: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`.
