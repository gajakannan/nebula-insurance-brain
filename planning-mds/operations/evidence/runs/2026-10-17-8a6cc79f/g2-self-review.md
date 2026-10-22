# Self Review — F0004 run 2026-10-17-8a6cc79f

Owner: Codex, Backend / AI / Architect implementation roles. 2026-10-19.

## Scope Review

The approved assembly plan and S0001–S0004 define the scope. Implemented dual
version verified bundles, normalized durable structure, fenced/current-authority
publication, append-only attributable date candidates and verified human
selection/clear, authorized consumer compatibility and isolated local restore.
The existing F0005 lifecycle owns scheduling, leases, retries and delivery.

Necessary refinements are recorded in implementation-decisions.md: transactional
audit staging for immediate FK order; actual Graph unresolved evidence; original
lease plus authorized fallback receipt; submitter-only serialization namespace;
quiesced local snapshots; SQLAlchemy DDL and bounded dependency fixes.
No UI, public mutation route, new permission, model engine or canonical fact
write was added. Production Graph qualification remains outside this feature.

## Acceptance Criteria Review

test-plan.md maps each of 25 ACs to named tests. test-execution-report.md retains
final observed results. Four worked examples have executable reproduction and
independent expected outcomes. Table/cell/header/continuation data now also has
an explicit PostgreSQL reopen/idempotency/FK/missing-index proof.

## Implementation Risks

V2 remains default false until deployment's expansion/backfill/reconciliation
and consumer gates are satisfied. Existing legacy bytes/IDs are never silently
reparsed or relabeled. A failed read records its decision only; operator
sweep/repair owns state changes. Human/source date verifiers default deny.
Actual direct-mode Graph evidence remains partial/unresolved when its ledger
omits native refs. A separate controlled ledger proves exact-span translation.

Pinned Docling component advisories remain for Security's reachability review;
the adapter allows PDF only, uses local OCR and has only the trusted built-in
plugin entry point in the measured runtime. The reviewed source now also rejects non-PDF initial magic before any parser,
closing the demonstrated METS polyglot path. No component waiver or production
security qualification is inferred. Public health/OpenAPI header warnings from
the passive scan are distinct from private content responses, which use
no-store/nosniff. G3 reviewers must judge remaining risk.

## Validation Evidence

Final engine 229 pass (including durable tables); neuron 93 pass / four optional inference/tokenizer skips;
restore four pass. Changed runtime coverage
90.60%, with each engine/neuron/ops layer above 80%. All changed-Python lint and
source type checks pass. Independent review corrections add date-read version
locking and split-once index hashing; their actual regressions pass. See coverage-report.md and test-execution-report.md.
All four security classes executed; raw findings remain in artifacts/security.

## Result

PASS
