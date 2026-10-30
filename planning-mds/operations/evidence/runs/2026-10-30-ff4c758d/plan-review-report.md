# Brain feature portfolio plan review — 2026-10-30

## Decision

**CONDITIONALLY READY** under the `plan-review` review-family policy: 0 critical, 3 high, 3 medium, 1 low findings. High findings require repair before the affected feature implementation, or explicit accepted risk with owner and target date. This report grants no new approval or risk acceptance.

**Recommended next action: `plan` for F0006, then `plan-review`, then `feature` after the applicable approvals.** F0006 is ready to enter planning; it has no completed plan to implement. F0065 has recorded Phase A+B approval but still needs upstream delivery and the targeted planning repairs below. There is no unstarted feature ready for immediate full implementation.

Scope is the current `planning-mds/features/**` portfolio, with detailed readiness review of the only nonarchived PRD-bearing feature, F0065. F0001–F0005 archive state was inspected for sequencing context; their runtime completeness was not independently certified through `feature-review`.

Inventory: **67 feature folders; 5 archived; 62 nonarchived.** The nonarchived set contains **61 intentional README-only reservations and one PRD-bearing feature, F0065**. The story index contains 32 stories: 26 archived and 6 unstarted F0065 stories. An intentional reservation is not a missing-plan defect, and KG coverage is not build readiness. The roadmap's Now lane is empty.

## Findings By Severity

### H1 — F0065 completion depends on its own downstream consumers

- **Owners:** Product Manager + Architect. **Fix before:** F0065 implementation/closeout scheduling.
- Evidence: `planning-mds/features/F0065-grounded-gl-guideline-assessment/PRD.md:64` and `feature-assembly-plan.md:22` explicitly make F0024/F0025 downstream consumers. However, `F0065-S0006-reproducible-worked-examples.md:25` requires implemented F0024/F0025 for mandatory runtime reproduction, repeats that dependency at line 42, and retains observed-evidence completion criteria at lines 54–59. Assembly step 7 (line 19) also names the joint integration.
- Impact: a sequence requiring full F0065 completion before starting its consumers cannot close as written. Joint execution may be intended, but no explicit capability handoff or lifecycle exception establishes it.
- Repair: define a capability milestone and valid closeout order, or explicitly rehome/split the reproduction acceptance with tracking in F0024/F0025. Preserve the real end-to-end reproduction requirement.

### H2 — F0065 assessment trace conflicts with the schema it names

- **Owners:** Architect + Backend. **Fix before:** S0003 storage/contract implementation.
- Evidence: `planning-mds/features/F0065-grounded-gl-guideline-assessment/assessment-contract.md:53` calls assessment execution a semantic trace with operation `assessment`; line 55 requires the ADR-0071 schema shape. `planning-mds/schemas/semantic-execution-trace.schema.json:35` accepts only `DOCUMENT_CHAT`, `ENTITY_CHAT`, `SEMANTIC_QUERY`, and `LEARNING_RUN`. The assembly plan's line 41 leaves the schema binding open.
- Impact: the newly required assessment trace has no declared valid operation representation. Implementers must invent a mapping or change the shared contract.
- Repair: specify the assessment/answer-basis mapping, versioned schema extension if needed, and compatible reader behavior; add a validating worked fixture. This is an existing contract mismatch, not a demand for future runtime files to exist today.

### H3 — F0065 leaves the assessment initiation interaction unassigned

- **Owner:** Product Manager, with frontend and architect input. **Fix before:** the S0005 UI handoff.
- Evidence: `planning-mds/features/F0065-grounded-gl-guideline-assessment/PRD.md:24`–30 requires explicit rule selection, on-demand time-scoped evaluation, persisted results and an Entity 360 panel. Its UX section at line 49 specifies display but no entry point or creation flow. `F0065-S0005-explain-assessment-in-entity-360.md:22` begins with an already evaluated assessment, while lines 25 and 27 refer to failed save and creation. S0002 specifies evaluation semantics without assigning the initiation interface. No desktop/narrow ASCII layouts are present in the PRD, as required by the PM role for a UI-bearing feature.
- Impact: a rendered panel could satisfy much of S0005 without a defined way for the user to request the assessment promised by the PRD.
- Repair: assign the initiation entry point, rule/time selection, permitted actions, validation/retry behavior and persisted reload evidence, or explicitly define the panel as read-only and assign creation to a named upstream interface/story. Add desktop/narrow layouts. This review does not invent which product behavior to choose.

### M1 — Downstream Graph acceptance does not carry the rejected-candidate branch

- **Owners:** Product Manager + Architect. **Fix by:** F0014/F0015 planning and before F0024/F0026 acceptance is authored.
- Evidence: `planning-mds/features/F0024-gl-vertical-slice/README.md:39` excludes a direct-vLLM baseline as migration acceptance, and `planning-mds/features/ROADMAP.md:58` requires an accepted Docling-Graph path. F0026's README lines 38–43 also carry Graph-specific gates. In contrast, `planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md:106` records Graph dense rejected for activation; line 108 requires an operator replan-or-reject decision at F0014/F0015 planning. F0014's README lines 26–30 already carries the override and conditional branch; F0015/F0016 carry corresponding guards.
- Repair: propagate that conditional branch into downstream acceptance and the authored shard rationale. Preserve `direct-baseline`/v1 defaults and Accepted ADR-0074 controls unless a new candidate is explicitly replanned and qualified. This does not block F0006 planning.

### M2 — Current status guidance contradicts archived/approved feature state

- **Owner:** Product Manager; Code Reviewer verifies tracker reconciliation.
- Evidence: `planning-mds/BLUEPRINT.md:233` retains F0005 Planned and subsequent story rows retain In Progress/Not Started. Its next-step guidance at line 473 directs the old F0005 handoff and says F0065 awaits review. Archived F0005 `STATUS.md:3` records completion on 2026-10-28 on the approved rejection branch. F0065 `STATUS.md:3` and `PRD.md:9` record plan approval on 2026-10-29, while its `README.md:3`, roadmap line 57 and blueprint line 260 still describe pending/draft planning. Tracker governance line 22 requires the blueprint snapshot to agree.
- Archived story headers also remain stale: F0003 S0001–S0004 each say Not Started at line 8; F0005 S0001–S0004 say In Progress and S0005 says Not Started at line 13. `TRACKER-GOVERNANCE.md:77` prohibits that archive state without a recorded rehoming decision. Feature STATUS/closeout evidence remains authoritative for delivered execution; these header contradictions do not by themselves prove unfinished runtime work. See `artifacts/inventory.json`.
- Repair: refresh the current position and accurately distinguish approved planning, unstarted implementation and unmet prerequisites. Update generated roadmap wording through `kg-source/features/**` and compilation. Preserve historical sections as dated history. All structural tracker checks pass, so they currently do not detect these narrative contradictions.

### M3 — F0065 worked examples omit its newest accepted planning requirements

- **Owners:** Architect + Quality Engineer. **Fix with:** H2 contract binding.
- Evidence: `planning-mds/examples/neurosymbolic-gl/cases.md:5` begins the existing CASE-01–19 table; the four assessment fixtures in `records.json:188` onward do not show the new answer-basis mapping or coarse-time `valid_time_imprecise` boundary. These are now required by F0065 `assessment-contract.md:34` and lines 46–55, and `F0065-S0004-temporal-reassessment.md:24`.
- Repair: add worked and boundary fixtures demonstrating used versus considered-not-used evidence and imprecise valid time, plus schema/reference validation. Keep synthetic examples separate from observed runtime evidence and the frozen holdout.

### L1 — F0064 rollout description is stale

- **Owners:** Product Manager / Technical Writer.
- Evidence: `planning-mds/features/F0064-repository-instructions-and-planning-check-adoption/README.md:3` says rollout pending; line 10 disclaims a published pin. `docs/framework-adoption.md:16` and blueprint framework binding describe rollout complete.
- Repair: distinguish delivered tooling/adoption from any remaining formal feature lifecycle work. Do not infer Done without the applicable evidence.

## Product Readiness

Role lane: Product Manager (`agents/product-manager/SKILL.md`), reviewed independently in parallel with the other lanes.

- The existing Now/Next/Later framework fits dependency-led sequencing; no speculative cost/impact scoring is needed. Confidence is high that F0006 is the next foundation to plan. Operator priority changes or a new accepted scope amendment could change that selection.
- F0065 has bounded outcomes, explicit exclusions, fictional-guideline scope, six measurable stories and recorded plan approval. Approval is acknowledged; the current raw gaps still require repair.
- The other 61 nonarchived features intentionally delegate PRD/story authoring to `plan`. Broad `build` would skip that work.
- F0005 is archived on its permitted rejection outcome: completed qualification is not Graph activation. F0065 is approved planning, not implemented delivery.

## Architecture Readiness

Role lane: Architect (`agents/architect/SKILL.md`).

- Carry F0006 README lines 28–32 into Phase A/B: `OPEN_STATEMENT` and `TYPED_ASSERTION`, origin/interpretation basis, evidence/admission checks and server selectors, mood constraints, and compatible versioned schema evolution. Preserve the v0.1 guard; automated alignment remains F0066.
- F0065 correctly separates accepted facts from model assertions and keeps assessment records outside canonical fact authority. Exact-decimal comparison, immutable lineage, current-grant checks, consistent snapshots and temporal abstention are specified.
- F0065 still depends on F0006–F0020 for its kernel/evaluator and F0021–F0023 for its UI. Assembly lines 26 and 40–45 explicitly assign future snapshot, transaction, DTO/OpenAPI, permission, conflict/completeness and reason bindings. Finish those decisions against delivered upstream contracts before the corresponding implementation. Their future runtime paths are not missing artifacts in this audit.
- Proposed ADR proof obligations remain open; structural validation does not accept those ADRs or certify runtime behavior. Retain the fictional guideline in v0.1 and F0026's real-authority/release qualification gate.

## Buildability Challenge

Role lane: Code Reviewer (`agents/code-reviewer/SKILL.md`).

- F0006 requires a complete `plan` handoff before feature Step 0. Its zero stories and retrieval exclusion accurately describe its present state.
- F0065 has explicit layer ownership and useful evaluator, snapshot, idempotency, revocation and independent-expectation tests planned. H1–H3 prevent an unconditional implementation handoff; upstream contracts are also undelivered.
- A reserved ID, a planning-only KG binding, a synthetic fixture, a prior approval and a completed runtime test are different evidence types. None substitutes for the others.
- No implementation code review, full security signoff, runtime test execution, deployment check or archived `feature-review` is claimed here.

## Brain Review Checklist

These outcomes apply to the substantive F0065 plan. F0006 and the other reservations are not completed plans; full per-rule review awaits their PRDs/stories. Archive documents were used only for sequencing and status context.

| Rule | Outcome | Feature-specific evidence / boundary |
|---|---|---|
| BRAIN-SCOPE | Partial | F0065 PRD scope/outcomes/exclusions lines 21–47; H3 leaves the user initiation contract incomplete. |
| BRAIN-AUTHORITY | Partial | PRD line 65 and assembly line 34 preserve proposed proof obligations; H2 requires a coherent trace contract. |
| BRAIN-EVIDENCE | Pass in design | Assessment contract lines 40–55: exact versions, lineage, immutable assessment outside canonical truth. |
| BRAIN-PARSE-ONCE | Pass in design | Assessment contract line 61: historical reconstruction reads stored facts/rules without rerunning extraction; no parser change proposed. |
| BRAIN-TEMPORAL | Pass in design | S0004 lines 22–27 and contract lines 17–21, 34, 57–61: coordinates, consistent snapshot, imprecise-time abstention, immutable history. |
| BRAIN-AUTHORIZATION | Pass at architecture review level | Contract lines 63–67 and S0005 line 26: current grants, complete lineage, denied disclosure/revocation; runtime security signoff remains future. |
| BRAIN-BUILDABILITY | Partial | Named owners and prerequisites exist; H1–H3 and future contract decisions prevent an unconditional build handoff. |
| BRAIN-EXAMPLES | Partial | S0006 preserves reproduction/holdout boundaries; M3 lacks examples for the newest precision/answer-basis requirements. |

## Validation Evidence

All seven required PR2 checks exited **0**. See `lifecycle-gates.log`, `commands.log`, `artifacts/pr2-driver-output.json`, and the product-check output/result files under `artifacts/project-checks/`.

| Required check | Result / scope |
|---|---|
| Planning approval history | PASS; project scope resolves F0065. No approvals were edited. |
| Story validation | PASS; driver resolves the sole nonarchived PRD-bearing feature, F0065. Reserved features have no story target. |
| Tracker validation | PASS; does not invalidate the narrative contradictions identified in M2. |
| KG integrity | PASS. |
| KG drift | PASS. |
| Framework templates | PASS. |
| Brain plan-readiness extension | PASS; JSON status `pass`, no structural findings. |

The severity-policy command is recorded separately in `artifacts/readiness-policy.json`. No failing check was waived. No source changed during this audit, so no index regeneration was needed. A structural pass does not resolve semantic or interaction gaps found in raw documents.

## Recommended Next Actions

1. **PM targeted reconciliation:** correct current F0005/F0065/F0064 guidance and downstream Graph wording, updating authored shards and regenerating their projections. This is follow-up work, not an edit performed by this review.
2. **`plan`, F0006:** PM Phase A defines the bounded requirements/stories; Architect Phase B defines admission, data, evidence, versioned contracts and ontology bindings. Record the action's approval decisions normally. Do not infer approval from this audit.
3. **`plan-review`, F0006:** PM + Architect + Code Reviewer challenge the completed plan and run the product checks.
4. **`feature`, F0006:** after readiness and approvals, Architect authors/reconciles the implementation assembly plan and assigns required signoffs. Backend, AI, QE, security and DevOps apply according to actual scope; frontend applies if there is a UI change.
5. **Later sequencing:** F0007–F0017 foundations → F0018–F0023 commits/temporal reads/360 → repaired and reviewed F0065 → F0024/F0025 integration → F0026 qualification. At F0014/F0015 planning, resolve the recorded Graph replan-or-reject decision. Keep broader retrieval, chat, process and generalized reasoning in their existing later phases.

## Artifact Trace

See `artifact-trace.md`. Findings were checked against raw feature/ADR/schema artifacts. Source precedence follows product instructions; KG lookup was routing context only. The three role lanes supplied independent file/line-backed findings. Duplicate issues were consolidated; stale Graph/status prose is medium because governing outcomes and repair owners are explicit, while F0065's active completion/trace/interaction gaps are high. No missing build-critical owner was found, so the special NOT READY owner rule does not apply.

All repair actions remain recommendations. No product source, plans, trackers, KG, approvals, canonical feature evidence, or remote services were changed.
