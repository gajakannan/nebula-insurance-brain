# Gate Decisions — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

> Required per §8. One row per gate evaluated. §17 stage matrix dictates which rows must be present at each validation stage.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G0   | PASS     | Architect | 2026-09-08T00:00:00Z | Existing `feature-assembly-plan.md` (authored plan run 2026-09-06-cdb5d8cb, reconciled 2026-09-08 for ADR-0057/ADR-0059) validated against current stories/ADRs; scope split, dependencies, integration checkpoints, and artifact ownership all confirmed; `run-gate.py --stage G0` exit `validate-g0` pass. See `g0-assembly-plan-validation.md`. | No | `kg-source/features/F0001.yaml` status flipped `architecture-complete` → `in-progress`; `compile.py` re-run. |
| G1   | PASS     | DevOps    | 2026-09-08T00:00:00Z | Host inventory confirmed (Docker, Compose v5.3.1, uv 0.11.31, GPU free with 11.9 GiB). One actionable finding: `nebula-insurance-crm`'s authentik container already holds host ports 9000/9443, so Brain's Step 2 compose file must remap its own authentik service off those defaults. See `g1-runtime-preflight.md`. | No | Remap Brain authentik to non-default host ports at Step 2; pin distinct Brain API / vLLM host ports (avoid 8080/8200/8082 already in use by the CRM). |

Decisions: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`, `SKIP`. Blocking values: `Yes` / `No`.
