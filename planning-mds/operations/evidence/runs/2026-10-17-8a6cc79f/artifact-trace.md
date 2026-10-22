# Artifact trace — F0004

## Artifacts Read

- planning-mds/features/F0004-content-artifact-model/PRD.md
- planning-mds/features/F0004-content-artifact-model/feature-assembly-plan.md
- All four local story files and STATUS.md.
- planning-mds/BLUEPRINT.md and planning-mds/architecture/SOLUTION-PATTERNS.md
- planning-mds/api/brain-api.yaml (content GET contracts).

## Artifacts Created Or Updated

| Artifact | Owner | Basis |
|---|---|---|
| g0-assembly-plan-validation.md | Architect | Raw four stories, approved assembly plan, blueprint, SOLUTION-PATTERNS and content GET contract |
| artifacts/lookup-tier1.txt | Orchestrator | F0004 tier-1 KG routing output |
| artifacts/lookup-tier2.txt | Orchestrator | F0004 tier-2 KG routing output |
| artifacts/diffs/changed-files.txt | Orchestrator | Current tracked and untracked runtime/test/config scope; refreshed for review |

## Generated Evidence

Lookup tier outputs and G0 gate/validator diagnostics are under artifacts/.
Runtime tests, coverage, build/schema deployment and all four security scan classes have run; see the current acceptance and review artifacts below.

## External Or Global Evidence References

Planning baseline: `../2026-10-17-620b7618/`. Its reconciliation report preserves
the older approval history. F0001/F0002/F0003 are dependencies named by lookup
and the approved plan; runtime proofs must recheck their impacted consumers.
No global frontend lane is substituted for feature evidence.

## Omissions And Waivers

None. Future-stage required evidence is pending, not waived.

## G1 generated failure evidence

- g1-runtime-preflight.md — DevOps FAIL, no runtime waiver.
- artifacts/test-results/docker-version.txt
- artifacts/test-results/docker-compose-preflight.txt
- artifacts/test-results/docker-compose-fallback-preflight.txt
- artifacts/test-results/runtime-availability.json

These outputs establish runtime unavailability only, not application failure.


## Runtime acceptance and review evidence

| Artifact | Owner | Basis |
|---|---|---|
| test-plan.md / test-execution-report.md | Quality Engineer | All 25 approved ACs; actual engine/neuron/restore jobs and raw logs |
| coverage-report.md / artifacts/coverage/changed-runtime.json | Quality Engineer | Measured changed executable statements and combined runtime lanes |
| g2-self-review.md | Implementation roles | Strict contracts, authority/ownership, retries, historical dates and compatibility |
| g2-deployability-check.md / deployability-check.md | DevOps | Locked builds, packaged contracts, isolated migration and actual restore |
| artifacts/security | Security | Dependency audits, Semgrep SARIF, scoped secret scan and passive OpenAPI DAST |
| code-review-report.md | Independent Code Reviewer | Current worktree/ACs, actual date-race reproduction, tests and architecture |
| security-review-report.md | Independent Security Reviewer | Ten dimensions, STRIDE, advisory reachability and bounded METS polyglot probe |
| artifacts/review | Independent reviewers | Bounded reproductions and independent post-fix checks |

Original runtime failures and initial G3 findings remain retained. A failed scan
or initial review is not relabeled as a clean raw result after mitigation.
G4 approval, G5 signoff and G6–G8 closeout artifacts remain pending.
