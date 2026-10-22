# Action Context

## Run Identity

NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain.
Action feature; F0004-content-artifact-model; run 2026-10-17-8a6cc79f;
mode clean (resuming same run); contract version/effective date 2026-07-11;
prior feature-completion run/rerun_of null.

## Inputs

Operator selected this run/root and requested G1 first on resume. The feature
operator contract governs implementation through closeout. Latest planning run
2026-10-17-620b7618 remains approved; three older approvals were reconciled under
prior operator authorization. Branch docs/f0004-plan-review-rework is unchanged.
No commit, push or merge is assumed.

## Assumptions

Continue the authorized feature action through its ordered gates; planning approval does not imply implementation signoff.

## Scope Boundaries

F0004 S0001–S0004 and approved integration surfaces; Python product stack.
No UI, new grant, public mutation route, model engine, canonical fact writes,
or production Graph activation. ADR-0073 stays Proposed until accepted proofs.
Default human/source verifiers deny. Shared development DB is not migrated.

## Lifecycle Stage

### Current position (2026-10-20)

G0–G8 PASS; explicit G4 approval and all twenty required current story/role verdicts are recorded. G1 was rechecked first on resume; Step 1a received the
Architect exit before the v2 implementation. Three locked application jobs are
healthy. Implementation and scoped G2 acceptance evidence are retained in
README, test-execution-report.md, coverage-report.md and deployability-check.md.

G3 independent Code Reviewer and Security Reviewer reports pass with recommendations;
the ordered G3 validator passed. Security confirmed SEC-H1: a gzip archive with appended PDF bypassed the prior
allowlist because detection occurs first. The exact initial-byte PDF guard is
now verified in both modes. A reproduced date read race is corrected by a
shared version lock. Final source regression: engine 229 pass; neuron 93 pass
and four optional skips; restore four pass; changed runtime 90.60%. Do not treat the earlier G2 result as a
security signoff. All scanner findings and initial failures remain recorded.

The v2 writer flag remains false. No production Graph activation, commit,
push, merge, shared DB migration or implementation signoff occurred.

## Closeout position

The user explicitly approved G4 on 2026-10-21. All four stories passed the five
required roles; G5/G6/G7 passed. The feature is archived, the manual archive
checkpoint is attested, prior completion manifests were patched before the new
latest-run pointer, and this manifest is approved. Final G8 executable evidence, scoped tracker and plain graph validations passed;\nresults are in lifecycle-gates.log.

No new run, production activation, shared migration, commit or merge is implied.

## Runtime safety

Use run-scoped Compose jobs. Do not recreate dependencies or inspect secrets.
Tests own fresh DBs/schemas and unique restore containers/directories. Only the
restore job uses Docker socket/client access for its isolated operator drill.

## Run Environment

Absolute cwd records identify the selected host product root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain. Framework gate commands run in sibling nebula-agents; application validation executes inside run-scoped containers. Host restore diagnostics are superseded by the final application-job proof.
