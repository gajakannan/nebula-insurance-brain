# ADR-0070 example defect repair — 2026-10-11-453de556

## Run Summary

Architect-led defect-bugfix action, with Backend Developer and Quality Engineer roles exercised sequentially by Codex. Account 360 now includes owned policies independently of named-insured roles. Dated account lifecycle distinguishes CURRENT and CLOSED, so retained closed history allows a replacement while two current accounts still fail validation. ADR, data model, glossary, examples and generated KG projections agree.

## Status

Implementation and validation complete; final Architect closeout recorded in gate-decisions.md. Lifecycle Authority = none. ADR-0070 remains Proposed. This is a base defect run, not feature completion evidence.

## Evidence Index

- [Architect analysis](architect-analysis.md): root cause, governing intent and implementation handoff.
- [Backend fix report](backend-fix-report.md): executable example changes.
- [Quality report](quality-report.md): boundary coverage and validation matrix.
- [Action context](action-context.md), [artifact trace](artifact-trace.md), [gate decisions](gate-decisions.md).
- commands.log and lifecycle-gates.log; runner outputs and test results under artifacts/.

## Validation Summary

Three failing reproduction cases became passing regressions. All 63 validation tests pass, including 12 new cases. Strict RDF and all four product lifecycle gates pass with RDF actually executed. Planning readiness, tracker and story checks pass. KG source/projection reproducibility and freshness checks pass. Existing dependency/heuristic warnings are recorded in quality-report.md.

## Open Follow-ups

None for the two reviewed defects. Production account lifecycle enforcement and Account 360 delivery remain with F0012/F0017/F0023 under the existing Proposed ADR; no production acceptance or feature status was advanced.
