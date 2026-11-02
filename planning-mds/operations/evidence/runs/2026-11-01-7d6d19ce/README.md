# F0006 planning run 2026-11-01-7d6d19ce

Action: plan; phase A+B; feature mode new; contract 2026-07-11; base-run-only.

## Approval and Publication

The operator explicitly approved Phase A with `approve-phase-a` and Phase B with `approve-phase-b` on 2026-11-01. Both tokens are recorded in gate-decisions.md. Automated publication status is authoritative in evidence-manifest.json and the durable G5 journal; approve-plan.py publishes that manifest after all required postapproval checks. No manifest approval is written manually.

This is planning authorization only. Five stories and 35 ACs remain unstarted; implementation is a separate feature action. ADR-0065 and ADR-0075 remain Proposed until their runtime proof gates pass. Roadmap stays Next.

## Evidence Index

- evidence-manifest.json: automated planning approval publication.
- gate-decisions.md: judgments and explicit operator approval tokens; frozen at checkpoint attestation.
- action-context.md, artifact-trace.md: bound product identity, scope, authority, dependencies and artifacts.
- commands.log, lifecycle-gates.log and gate-state journals: observed validation/operation results.
- artifacts/test-results/: command outputs, not feature role reports.
- artifacts/validation/validate-contract-examples.py: durable offline contract checker.
- workstate.yaml: durable decisions (use its explicit path).

Feature requirements, stories, assembly plan, examples and status are in planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/. No feature evidence index/package is created by plan.

## Validation

G1–G4 passed. All seven G5 preapproval operations passed in order. Five strict story validations passed without warnings; tracker validation had zero errors/warnings; all 16 contract cases, product structural readiness and semantic teaching checks passed. API validation passed with six convention warnings identical to the baseline. Plain KG validation passed with current coverage and nonblocking warnings in unchanged symbol/vocabulary layers.

After operator approval, G5 performs the required compile, coverage refresh, reproducibility, plain KG, tracker-only and final approval operations; its journal/logs record the observed results. No planning-source edit follows that final refresh. If publication is interrupted, resume this same run.
