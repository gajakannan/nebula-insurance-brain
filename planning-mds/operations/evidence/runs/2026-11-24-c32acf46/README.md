# F0009 plan run 2026-11-24-c32acf46 (PHASE=B rework)

Action `plan`, PHASE=B, FEATURE_MODE=existing, policy 2026-07-11. This is a targeted Architect rework that resolves plan-review 2026-11-24-2af6f972 findings PR-H1 and PR-H2.
Canonical NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (environment).

## Status

**approved.** The operator gave the exact token `approve-phase-b` on 2026-11-24. This run supersedes plan run `2026-11-24-bfdbbf04`, and check-plan-approvals passes with this run as F0009's current approval. G1–G3 were skipped because Phase A is unchanged. G4 passed. G5 passed all pre-approval checks, the attested checkpoint, the post-approval refresh and approve-plan.

## Changes

- **PR-H1 (operator chose "Always re-evaluate"):**
  - Replay identity comes only from ReviewDecision rows, and refused attempts never short-circuit.
  - Attempts are get-or-create on (item, event, outcome).
  - Each refused request writes its own refusal audit.
- **PR-H2:**
  - A closed per-kind edge table (17 kinds) is in the assembly plan's Edge Semantics section and is enforced by provenance-result-v1.
  - `reviewed_by` becomes `reviews`. New kinds: located_in, interprets, recorded_decision.
  - Graph invariants: endpoints present, root connectivity, acyclic ancestry.
  - contract-examples.json passes 21/21.

Details are in [gate-decisions.md](gate-decisions.md) and [action-context.md](action-context.md).

## Evidence Index

- evidence-manifest.json, action-context.md, artifact-trace.md, gate-decisions.md, commands.log, lifecycle-gates.log, gate-state.json
- artifacts/phase-b-rework-examples.log

## Open Follow-ups

- PR-M1 (decided_at naive-UTC vs reserved_at timestamptz), PR-M2 (contract-inventory sources.yaml fields), PR-L1–L5: route to feature G0.
- Optional: a fresh-session plan-review re-check before `feature.md`.
