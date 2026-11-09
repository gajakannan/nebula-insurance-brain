# Data Protection — Nebula Insurance Brain

Status: Baseline (v0.1 local scope)
Last Updated: 2026-11-08
Owner: Security + Architect

## Objective

Define how the Brain classifies, stores, derives, retains and deletes insurance data, from master blueprint section 110 and ADR-0039, ADR-0042, ADR-0043 and ADR-0053. Current approved use is trusted local synthetic fixtures; nothing here authorizes real customer data.

## Data Classification

| Class | Examples | Handling |
| --- | --- | --- |
| Source evidence | Policy packages, endorsements, loss runs, submissions | Immutable, tenant-owned, restricted by classification and source ACL declared at submission (F0002-S0004) |
| Derived content | Docling bundles, content blocks, OCR output | Same restrictions as the source; parse once, never re-derived silently |
| Semantic records | Assertions, canonical facts, review decisions | Restrictions follow their evidence; corrections append |
| Derived results | Assessments, summaries, counts, embeddings, answers | Served only to principals entitled to all evidence dependencies (ADR-0042) |
| Audit and authorization records | Decisions, grants, policy versions | Append-only; privileged audit access only |
| Operational telemetry | Job stages, latency, token counts | No source text, prompts or answers (section 114.2) |

Every submission must declare at least one classification; missing metadata denies later job steps.

## Protection Requirements

- **At rest:** PostgreSQL and the content store are local to the host in v0.1. Encryption at rest and backup encryption are production-host decisions (blueprint 117.1 item 3) and must be settled before a pilot.
- **In transit:** local loopback only in v0.1. TLS is required for any non-local deployment, including the BFF session cookie (`Secure`, ADR-0051).
- **Access:** current grants apply to every read, including historical queries and every projection (ADR-0053). Authorization is evaluated before content reaches a model, an answer, an export or a cache.
- **Model boundary:** v0.1 inference is local only (ADR-0055). A timeout never falls back to an external provider. Prompts are not persisted by the inference path.
- **Converter boundary:** the conversion child receives no credentials and runs under memory, task, CPU and file-size ceilings (ADR-0074 §1a).
- **Error and telemetry hygiene:** converter errors cross IPC as stable codes only; logs never carry source text.

## Retention And Deletion

ADR-0043 (decision recorded 2026-11-08) governs:

- Source withdrawal, canonical retraction, access revocation and authorized deletion are four distinct events.
- v0.1 supports **operator-initiated deletion only**: a dependency inventory across files, artifacts, assertions, facts, reviews, chat history, embeddings, derived results, caches and exports; removal or tombstoning of each; and a deletion record that every restore re-applies before data becomes readable (F0026 drill).
- Retention schedules and legal holds become versioned policy inputs before a production pilot; records and legal owners supply them.
- Already-downloaded copies cannot be recalled by the service; their treatment is a separate policy decision.

## Data Access And Auditability

Every authorization decision records the policy version, grant revision, actor and delegate, resource, action, decision, reason codes and trace ID. Review decisions record the session principal. Deletions and revocations are recorded through the commit audit with tombstones (F0018).

## Open Items

- Encryption at rest, backup encryption and key management for the production host.
- Retention schedules, holds and conversation-sharing policy (ADR-0043).
- Row-level security as defense in depth under the real application and worker roles (ADR-0042, F0018/F0026).
