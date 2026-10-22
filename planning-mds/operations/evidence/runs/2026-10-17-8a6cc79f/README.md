# F0004 feature run — 2026-10-17-8a6cc79f

## Run Summary

F0004 content artifact model; product root
/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain.
Planning approval remains 2026-10-17-620b7618.

## Status

Approved implementation, all four stories Done and archived on 2026-10-21.
G0–G8 PASS. User G4 approval and all required G5 signoffs are recorded.
G8 patch-then-publish preserves the independent planning approval. Final ordered
closeout, scoped tracker and plain KG integrity checks all passed; exact outcomes
are recorded in lifecycle-gates.log. Code and Security pass
with bounded recommendations; no open High/Critical. V2 flag false;
ADR-0073 Proposed. No deployment or commit/merge occurred.

## Evidence Index

[Action context](action-context.md); [implementation decisions](implementation-decisions.md);
[preflight](g1-runtime-preflight.md); [gate decisions](gate-decisions.md);
[code review](code-review-report.md); [security review](security-review-report.md);
[G4 approval request](g4-approval-request.md); [signoffs](signoff-ledger.md);
[graph reconciliation](kg-reconciliation.md); [PM closeout](pm-closeout.md).
Raw logs and coverage live under artifacts/test-results and artifacts/coverage.
The [PR #27 CI follow-up](ci-followup.md) records the archived fixture correction
and PostgreSQL persistence/restore coverage lane verification.

## Validation Summary

- Final engine regression: 229 passed; neuron: 93 passed and four optional skips.
- Actual isolated v1/v2 backup/restore: four passed; durable table/index proof is included in the engine total.
- Changed runtime coverage: 90.60%, each engine/neuron/operations layer above 80%.
- Strict schema examples: 40 cases passed; packaged-wheel schema deployment passed.
- Engine dependency audit clear; all 15 retained Docling advisory records have scoped reachability review.
- No blocking SAST or secret findings; passive OpenAPI scan has two public-endpoint header warnings.
- See [test execution](test-execution-report.md) and [coverage](coverage-report.md) for exact scope and artifacts.

## Open Follow-ups

Named owned follow-ups are recorded in pm-closeout.md: baseline security docs,
fixed converter/hooks and exact OCR assets, public headers, static caller graph
limits and future PR owner acknowledgement. G7 bindings and generated layers
passed; current source callers are retained in kg-reconciliation.md. No required
story is deferred. Deployment activation remains separate.

## Run Environment

Application commands run in run-scoped Compose jobs, with the product mounted
at /app/brain. Absolute host cwd entries in commands.log identify the selected
product root; framework orchestration runs in sibling nebula-agents. Restore
job uses Docker client/socket only to create its owned throwaway targets.
