# Security Planning — Nebula Insurance Brain

**Status:** Baseline index (2026-09-05). The security role authors the required artifacts during Phase B of the first security-sensitive features (F0002, F0018, F0021, F0022).

## Authoritative sources in the master blueprint

- Section 65 Tenancy and section 66 Principals and Authorization, including the CRM-aligned AuthX contract
- Section 110 Security, retention, and learning boundaries (authorization envelope, derivation propagation, governed retention, untrusted inputs, self-confirmation prevention)
- Section 118 AuthX reference architecture and section 119 CRM gaps that must not be copied unchanged
- Section 120 Concrete AuthX contract for the Brain and section 121 validation evidence and required tests
- Section 122 proposed AuthX ADRs (ADR-0049 to ADR-0053, individual records under `../architecture/decisions/`) and section 123 AuthX source map pinned to CRM commit `47375571b19e3f917c1d22cbc076df41320100ff`

## Artifacts in this directory

| File | Status | Notes |
| --- | --- | --- |
| `authorization-review.md` | Draft | Seeded from sections 66 and 118 to 121; the security role completes it with the Brain's permission catalog and policy files |
| `threat-model.md` | Pending | Required by the framework security audit; author from the threat surfaces in sections 110 and 120 |
| `data-protection.md` | Pending | Required; author from section 110 (classification, derivation propagation, retention, deletion, restore) |
| `secrets-management.md` | Pending | Required; model-provider keys, Label Studio tokens, database credentials, authentik client secrets |
| `owasp-top-10-results.md` | Pending | Required; first results land with the first DAST run in a feature evidence package |
| `policies/` | Seeded (F0001 Phase B) | `model.conf` and `policy.csv` for the F0001 proof scope (TenantMember, Reviewer, ServicePrincipal over content_artifact, review_task, fact_slot); mirrored by `kg-source/policies/policy_rules.yaml`; parity fixtures arrive with F0002 |
| `reviews/security-review-YYYY-MM-DD.md` | Pending | Dated review outputs per feature run |

## Non-negotiables carried into every feature

- Verify credentials for the receiving service's issuer and audience before resolving identity or reading any protected storage; forwarding a token is not verification.
- Authorization is the conjunction of current tenant and knowledge-base membership, permitted action, actual resource or parent scope, classification and source restrictions, and delegation limits; role allows cannot override those boundaries.
- Scope rows before retrieval, counts, facets, snippets, graph paths, and model context; recheck at evidence download and commit boundaries.
- User, service, and agent principals are distinct; an agent acting for a user carries both identities and a bounded, expiring delegation.
- Record policy version or hash, grant revision, actor and delegate, resource and action, decision and reason codes, and trace ID for every authorization decision.
- The model never issues authorization decisions or modifies active access policy through ordinary knowledge learning.
