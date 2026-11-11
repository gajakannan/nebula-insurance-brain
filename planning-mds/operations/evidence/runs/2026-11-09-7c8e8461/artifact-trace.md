# Artifact Trace

## Artifacts Read

- Framework: agents/actions/{plan-review,feature-review}.md and matching spec YAML; agents/ROUTER.md, agent-map.yaml, AGENT-USE/AGENT-OPS; PM, Architect, Code Reviewer, QE, Security and DevOps role skills.
- Product instructions: .agentignore, .nebula-project.yaml, planning-mds/BLUEPRINT.md, docs/agent-instructions.md, docs/plan-review-checklist.md.
- Scope: planning-mds/features/archive/F0007-factslot-model/{README,PRD,STATUS,GETTING-STARTED,feature-assembly-plan,acceptance-criteria-checklist,worked-examples}.md, six strict story files, contract-examples.json.
- Governing raw ADR-0077, design schemas, existing data/solution patterns and F0007 KG mappings/bindings; lookup is a routing aid only.
- Completion index planning-mds/operations/evidence/features/F0007-factslot-model/latest-run.json and selected manifest planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/evidence-manifest.json.
- Only manifest/report-cited role, preflight, test, coverage, scan and post-CI evidence needed for this audit. Exact paths appear in the report and command logs; no blanket retrieval of the cold evidence archive.
- Actual ff0a619..fa8fc1d diff and relevant raw runtime/test/migration/config files; planning approval history for 2026-11-09-60865e32.

## Artifacts Created Or Updated

Only the two new audit run packages 2026-11-09-7c8e8461 and 2026-11-09-8b8456df, plus temporary audit runners under /tmp. No source, tests, plan, schema, graph, tracker, canonical run or latest-run pointer changes.

## Generated Evidence

- README.md
- action-context.md
- artifact-trace.md
- artifacts/architect-final-notes.txt
- artifacts/architect-postgres-proof.md
- artifacts/architect-postgres-raw.json
- artifacts/architect-probes.json
- artifacts/architect-probes.py
- artifacts/architect-review.md
- artifacts/code-diff-impact.txt
- artifacts/code-review.md
- artifacts/code-risk.txt
- artifacts/exact-defect-citations.txt
- artifacts/kg-check.txt
- artifacts/kg-lookup.txt
- artifacts/local-plan-check.txt
- artifacts/plan-approvals.txt
- artifacts/pm-citation-lines.txt
- artifacts/pm-feature-artifacts.txt
- artifacts/pm-prd-read.txt
- artifacts/pm-story-review.txt
- artifacts/pr0.txt
- artifacts/pr1.txt
- artifacts/pr2.txt
- artifacts/prd-nfr-read.txt
- artifacts/project-checks/PR2-plan-readiness-ccf021a5b3a547cb8df00b3b61471543.result.json
- artifacts/project-checks/PR2-plan-readiness-ccf021a5b3a547cb8df00b3b61471543.stderr.txt
- artifacts/project-checks/PR2-plan-readiness-ccf021a5b3a547cb8df00b3b61471543.stdout.json
- artifacts/project-context-plan.txt
- artifacts/project-doc-and-generator.txt
- artifacts/project-plain-kg.txt
- artifacts/qe-devops-skills.txt
- artifacts/readiness-verdict.txt
- artifacts/role-notes.txt
- artifacts/semantic-examples.txt
- artifacts/story-index-tool.txt
- artifacts/story-validation.txt
- artifacts/template-validation.txt
- artifacts/tracker-validation.txt
- commands.log
- gate-decisions.md
- gate-state.json
- lifecycle-gates.log
- plan-review-report.md

## External Or Global Evidence References

No external publication, messaging, PR/issue or global evidence substitution. The existing Compose PostgreSQL service was inspected; SQL proofs evaluated expressions without persistent reads/writes. Historical scan outputs were inspected, not refreshed.

## Omissions And Waivers

No waivers requested or granted. No UI/AI scope, active deployment, fresh full integration suite or fresh vulnerability scan. Full historical raw test counts and fresh 118-test unit baseline are distinguished in the feature report. Security lane final-report failure was completed conservatively by primary source/artifact review and safe proof reruns; no independent full-scan claim.

## Run Environment

Product checkout fa8fc1d, framework consumed in place, existing locked engine virtual environment, existing healthy brain-postgres. Initial Docker socket sandbox denial retained; successful inspection/SQL used approved escalation. Shared application database/schema and services unchanged. Scratch probe allocations were capped, with no network target.
