# G0 — Architect Assembly Plan Validation — F0001 run 2026-09-12-855d2b93

**Role:** Architect
**Primary spec:** `planning-mds/features/archive/F0001-repository-and-engineering-foundation/feature-assembly-plan.md`
**Mode:** clean remediation rerun

## Remediation Scope

This rerun changes no semantic capability, canonical node, or KG binding surface. It
addresses the F0001-S0006 credential-audit finding, stale archived feature status
documents, and incomplete closeout evidence from the prior run.

## Step 0 — Author

`feature-assembly-plan.md` already existed (authored 2026-09-06 during the plan run
`2026-09-06-cdb5d8cb`'s Phase B, then further reconciled uncommitted on 2026-09-08 alongside
ADR-0057 — Label Studio replaced by the native Nebula Review Panel — and ADR-0059 — provider-neutral
content-artifact storage). Per the drift-reconcile judgment (`if PRIMARY_SPEC is absent, author it
... on drift-reconcile/rerun, reconcile the existing plan instead of overwriting`), the plan is present
and current, so this gate reconciles/validates it rather than re-authoring:

- Cross-checked "Governing Decisions" against current ADR statuses: ADR-0054 (amended by ADR-0057,
  ADR-0059), ADR-0055 (Accepted, Phi-4-mini-instruct on vLLM), ADR-0057 (Accepted 2026-09-08), ADR-0059
  (Accepted 2026-09-08). No stale references to Label Studio or an external review task remain in the
  plan text.
- Cross-checked each of the plan's 8 build steps against the corresponding story
  (F0001-S0001..S0007) for title, scope, and ADR references — S0004's step 6 ("Native review round
  trip") matches the story's ADR-0057/ADR-0058 framing exactly; S0006 is correctly split across step 3
  (access) and step 7 (hosting/restore).
- The five architecture decisions once open at Phase B (object store, Docling-Graph pin, authentik
  version, webhook trust, recorded-interval policy) are deliberately **not** resolved here: the plan's
  Governing Decisions section states each is settled by its owning proof story's measured outcome
  (S0003, S0004, S0005, S0006) and finalized at S0007 ("Record proof outcomes and settle the pre-build
  contracts"). Object store is already settled (ADR-0059, LocalFilesystemObjectStore) ahead of schedule.

## Step 0.5 — Validate

- [x] **Scope split matches feature story requirements** — Build Order table step-to-story mapping
  covers all 7 stories with no gaps or overlaps; "Existing Code (Must Be Modified)" correctly states
  None (runtime roots do not exist yet).
- [x] **Agent dependencies identified** — Build Order rationale column states inter-step dependencies
  (e.g., step 3 before step 6: "S0004 needs verified reviewer principals"); Dependency Order section
  present (line ~521).
- [x] **Integration checkpoints are feasible** — Checkpoints A–F declared after steps 2–7, each tied to
  a concrete runtime artifact (compose stack up, principal resolution live, artifact bundle written,
  etc.) plus a final Cross-Story Verification step.
- [x] **No missing or conflicting artifact ownership** — New Files table assigns each path to exactly
  one layer/owner (backend-developer: `engine/`; ai-engineer: `neuron/`; frontend-developer:
  `experience/src/review-panel/**`; devops: `docker*`, `docker/DEPENDENCY-MATRIX.md`); no path appears
  under two owners.
- [x] **Knowledge-Graph Binding Plan present** — declares intended `kg-source/bindings/**` globs for
  all 10 capabilities in `kg-source/features/F0001.yaml`, to be authored as shards at G7 (not hand-edited
  into `code-index.yaml` now). Feature-shard status transition `architecture-complete → in-progress`
  at this gate is recorded as a to-do (see Follow-ups).

## Required Signoff Roles (STATUS.md)

Already initialized by the Architect at the Phase B plan run (2026-09-06): Quality Engineer,
Code Reviewer, Security Reviewer, DevOps, and Architect all `Required = Yes`, each with a stated
reason. No changes needed at this gate — risk profile (identity/authorization in S0004/S0006,
containers/CI/restore in S0002/S0006) still matches.

## Outcome

**PASS.** The assembly plan is authored, internally consistent with current stories and ADRs, and
satisfies all four Step 0.5 checks. No re-authoring required.

## Follow-ups (non-blocking, tracked for later gates)

- `kg-source/features/F0001.yaml` `status` should move `architecture-complete → in-progress` as part
  of this run (plan says "at feature G0"); recorded here, applied via the standard kg-source edit +
  `compile.py` path rather than hand-editing the generated registry tables.
- Pre-existing uncommitted working-tree changes (ADR-0057/0059 authoring, story/PRD/STATUS text
  reconciliation) predate this run and are carried forward as this run's baseline; they will appear in
  `artifact-trace.md` / `changed_paths` alongside this run's own edits.
