# F0005 plan rework — 2026-10-25-50fcf658

Status: **APPROVED — Phase B planning complete.** The operator replied `approve` to the revised architecture. G4 and G5 completed; all seven pre-approval and six post-approval operations passed. approve-plan.py published this run and explicitly superseded prior plan 2026-10-23-9a04b327, retaining its Phase A history. The approval-history check identifies this run as the current F0005 plan with no errors.

The three repaired gaps are explicit direct-baseline rejection selection, supervised conversion with a parent-owned 300-second bound/publication fence, and a shared host worker guard with safe recovery from uncertain provider work. The requirements, thresholds, five stories and checklist are unchanged. Runtime implementation and qualification remain future work; ADR-0060 remains Proposed.

## Evidence

- [Approved architecture](../../../../features/F0005-one-time-docling-ingestion/feature-assembly-plan.md).
- [Approval and gate decisions](gate-decisions.md), gate-state.json and evidence-manifest.json.
- [Final approved patch](artifacts/diffs/approved-plan-quiet.txt).
- [Publication verification](artifacts/publication-verification.json) and [approval-history check](artifacts/published-approval-history.txt).
- action-context.md, artifact-trace.md, commands.log, lifecycle-gates.log and artifacts/validation/.

The plan is ready for the feature action's preflight. No runtime source/config/tests, feature-completion package or activation decision was produced by this planning action.
