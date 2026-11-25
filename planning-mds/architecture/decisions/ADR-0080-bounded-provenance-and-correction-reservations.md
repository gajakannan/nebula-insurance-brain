# ADR-0080: Bounded provenance and correction reservations

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-11-24
**Owner:** Architect
**Plan run:** 2026-11-24-bfdbbf04
**Requirements:** F0009 Phase A approved with operator token `approve-phase-a`, 2026-11-24. Phase B approved 2026-11-24 by operator token `approve-phase-b`; rework run 2026-11-24-c32acf46 (§3 edge table, §5 replay rule) approved the same day. Plan approval does not formally accept this ADR; the proofs below and explicit operator acceptance are required.

## Context

ADR-0010 and ADR-0037 require source-grounded explanations and additive corrections. F0006 already stores versioned assertions and checks source ancestry; F0008 ships close-only canonical versions, same-slot split ancestry and ending evidence. F0011 supplies an installed offline contract system. A complete consumer lineage result and the §88 reserved LearningCandidate identity are absent.

The existing review service returns a prior event on replay, creates a v2 child through the persistence guard, records stale decisions, and rejects a different event on an already-decided item. Its stale path omits submitted value/evidence/comment, and the rejected competing attempt has no durable attributed payload. These gaps are reconciled without changing canonical authority, HTTP envelopes, the decision event hash or the existing batch failure behavior.

## Decision Drivers

- Reuse current F0002 authority, keeping payloads behind every required source READ.
- Preserve precise source/correction/split/change edge meanings and all stored temporal coordinates.
- A reservation is an identity for future learning, never evidence of approval or a delivered producer.
- Keep all source and canonical rows intact, and make rollback/concurrency behavior observable.

## Decision

1. Add an internal `brain_provenance.ProvenanceReader` over a metadata-first repository port. Inputs identify an exact assertion/version plus an existing authority anchor (`fact_slot`, `review_task` or `content_artifact`). The repository proves root-to-anchor association; an arbitrary accessible anchor cannot authorize another root. There is no assertion auth resource, route, grant or UI.
2. Extend `AuthorizationExecution.read` with optional `prepare_reads` executed after root authorization and before `load`. It discovers only structural links/access keys. Source READ checks and semantic consistency checks precede payload materialization. Existing callers retain current behavior. Current policy/principal/resource locks span discovery, materialization, final recheck, durable audit and the single commit; never call a nested read facade inside a mutation.
3. Return a bounded typed result whose edges follow a closed per-kind table of (source kind, target kind) pairs. The table is in the assembly plan's Edge Semantics section and is enforced by `provenance-result/v1`; every edge reads `<source> <kind> <target>`, is unique, joins two returned records and keeps every record connected to the root. The result is bounded: at most 256 correction ancestors, 2048 records, 8192 edges and the existing F0011 serialization size/depth limits. Limits refuse without a truncated graph. Broken/cyclic/unsupported lineage fails with a sanitized internal error; inaccessible/missing/badly scoped roots or required targets are indistinguishable. No errors expose IDs, counts or excerpts. Metadata genuinely unavailable on an authorized intact legacy chain yields an explicit INCOMPLETE result with named gaps.
4. Add two append-only scoped tables, `learning_candidate_reservation` and `review_submission_attempt`. One reservation per new effective non-stale CORRECT is written in the same unit of work as its decision, child assertion and audit. It links exact decision/original/child/reviewer/time and is never backfilled. Future F0041 may adopt its UUID, but no LearningCandidate job or full candidate model is delivered.
5. Preserve review HTTP 200/404/422/503 behavior and the current event-hash identity. Stale decisions retain submitted value/evidence/comment. Before staging any batch correction, lock/preflight every item: a distinct already-decided submission refuses the entire batch. Persist non-applied attempt records for the nonduplicate submissions in that refused batch, get-or-create on (item, event hash, outcome), plus one refusal audit per refused request. Commit only those refusal records, then return the existing sanitized 422. No accepted review decision, correction or reservation is created for the refused batch. Replay identity comes only from review decisions: a prior effective/stale event still returns its original duplicate outcome and creates no second business/audit effect, with current access rechecked first. A stored refused attempt never short-circuits a request; a matching resubmission is re-evaluated against current state, so a sibling refused only because of another item can later apply (rework run 2026-11-24-c32acf46). The preexisting authorization audit still occurs per protected request.
6. Traverse exact stored evidence IDs, correction ancestors, same-slot split predecessors, canonical change links, ending refs and attestation sources. A remainder is not a fresh assertion. Follow incoming change links and split ancestry only, plus outgoing changes of a version to explain its closure; load the exact endpoints and their source requirements, without recursively scanning an entire slot or selecting a latest value. Existing derivation references stay labelled and undelivered producers stay unavailable.
7. New schemas are design-time authored under planning-mds/schemas. Implementation registers them through the F0011 source allowlist and generator; runtime snapshots are not changed by this plan. Existing HTTP schemas remain unchanged. Native embedded legacy values retain native-compat/v1 rather than being rounded into the portable numeric profile.

```text
internal exact root + existing anchor
    -> authorize anchor -> discover IDs/ownership/access keys
    -> authorize every source -> verify metadata snapshot -> load stored payloads
    -> validate/sort result -> final current-authority recheck -> audit + commit

review annotate -> lock/preflight whole batch
    -> effective CORRECT: child + decision + reservation + audit, atomically
    -> stale: attributed non-applied decision, no reservation
    -> competing event: durable refusal attempt + audit only -> existing 422
    -> resubmission matching a refusal: re-evaluated, never replayed
```

## Options Considered

1. **Selected: bounded on-demand lineage over existing rows, with two additive durable hooks.** Preserves source authority and avoids a second authoritative graph. Costs bounded SQL traversal and a small read-facade extension.
2. **Persist a separate provenance graph or snapshot every explanation.** Duplicates facts, evidence and current-authority state; requires independent repair/retention semantics. Rejected for this scope.
3. **Build public history APIs, full review-to-commit orchestration and learning now.** Would duplicate F0020/F0018/F0041 and broaden the approved Phase A. Rejected.
4. **Store only a nullable candidate ID on the mutable review item.** Cannot enforce immutable decision/child linkage or preserve the future identity after item reuse. Rejected.

## Consequences

No new deployable/cache or source parse is needed. Two new tables and migration 0016 are proposed (rebase number if implementation head advances). App checks and composite FKs remain necessary while the application role is elevated; RLS and role remediation remain F0018. An inaccessible required source refuses the entire result, consistent with shipped F0007/F0008 behavior. Legacy incompleteness may prevent a complete explanation, but cannot be silently repaired or promoted.

F0010 owns reason-aware retraction and change vocabulary; F0018 owns complete canonical provenance enforcement and orchestration; F0020/F0022/F0023 consume the internal reader later; F0026 owns benchmark governance and F0041 owns processing of any future learning candidate. The reserved identity is not a new independent source of support.

## Security & Compliance Notes

Current membership, parent/classification conjunction, policy/grant revisions and source restrictions apply to every link. Discovery uses column projections, not ORM claim/source objects. Request-supplied principal or ownership is never trusted. Refused-submission rows may contain sensitive submitted evidence/comments and are returned only through the fully authorized lineage reader; general logs/audit contain only safe correlation and outcome fields, not those payloads. This is a software access contract, not an insurance regulatory interpretation.

## Proofs Required Before Acceptance

| Proof | Owner | Gate |
|---|---|---|
| Exact source/version explanation, completeness and all traversal limits; no parse/model/write effects | Backend + QE | F0009 feature G2 |
| PostgreSQL correction/reservation atomicity, replay, stale retention, whole-batch competing refusal with fresh-query attribution, and a refused sibling that applies on resubmission | Backend + QE | F0009 feature G2 |
| Metadata-first READ ordering, complete source/attestation/ending closure and current-authority denial, including authority races | Security + QE | F0009 feature G3 |
| Composite-owner/child/decision invariants and append-only tables; guarded downgrade, legacy bytes and F0008 close-only behavior | Backend + DevOps + QE | F0009 feature G2/G5 |
| F0011 offline schema/consumer integration and unchanged HTTP route/receipt contracts | Backend + QE | F0009 feature G2/G3 |
| All 41 ACs observed, coverage at least 80%, required reviews and explicit operator ADR acceptance | Architect + operator | Feature completion and separate ADR acceptance |

## References

- [F0009 PRD](../../features/F0009-provenance-and-human-correction-lineage/PRD.md), [assembly plan](../../features/F0009-provenance-and-human-correction-lineage/feature-assembly-plan.md), [contract inventory](../../features/F0009-provenance-and-human-correction-lineage/contract-inventory.yaml)
- [ADR-0010](ADR-0010-provenance-is-mandatory.md), [ADR-0037](ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0044](ADR-0044-review-surface-and-approval-contract.md), [ADR-0078](ADR-0078-bitemporal-version-contract-and-close-only-immutability.md), proposed [ADR-0079](ADR-0079-offline-schema-bundle-and-cross-language-conformance.md)
