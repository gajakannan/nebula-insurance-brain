# F0009 G0 — Assembly plan validation

Reviewer: Claude (Opus 5.5) / Architect
Date: 2026-11-24
Verdict: PASS
Run: 2026-11-24-08701e37
Product: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

Result: PASS

The approved plan, with Phase B rework `2026-11-24-c32acf46` (which resolved PR-H1/PR-H2), is the implementation baseline. No new plan was authored. I read the PRD, all six stories (41 ACs), the four authored schemas plus `review-decision`, migration-design.sql, contract-inventory.yaml, ADR-0080 and the plan-review report `2026-11-24-2af6f972`, and checked them against the shipped code at `main` 3729dbe. Requirements are unchanged.

## Scope split and dependencies

The five build steps keep their order and checkpoints:

1. carriers and contracts;
2. migration 0016;
3. the review boundary;
4. the metadata-first reader;
5. temporal closure and delivery.

Backend owns domain, application and infrastructure, plus the review and reader integration. QE owns independent EX-PROV fixtures and PostgreSQL proof of concurrency, rollback and denial. DevOps owns migration ordering, the guarded downgrade and package install. Security owns READ-before-materialize and current grants. Code Reviewer owns correctness and compatibility. Architect owns shared semantics and the ADR-0080 proof gates. Frontend and AI are out of scope (no UI, model, parse or producer). The five-role signoff matrix in STATUS.md is reconfirmed for every story.

Dependencies are all shipped: F0002, F0004, F0006, F0007, F0008 and F0011. The brain-review reservation methods stay on the review repository port, so there is no brain-review ↔ brain-provenance cycle.

## Verified plan claims against code

| Plan claim | Code evidence | Result |
|---|---|---|
| Migration head is 0015 | `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py` is the latest revision | Confirmed; 0016 needs no rebase |
| `submit` replays first, then `has_any_decision` rejects; stale branch drops value/evidence/comment | `brain_review/decisions.py` `ReviewDecisionService.submit` | Confirmed |
| `save_decision` relies on the server default for `decided_at` | `repositories.py` `save_decision`; `models.py` `decided_at` `server_default=func.now()`; migration 0002 `sa.DateTime()` (naive) | Confirmed (PR-M1) |
| POST route authorizes all tasks, passes `source_keys` as `additional_reads`, maps already-decided to 422 | `brain_api/routes/reviews.py` `submit_review_decisions` | Confirmed |
| `source_keys` includes sources only for v2 discovery | `SqlAlchemyReviewItemRepository.source_keys` (`if discovery.has_v2`) | Confirmed; Step 3.1 extension stands |
| `AuthorizationExecution.read` authorizes payload-derived reads only after `load` | `brain_security/execution.py` `read` | Confirmed; opt-in `prepare_reads` is additive |
| `review_decision` has no append-only trigger | 0007 `APPEND_ONLY = ("audit_event", "authentication_event")`; owner-change trigger only | Confirmed; 0016 adds it |
| `review-decision` is not a bundled resource | `scripts/contracts/sources.yaml` `retained_boundaries` + `openapi_only_resources` | Confirmed; promoted (PR-M2) |
| Composite owner unique keys exist for the FK targets | 0005/0006 owner keys on `review_decision`, `assertion`, `review_item`, `review_batch` | Confirmed at Step 2 by the PostgreSQL proof |

## Carried plan-review findings — resolved at G0

| Finding | Resolution | Where |
|---|---|---|
| PR-M1 | Persist `decided_at` through `audit_timestamp()` (naive UTC). The guard compares `decided_at AT TIME ZONE 'UTC'` with `reserved_at`. | Assembly plan §G0 Reconciliation |
| PR-M2 | Full `sources.yaml` field set for five resources; `review-decision` promoted to a resource; edit list completed | contract-inventory.yaml |
| PR-L1 | Legacy GET keeps `null` stale payload fields, unchanged; a regression fixture asserts this | Assembly plan §G0 Reconciliation |
| PR-L2 | Duplicate item in a batch keeps the shipped duplicate/422 behavior, with no attempt. A fingerprint change gives the existing 503 after a durable failed audit; the client resubmits. | Assembly plan §G0 Reconciliation |
| PR-L3 | Narrow the KG story mappings at G7 | Assembly plan §G0 Reconciliation; G7 |
| PR-L4 | Story grammar fixed (S0005, S0006) | Story files |
| PR-L5 | S0006 interaction row describes the operator migration | S0006 |

None of these changes adds a route, grant, response field, table or story requirement. PR-L1 deliberately chooses the zero-change option for the legacy route, so S0006 AC4 needs no new operator approval.

## Integration checkpoints (feasible)

1. All contract examples validate, the closed registry builds, and OpenAPI paths are unchanged.
2. PostgreSQL refuses invalid links, mutations and TRUNCATE. Legacy snapshots are unchanged. A populated downgrade refuses.
3. Replay, stale, race and mixed batches have exact effects. Reservation failure rolls back. There are zero canonical effects.
4. Every source is authorized before the protected load, with no partial output or log leak.
5. EX-PROV-001–005 reproduce; 41/41 ACs, coverage ≥ 80% on changed lines, and reviews pass.

## Artifact ownership and knowledge graph

There is no ownership conflict. The four new schemas and the `review-decision` source are Architect-owned and unchanged at G0. Generated contract artifacts come only from the F0011 toolchain. Predicted KG delta: the existing planned capabilities `provenance-lineage`, `review-submission-attribution` and `learning-candidate-reservation` gain code bindings for `brain-provenance/**`, `brain_domain/provenance.py`, `brain_persistence/provenance*.py` and migration 0016. `evidence-review-round-trip` and `durable-authorization-decisions` already cover the modified review and security files. No generated KG YAML is hand-edited.

## Validation limits

This verdict approves the assembly and its checkpoints only. Runtime readiness, conformance and all 41 ACs remain unproven until G1/G2. ADR-0080 remains Proposed.
