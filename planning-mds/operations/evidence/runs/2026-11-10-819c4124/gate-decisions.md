# Gate Decisions — F0064-repository-instructions-and-planning-check-adoption run 2026-11-10-819c4124

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager (Claude) | 2026-11-11T04:07:42+00:00 | Three scope questions answered by the operator; no product business rule involved | No | G2 tracker sync |
| G2 | PASS | Product Manager (Claude) | 2026-11-11T04:08:11+00:00 | Four stories pass strict validation; STORY-INDEX regenerated; trackers 0 errors/0 warnings; Brain plan-readiness passes for F0064 and at project scope; BLUEPRINT 3.3 lists F0064 | No | G3 operator review |
| G3 | PASS | Operator token; Product Manager attestation | 2026-11-11T04:18:54+00:00 | Explicit approve-phase-a recorded; checkpoint attested and approve-plan.py Phase A operation completed | No | Phase B |
| G4 | PASS | Architect (Claude) | 2026-11-11T04:18:54+00:00 | Three capability nodes, f0064 bindings and four story mappings compiled; coverage exclusion removed; drift check exited 0 | No | G5 architecture review |

## Clarification Judgment (G1)

F0064 is retroactive: the tooling shipped on 2026-09-07 without a feature lifecycle. The delivery record (`planning-mds/framework-adoption-plan.md`, `docs/framework-adoption.md`) left three scoping questions for the closeout. The operator answered them on 2026-11-10:

1. **Scope boundary.** Decision: Brain-side deliverables only (manifest, instructions, checklist, validator and fixtures, compatibility entry point, CI wiring, contributor/workspace docs). The generic mechanism is framework F0009, consumed at the pinned revision and not re-proven here.
2. **Untested native host adapters.** Decision: explicit non-goal with no reserved feature ID. The shared CLI with an explicit product root is the supported path.
3. **Defects found by re-verification.** Decision: fix everything before closeout, including any defect that needs a framework change and pin advance. Nothing is deferred.

The PRD records one PM assumption labelled for G3 review: pin agreement between CI and BLUEPRINT section 0 stays a documented manual rule verified at closeout, with no new automated guard.

## Approval Checkpoints

The instruction to run the closeout is not a review approval. A manual checkpoint is attested only after the operator explicitly approves the corresponding reviewable artifacts.

## G3 Review Package

Phase A is ready for operator review:

- [PRD](../../../../features/F0064-repository-instructions-and-planning-check-adoption/PRD.md). Brain-side scope, explicit exclusions (framework F0009, native host adapters, new checks, runtime behavior), no UI, and persona Dana the Platform Engineer.
- Four stories with 23 acceptance criteria:
  - S0001 manifest (5 ACs)
  - S0002 instructions and checklist (5 ACs)
  - S0003 validator (7 ACs)
  - S0004 CI and setup docs (6 ACs, including the repair of the stale adoption documents found in L1)
- STATUS (G1 decisions, no deferrals allowed) and GETTING-STARTED.
- One PM assumption: pin agreement between CI and BLUEPRINT section 0 stays a manual rule, with no new automated guard.

Validation output is in `artifacts/test-results/phase-a-*.log`: strict story validation, tracker validation and Brain plan-readiness all exit 0.

G3 has no PASS decision until the operator approves. The plan manifest stays draft. Phase B binds the delivered files in the KG, removes the coverage exclusion, sets the role matrix and writes the assembly plan.

## Explicit Phase A Approval

- **Token:** `approve-phase-a`
- **Source:** operator reply in the plan session, given after the G3 review package was presented (PRD, four stories and 23 ACs, STATUS, GETTING-STARTED, the G1 decisions and the PM assumption)
- **Timestamp:** 2026-11-11T04:16:02+00:00
- **Scope:** Phase A requirements as drafted. The PM assumption is accepted with the package: CI/BLUEPRINT pin agreement stays a manual rule verified at closeout, with no automated guard. The roadmap lane stays Now.

## Phase B Design Decisions and G5 Review Package

The Architect authored:

- the [feature assembly plan](../../../../features/F0064-repository-instructions-and-planning-check-adoption/feature-assembly-plan.md). It is a verification-only infrastructure variant with four steps, one per story, giving exact commands and expected results.
- three capability nodes, each bound to the delivered files:
  - `project-context-manifest`
  - `plan-readiness-validation`
  - `project-check-ci-enforcement`
- the `bindings/f0064.yaml` shard, four story mappings, and removal of the coverage exclusion.
- the required role matrix in STATUS, a row in the umbrella assembly index, and the GETTING-STARTED retrieval note.

No ADR, API, schema, permission or runtime file was created.

**Review points:**

1. **Expected source change is documentation only.** The two stale adoption documents get refreshed (S0004 AC6). The CONTRIBUTING line-26 KG-test claim is repaired if a fresh `scripts/kg/tests` run shows it is stale. Any other change is logged as a defect repair.
2. **Negative paths run on temporary copies,** never on the working tree: a missing instruction file, a broken checklist through the real shared executor, and invalid invocations.
3. **Framework defects still block closeout.** If Step 1.5 shows the framework silently omits a missing instruction file, the fix lands in `nebula-agents` and the pin advances in CI and BLUEPRINT section 0 together (G1 decision 3).
4. **Roles:** Quality Engineer, Code Reviewer and DevOps are required. Security is not required: there is no authn/authz or data-boundary change, and the manifest forbids shell evaluation. Architect is not required: no ADR or risk exception.

**Known trade-offs:**

- `hint.py` is silent for root-level paths by design; `lookup.py` by capability ID resolves them.
- Pin agreement stays a manual check (accepted with Phase A).

## Explicit Phase B Approval

- **Checkpoint:** `approve-phase-b` (G5)
- **Operator token:** `approve-phase-b`
- **Source:** operator reply in the plan session, given after the G5 review package was summarized: the assembly plan, three capability nodes and bindings, the role matrix, four review points and two known trade-offs
- **Recorded by:** Architect (Claude)
- **Recorded at:** 2026-11-14T17:04:17+00:00
- **Precondition met:** all seven G5 pre-checkpoint exit operations completed in declared order with exit 0, and the driver paused at `approve-phase-b`.
- **Scope approved:** the verification-only F0064 Phase B design for four stories and 23 ACs, including the four review points and two known trade-offs listed above.

**Approval-status edits made before attestation:**

- feature STATUS, README, PRD and assembly plan;
- the BLUEPRINT §3.3 line;
- the F0064 feature shard approval note.

**Unchanged:**

- All four stories remain Not Started; they are verified in the feature run.
- No ADR, API, schema or runtime file is created.
- The feature shard's `validation_gate` is unchanged.

**Next:**

- This approval evidence is frozen for attestation.
- G5 resumes with the post-approval KG refresh, tracker validation and approve-plan.py.
- No planning-source edit follows the final refresh.
