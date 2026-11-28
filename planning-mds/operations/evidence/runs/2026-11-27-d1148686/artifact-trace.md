# Artifact Trace — F0021 Plan Review

## Run Environment

- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; source shell environment, normalized once by the resolver and explicitly passed to product-aware invocations.
- Framework cwd: `/home/gajap/uSandbox/repos/nebula/nebula-agents`; session starting cwd: `/home/gajap/uSandbox/repos/nebula`.
- Absolute cwd values in commands.log distinguish the sibling framework and product repositories and the independent reviewer processes. They are intentional.
- Contract: read-only-audit 2026-07-11; run ID: 2026-11-27-d1148686.
- Initial product HEAD and 1,423 non-operations file hashes: `artifacts/review-baseline.json`. Initial worktree was clean except for this new base run.
- Product instructions (including blueprint and local review checklist) captured in `artifacts/product-context.txt`.
- Bootstrap commands were transcribed after commands.log was created; timestamps are transcription times. Setup invocation errors and corrections are disclosed in `artifacts/bootstrap-telemetry.md`.

## Scope and authority

`features/REGISTRY.md:42` resolves F0021 to `features/F0021-native-react-semantic-shell-and-oidc-session/`. `lookup.py F0021` returned the exact feature with one-hop routes; it was used only as a routing aid. Every feature-local file was inspected by the PM lane, while architecture and buildability lanes inspected their raw design/dependency surfaces directly. The feature folder has 19 planning artifacts, including nine stories and 55 ACs.

Raw current requirements/design/API/schema/security evidence wins over KG mappings and prior approval tokens. Approved reconciliations R1/R2 were read directly in `feature-assembly-plan.md:35` and `:36` and the selected plan run's `gate-decisions.md` G5 approval section. The audit did not alter them. The existing assembly design was inspected, without treating its filename as a prerequisite deliverable.

## Raw evidence

`artifacts/raw-artifacts-sha256.json` records 34 target/governing/approval files. Additional exact dependency, runtime and KG references cited by each lane are preserved in its shell-read logs and section. No broad cold-evidence content review was performed; selected planning approval history was opened specifically for this audit and core approval validation.

| Evidence | Purpose |
|---|---|
| F0021 PRD.md, personas.md, nine strict story files, acceptance-criteria-checklist.md | Value, boundary, 55 ACs, screen and mutation interactions |
| F0021 STATUS.md, README.md, GETTING-STARTED.md | Current planning state, role ownership and delivery handoff |
| F0021 feature-assembly-plan.md, bff-api-design.yaml, migration-design.sql, contract-inventory.yaml | Existing technical design, operation ordering, tests, DTO and persistence changes |
| ADR-0082, ADR-0051; three session design schemas | Session transport/CSRF/expiry/logout and shell architecture |
| Registry, roadmap, story index, blueprint, tracker governance | Target identity, dependency ordering, coherent planned status |
| Plan run 2026-11-27-6cda122a manifest and gate-decisions.md | Current base-run-only A+B approval, approved R1/R2 reconciliations |
| docs/plan-review-checklist.md | Eight BRAIN-* rule dispositions in role sections |

## Review and validation outputs

Each role owns one source section: `artifacts/product-readiness.md`, `artifacts/architecture-readiness.md`, `artifacts/buildability-challenge.md`. They are incorporated verbatim into `plan-review-report.md`. `artifacts/test-results/*` holds shell-read/runner stdout; `commands.log` is append-only JSONL telemetry. PR2 core operation outputs and the required local product-check outputs are referenced by lifecycle-gates.log and the run's gate state, and summarized in the combined report. All outputs are within this base run; no feature evidence manifest or index is created.

## Scope exclusions

No product implementation, feature assembly creation, planning repair, approval repair, ontology compilation/regeneration, tracker sync, feature evidence write, production rollout or external message is authorized by this review. Runtime tests, coverage measurement, real-IdP/browser execution and scan results are future F0021 feature work; this audit checks whether their planned contracts are buildable. Shared/downstream artifacts are inspected only for F0021 compatibility or recorded impact. The 80% coverage floor applies to that later implementation proof.
