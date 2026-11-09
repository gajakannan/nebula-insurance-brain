# Threat Model — Nebula Insurance Brain

Status: Baseline (v0.1 local scope)
Last Updated: 2026-11-08
Owner: Security + Architect
Review cadence: refreshed by each security-bearing feature run (F0018, F0021, F0022, F0026 next) and before any production pilot

## Scope And Objectives

This is the project-level threat model for the Brain as built through F0006 plus the planned v0.1 surfaces (F0007–F0026, F0069). It covers the engine API, the document worker and conversion child, PostgreSQL (with pgvector/AGE planned), the filesystem content store, local inference (vLLM), authentik, and the planned React shell and Review Panel.

Feature runs keep their own STRIDE assessments in their evidence packages; this document is the shared baseline they refine. Retrieval-specific threats for F0033–F0036/F0067/F0068 are in the [authorization review's governed retrieval carry-in](authorization-review.md#governed-retrieval-carry-in-2026-11-06).

Sources: master blueprint sections 65, 66, 110, 118–121; ADR-0042, ADR-0043, ADR-0049–ADR-0053, ADR-0074; F0002, F0005 and F0006 security reviews.

## System Context And Assets

| Asset | Where it lives | Why it matters |
| --- | --- | --- |
| Source documents (policies, endorsements, submissions) | Filesystem content store under `./content/` (ADR-0059), immutable | Confidential insurance data; the evidence every fact cites |
| Content artifacts and native Docling bundles | Content store + PostgreSQL manifests | Parse-once evidence; tampering breaks every citation |
| Assertions, canonical facts, review decisions, audit events | PostgreSQL | System of semantic record; must be attributable and append-only |
| Authorization state (principals, memberships, grants, Casbin policy) | PostgreSQL + `planning-mds/security/policies/` | Decides who sees what; drift or bypass is a cross-tenant leak |
| Credentials (DB URLs, inference key, authentik secrets) | Environment / `~/.brain-secrets` (see [secrets-management](secrets-management.md)) | Compromise grants direct data or model access |
| Host capacity (CPU, memory, GPU) | Single local host | Converter and model exhaustion stop all ingestion |

**Actors:** authenticated knowledge workers and reviewers; trusted operators (submission, deletion); the worker service principal; the conversion child (no credentials); future agent principals (v0.2+, ADR-0052); adversaries supplying documents or calling the API.

**Trust boundaries:** browser ↔ API (OIDC session, ADR-0051); API ↔ PostgreSQL; worker ↔ conversion child (pipe IPC, staging directory); worker ↔ vLLM; extracted text ↔ model and tools (documents are untrusted input, section 110.4); canonical store ↔ derived projections and caches.

## Threat Inventory (STRIDE)

| ID | Category | Threat | Current control | Status |
| --- | --- | --- | --- | --- |
| T-01 | Spoofing | Forged or replayed token selects another principal | Issuer/audience verification and stable `(iss, sub)` principal mapping (ADR-0049, F0002) | Mitigated (F0002) |
| T-02 | Spoofing | Client-supplied actor or reviewer identity | Server-side principal only; payload identity ignored (ADR-0052) | Mitigated for existing consumers; F0022 extends |
| T-03 | Tampering | Content artifact or bundle altered after publication | Immutable store, content hashes, fenced readiness commit (ADR-0004/0059/0073) | Mitigated |
| T-04 | Tampering | Assertion history rewritten | Append-only corrections, deferred integrity triggers (ADR-0037, ADR-0075, F0006) | Mitigated |
| T-05 | Repudiation | Authorization or review decision without audit | Atomic durable decision audit with policy version (F0002, F0006) | Mitigated |
| T-06 | Information disclosure | Cross-tenant or cross-knowledge-base read | Conjunctive scope checks, composite FKs (F0002); row security as defense in depth planned (ADR-0042, F0018/F0026) | Partially mitigated |
| T-07 | Information disclosure | Derived result (summary, count, embedding, assessment) leaks restricted evidence | Derived results inherit evidence restrictions (ADR-0042); historical reads use current grants (ADR-0053) | Planned (F0018, F0020, F0065, F0069; proof F0026) |
| T-08 | Information disclosure | Missingness explanation reveals restricted evidence exists | Access denial is never an information state (ADR-0039) | Planned (F0007, F0020) |
| T-09 | Denial of service | Crafted PDF exhausts converter memory/CPU | Supervised child with 300 s deadline (ADR-0074); kernel memory/task ceilings, child rlimits and memory sampler (ADR-0074 §1a); patched parser dependencies | **Mitigated 2026-11-08 (SEC-01)** |
| T-10 | Denial of service | Queue flooding | Bounded unfinished-job queue with explicit rejection (ADR-0074) | Mitigated |
| T-11 | Elevation of privilege | Instructions inside a document drive tools or commits | Extracted text is evidence only; worker has no business-write credentials; commits go through the authorized commit path (section 110.4, EX-OWN-006) | Partially mitigated; acceptance test owned by F0016/F0026 |
| T-12 | Elevation of privilege | Converter escapes to the worker's user or network | Child gets no credentials and an allowlisted environment; shares the worker's OS user and network | **Open** (SEC-F5-M1 remainder) |
| T-13 | Information disclosure | Browser token theft or incomplete logout | Same-origin BFF with server-held tokens and upstream revocation (ADR-0051) | Planned (F0021) |
| T-14 | Information disclosure | MIME sniffing of served content or errors | `nosniff` on content routes; not yet on public/error responses | Open (SEC-03, F0004 SEC-L2) |

## Risk Scoring And Acceptance

Severity uses the feature security reviews' scale (Critical, High, Medium, Low) from exploitability and impact on confidentiality, integrity and availability of insurance data. A High finding blocks activation for real or untrusted documents unless the operator records a bounded acceptance with an owner and a date, as at F0006 G4. Acceptances never widen scope: the current approved scope is **trusted local synthetic fixtures** only.

## Mitigations And Evidence Plan

- AuthX carryover matrix (master blueprint 121.2) runs per owning feature; F0026 runs the v0.1 negative suite (ADR-0042/0053).
- Dependency scanning (pip-audit for engine and neuron) runs in every feature security review; any lock change reruns it. The 2026-11-08 scan of neuron reports no known vulnerabilities.
- Converter containment is proven by `neuron/packages/brain-ingestion/tests/test_conversion_limits.py` (ADR-0074 §1a).
- Secrets scanning (gitleaks) runs in feature security reviews; see [secrets-management](secrets-management.md).
- OWASP status is tracked in [owasp-top-10-results](owasp-top-10-results.md); dated reviews live in [reviews/](reviews/).

## Residual Risks

| Risk | Severity | Owner | Before |
| --- | --- | --- | --- |
| T-12 converter shares OS user and network (SEC-F5-M1 remainder) | Medium | DevOps + AI Engineer | Any untrusted or production PDF |
| SEC-F5-L4 provider restart allowlist and minimal restart environment | Low | DevOps | Activation |
| T-14 / SEC-03 / F0004 SEC-L2 response headers | Low | Backend + DevOps | 2026-11-17 |
| Production host, TLS and secret store not chosen (blueprint 117.1 item 3) | Medium | DevOps + Security | Production pilot |
| Retention schedules and legal holds not supplied (ADR-0043) | Medium | Records/legal owners | Production pilot |

## Approval And Sign-Off

Baseline authored 2026-11-08 to close SEC-02 for the v0.1 local scope. It records controls already proven by feature runs and plans the rest; it is not a production security qualification, which belongs to F0026 and a pilot readiness review (ADR-0048).
