# Plan Review Report: F0009 Provenance and Human-Correction Lineage

**Run:** `2026-11-24-2af6f972` (action `plan-review`, policy 2026-07-11)
**PLAN_SCOPE / TARGET:** feature / F0009
**NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (source: environment)
**Reviewed plan run:** `2026-11-24-bfdbbf04` (plan, A+B, manifest `approved`)
**Reviewed tree:** product HEAD `2613b0b` on branch `fix/F0011-feature-review-findings`. The F0009 plan package is uncommitted in the working tree, and this review read it as found.
**Reviewer session:** fresh. It is not the session that produced the plan.

## Decision

**CONDITIONALLY READY.** Critical 0, High 2, Medium 2, Low 5 (`gate_policy.py --profile review-family --variant plan`).

The F0009 package is substantive and close to buildable. The PRD, six stories, and 41 ACs are explicit. The assembly plan names exact files, carriers, SQL guards, lock order, and an AC-to-proof map. Its claims about shipped code held up when checked against the source: the stale branch omits value/evidence/comment, `mutate` stages audit before the operation, migration head is 0015, `CanonicalFactChangeRow` has no actor/commit column, and composite owner keys exist.

Two High findings must be fixed in the plan, or accepted as explicit risk with an owner and target date, before `feature.md` starts:

- **PR-H1:** the replay rule poisons the event hash of a sibling refused only because of another item in its batch.
- **PR-H2:** the `provenance-result/v1` edge vocabulary has no defined direction or endpoint kinds.

Both route back to the Architect through a targeted PHASE=B plan rework. Every build-critical area has an owner.

## Findings By Severity

| ID | Severity | Owner (section) | Summary | Evidence |
|---|---|---|---|---|
| PR-H1 | High | Code Reviewer (Buildability) → Architect rework | A prior `BATCH_REFUSED` attempt makes a valid later resubmission of that item permanently return 422 | feature-assembly-plan.md Step 3 items 3–4 (lines 194–195); migration-design.sql line 43; decisions.py `compute_event_sha256` lines 53–63 |
| PR-H2 | High | Architect (Architecture) | `provenance-result/v1` edge kinds have no direction or allowed (source kind → target kind) pairs, and `review_attempt` has no linking edge | provenance-result-v1.schema.json `edges`; feature-assembly-plan.md lines 95–99, 152; contract-examples.json `provenance-result-v1-valid` has `edges: []`; S0006 AC5 |
| PR-M1 | Medium | Code Reviewer (Buildability) | The reservation guard equates `review_decision.decided_at`, which is `timestamp without time zone`, with `reserved_at timestamptz`, and the plan states no conversion rule | migration 0002 line 91; models.py line 344; migration-design.sql line 14; feature-assembly-plan.md lines 31, 163 |
| PR-M2 | Medium | Architect (Architecture) | contract-inventory.yaml lacks fields that shipped `sources.yaml` entries require. This repeats F0011 plan-review PR-M2 | contract-inventory.yaml lines 66–103 vs scripts/contracts/sources.yaml entries |
| PR-L1 | Low | Code Reviewer (Buildability) | Retained stale value/evidence/comment becomes visible through the legacy `GET /reviews/{id}` decision projection. The plan does not call out this value change | schemas/review.py `ReviewDecisionOut` lines 39–74; feature-assembly-plan.md lines 33, 207 |
| PR-L2 | Low | Code Reviewer (Buildability) | Two gaps under the new preflight: what happens when one batch names the same review item twice, and the outcome and status for a "fingerprint changed, retry as a fresh operation" refusal | feature-assembly-plan.md Step 3 items 2 and 4 (lines 193, 195) |
| PR-L3 | Low | Architect (Architecture) | Every KG story mapping copies the same four `uses_schema` entries and the same `governed_by` (0080/0010/0037). Per-story bindings are imprecise | kg-source/features/F0009.yaml `story_mappings` |
| PR-L4 | Low | Product Manager (Product) | Story grammar: "I want to my effective correction…" (S0005) and "I want to the lineage contract…" (S0006) | S0005 line 13; S0006 line 13 |
| PR-L5 | Low | Product Manager (Product) | The S0006 Interaction Contract row is generic mutation boilerplate ("stale/blocked/duplicate outcomes follow the ACs") that does not describe an operator migration entry point | S0006 line 37 |

## Product Readiness

Owner: Product Manager.

| Rule | Outcome | Evidence |
|---|---|---|
| BRAIN-SCOPE | PASS | PRD §Scope & Boundaries (lines 26–44) names in-scope items 1–6 and the out-of-scope owners F0010/F0016/F0018/F0020/F0022/F0023/F0026/F0041/F0042/F0056. Six stories carry 7/8/7/7/6/6 = 41 numbered, testable ACs. acceptance-criteria-checklist.md indexes all 41 |

Assessment:

- **User value and non-goals.** The value is explicit: attributable answers to "why do we believe this" and "who corrected it". A2 records the approved minimal reading of the §88 reservation (PRD line 98). No business rule is invented. Assumptions A1–A3 are traceable to master blueprint §§17/75/88 and ADR-0010/0037/0044.
- **Mutation stories.** S0002, S0005, and S0006 name the entry point (existing `POST /reviews/batches/{id}/decisions`; the operator migration for S0006), roles, non-applying states (stale, BLOCKED, replay, competing, unresolved evidence), atomic persistence, fresh-session reload proof, and audit. Render-only behavior is explicitly ruled out. S0006's interaction row is boilerplate (PR-L5), but the assembly plan's Mutation Traceability row for 0016 fully specifies the operator path, so this is Low.
- **UI.** The PRD records an explicit "No UI" justification (lines 61–67). F0022/F0023 own display. Personas reuse existing Rosa/Ingrid/Mateo with no new roles.
- **Roles.** The PRD role matrix (lines 82–89) covers TenantMember, Reviewer, ServicePrincipal, and unverified/nonmember/cross-scope/external callers. The prose `review:annotate` is mapped to the real `review_task:annotate` resource in assembly plan line 210. Acceptable.
- **Trackers.** STATUS, README, REGISTRY (Planned), ROADMAP (Now), STORY-INDEX, and BLUEPRINT §3/§4.18 agree on Planned, 0/6 stories, and both approvals. Grammar defects are recorded as PR-L4.
- **Placeholders.** No TODO, TBD, or vague build-critical wording was found in the PRD or stories. "Phase B specifies…" deferrals in the stories are all resolved in the assembly plan (limits, error categories, migration procedure).

## Architecture Readiness

Owner: Architect.

| Rule | Outcome | Evidence |
|---|---|---|
| BRAIN-AUTHORITY | PASS | ADR-0080 is Proposed and its proofs are gated to feature G2/G3/G5 plus explicit acceptance (ADR-0080 lines 67–76). PRD line 100 keeps ADR-0075/0079 Proposed. No plan text claims acceptance |
| BRAIN-EVIDENCE | PASS | S0001 AC1–AC5 and assembly plan Step 4 (completeness rules at line 266, gap reasons at line 105) tie every explanation to stored evidence, with explicit INCOMPLETE/DERIVATION_UNAVAILABLE |
| BRAIN-PARSE-ONCE | PASS | S0001 AC6 requires zero Docling parses and model calls. The reader reads persisted metadata only (assembly plan line 262) |
| BRAIN-TEMPORAL | PASS | S0003 AC1–AC7 and Step 5 (lines 272–277) preserve valid/recorded coordinates, same-slot `split_of_version_id`, and `ending_refs`, with no mutation of close-only rows |
| BRAIN-AUTHORIZATION | PASS | Step 4 items 1–6 (lines 255–260) run anchor READ, then metadata discovery, then source READ for every key before materialization. S0004 AC1–AC7 carries the negative test plan. No new grants (line 210) |
| BRAIN-EXAMPLES | PASS WITH FINDING | worked-examples.md EX-PROV-001–005 gives definition, worked case, boundary, and owner. Glossary adds Provenance Explanation, Learning Candidate Reservation, and Refused Review Submission. contract-examples.json has 16 structural cases. The result examples contain no edges, however, which contributes to PR-H2 |

Assessment:

- **API/schema.** No new route; this is justified (PRD A1; assembly plan lines 204–210). Four new design schemas exist under `planning-mds/schemas/` (untracked). `review-decision.schema.json` is unchanged.
  - **PR-H2 (High).** `provenance-result-v1.schema.json` constrains `edges[].kind` to 14 names and each endpoint to 12 record kinds independently. Nowhere in the schema, assembly plan (`ProvenanceEdge.kind: str # exact enum`, line 97), ADR-0080, or examples are the direction and allowed endpoint kinds defined for any edge kind. Examples of the open questions: is `corrected_from` child→original? Is `reviewed_by` assertion→review_decision, and does it also cover review_attempt? Which edge connects a `review_attempt` record (an exposed record kind, Step 4 item 4) to the graph? Is `derived_from` target always `derivation_reference`?
  - Why PR-H2 is High: the plan sorts edges deterministically and requires all endpoints to be present (line 152). S0006 AC5 has QE author expected edges independently, before implementation. F0020/F0022/F0023 will consume v1 later. Leaving this to implementers forces them to invent a frozen v1 contract semantic.
  - Fix for PR-H2: add an edge table (kind, source kind, target kind, meaning) to the schema description or the assembly plan, plus one or more example edges per kind in contract-examples.json, and an invariant that every non-root record is reachable.
- **Data model and migrations.** migration-design.sql gives complete DDL for both tables, with composite owner FKs backed by the existing 0005/0006 owner keys (verified in migration 0006, `CHAINS` and `NEWLY_OWNED`). There are unique decision and child keys, and the attempt FK to `audit_event` is satisfiable because `mutate` stages audit before `operation` (execution.py lines 466–481). Downgrade guard and lock order are specified.
  - `review_decision` currently has no append-only trigger; migration 0007's `APPEND_ONLY` covers only `audit_event` and `authentication_event`. The plan's "added if absent after inspecting" therefore resolves to "add". Not a finding.
- **Authorization model.** Resources, actions, and constraints are named with real policy strings, and there is no Casbin edit. `AuthorizationExecution.read` already has the `load` + `additional_reads` shape that the `prepare_reads` extension builds on (execution.py lines 356–418).
- **ADRs and NFRs.** ADR-0080 covers the consequential decisions with options and proof gates. Traversal limits are concrete (256/2048/8192 plus F0011 limits). No latency target is invented; this is justified at PRD line 93.
- **Contract inventory.**
  - **PR-M2 (Medium).** Each shipped `scripts/contracts/sources.yaml` resource carries `version`, `id`, `source_sha256_at_design`, `owner`, `disposition`, `consumer_entry_points[{entry_point,path,state}]`, `compatibility_tests[{path,state}]`, `version_selector` and `wire_profile`. contract-inventory.yaml supplies only name/source/producer/consumer/profile, and its consumers for `provenance-result-v1` are prose ("internal engine consumers and future F0020…").
  - `future_feature_edits` omits `behavior-cases.json` and `native-cases.json`, which exist beside the files it lists.
  - Most of the missing values are derivable from the assembly plan's New Files table, so this is Medium rather than High. It is the same gap F0011's plan-review recorded as PR-M2.
- **KG.** The F0009 shard has the correct status, phase, dependencies (F0002/4/6/7/8/11), ADRs (incl. 0080), schemas, and affects. lookup.py returned an unambiguous match.
  - **PR-L3 (Low).** All six story mappings list the same four new schemas and the same governed_by trio. For example, S0003 maps to `learning-candidate-reservation-v1`, and S0005 omits ADR-0044. This is KG precision drift against the raw stories, which win.
- **Assembly plan.** It exists and is detailed (379 lines). It was not required as a plan deliverable, and its presence was not counted for or against readiness.

## Buildability Challenge

Owner: Code Reviewer.

| Rule | Outcome | Evidence |
|---|---|---|
| BRAIN-BUILDABILITY | PASS WITH FINDINGS | Five ordered steps with integration checkpoints (assembly plan lines 16–24), exact modified/new paths (lines 26–54), a 41-row AC→step→proof map (lines 299–341), and owner handoffs (lines 345–353). STATUS sets the required signoff roles QE, Code Reviewer, Security, DevOps, and Architect. PR-H1 and PR-M1 below |

Assessment:

- **Vertical slice.** The slice is large but cohesive: one new package, two tables, one review-boundary change, and one facade hook. The step order puts carriers before tables, tables before the review boundary, and the review boundary before the reader. Every step has a checkpoint. Backend, QE, Security, and DevOps responsibilities have no conflict. Frontend and AI are correctly "—".
- **Verified against shipped code.** These assembly-plan statements matched the source:
  - `ReviewDecisionService.submit` replays the prior event, then raises `ReviewItemAlreadyDecided` on `has_any_decision`. The stale branch omits `corrected_value`, `evidence` and `reviewer_comment` (decisions.py lines 117–148).
  - `save_decision` does not pass `decided_at` (repositories.py lines 264–287).
  - The POST route maps already-decided to 422 and calls `mutate` with `source_keys` as `additional_reads` (reviews.py lines 104–182).
  - Migration head is 0015. `CanonicalFactChangeRow` has `reason/from/to/created_at` and no actor or commit column.
  - `current_attesting_artifact_keys` exists in repositories.py, and `scripts/contracts/{generate,check}.py` and `experience` `contracts:check` exist.
- **PR-H1 (High): refused-sibling event-hash poisoning.**
  - The trigger case: under Step 3 item 4, item J in a batch is recorded as `BATCH_REFUSED` only because a different item I already had a decision. Step 3 item 3 then makes any later submission whose `(review_item_id, event_sha256)` matches J's attempt "retain the same non-applied receipt/422 outcome".
  - Why the hash keeps matching: `compute_event_sha256` hashes only item, action, reviewer, version, reason, and corrected_value. Evidence and comment are excluded (decisions.py lines 53–63). A reviewer who resubmits J alone, unchanged, in a clean batch is therefore refused forever. For ACCEPT, the only way out is to change the reason or action. This contradicts S0002 AC6, which says only the losing attempt is non-applied, and the stated preservation of existing behavior: today J would apply on resubmission.
  - The plan does not say whether refused-attempt replay is keyed per batch or per item. The literal implementation is wrong, and the correct rule is not written down.
  - Fix: replay of a prior refused attempt applies only when the whole batch is resubmitted, or only to `ALREADY_DECIDED` attempts. Otherwise re-evaluate the item. Specify how a later effective decision coexists with an earlier attempt row that has the same hash.
- **PR-M1 (Medium): decided_at type mismatch.**
  - `review_decision.decided_at` is `timestamp without time zone` (migration 0002 line 91; ORM `mapped_column(server_default=func.now())`, models.py line 344). The domain sets it to tz-aware `datetime.now(UTC)`.
  - The plan requires persisting it explicitly (line 31). It also requires the reservation guard to check `decision.decided_at = NEW.reserved_at`, where `reserved_at` is `timestamptz` (migration-design.sql line 14; plan line 163).
  - PostgreSQL compares the two by converting with the session `TimeZone`, so equality depends on a connection setting. asyncpg also handles aware values bound to a naive column differently.
  - The repository already has the rule needed: `audit_timestamp()` in brain_persistence/authx.py lines 268–271 stores naive UTC. The plan should state that convention, or cast explicitly (`decided_at AT TIME ZONE 'UTC'`) in the guard. A PostgreSQL proof at Step 2 would catch it, so this is Medium.
- **PR-L1 (Low).** The plan says GET `/reviews/{id}` keeps "the same latest decision projection" (line 207). `ReviewDecisionOut` exposes `corrected_value`, `evidence` and `reviewer_comment`, so stale decisions now return those values where they were previously null. Fields are unchanged but values change. The authority is the same as for effective decisions (`review_task:read`). S0006 AC4 accepts only additive changes that Phase B explicitly approved, so this needs an explicit line in the plan and a regression fixture.
- **PR-L2 (Low).** Two cases need a sentence each:
  - a batch that names the same review item twice: preflight sees no existing decision, and the second submit then raises inside the operation with a full rollback and no attempt record;
  - "fingerprint changed → retry as a fresh operation" (line 193): which status is returned (409, 503, or the existing 422?), and does the client or the server retry?
- **Testability.** Every AC maps to unit, PostgreSQL integration, security-negative, or migration proof, and there are concrete test file paths. The 80% changed-code floor is stated, and existing `test_reviews.py`/`test_facts.py` stay as regression gates. Proposed commands are flagged for G0 syntax validation.
- **Dependencies and risk hotspots.** All dependencies are shipped (F0002/4/6/7/8/11), and no future feature is a prerequisite. The plan flags these high-blast-radius nodes for extra review:
  - the shared `AuthorizationExecution.read` (opt-in `prepare_reads`, Security);
  - the review POST transaction shape (audit-only refusal commit);
  - the new deferred constraint trigger on `review_decision`;
  - the shared F0011 contract bundle.

  The elevated DB role is recorded as an F0018 handoff.

## Validation Evidence

PR2 validator results are recorded below and in `lifecycle-gates.log` and `commands.log`.

All PR2 validators ran through `run-gate.py --stage PR2` with explicit `--product-root`, `--plan-scope feature` and `--target F0009`. All are read-only and every one exited 0.

| # | Command | Exit | Result | Output reference |
|---|---|---|---|---|
| 1 | `python3 agents/scripts/check-plan-approvals.py --product-root <root> --plan-scope feature --target F0009` | 0 | PASS: one current base-run-only approval (plan run 2026-11-24-bfdbbf04, `approved`), no active rework | - |
| 2 | `python3 agents/product-manager/scripts/validate-stories.py <FEATURE_PATH>` | 0 | PASS | - |
| 3 | `python3 agents/product-manager/scripts/validate-trackers.py` | 0 | PASS | - |
| 4 | `python3 <root>/scripts/kg/validate.py` | 0 | PASS | - |
| 5 | `python3 <root>/scripts/kg/validate.py --check-drift` | 0 | PASS | - |
| 6 | `python3 agents/scripts/validate_templates.py` | 0 | PASS | - |
| 7 | Project check `plan-readiness`: `validate_plan_readiness.py --product-root <root> --plan-scope feature --target F0009` | 0 | PASS (status `pass`, 0 findings) | `artifacts/project-checks/PR2-plan-readiness-71c47759ce294cfab2005ad59f42212c.stdout.json` |

A validator pass is structural evidence only. PR-H1, PR-H2, PR-M1 and PR-M2 are reviewer findings that no validator covers.

## Artifact Trace

Raw artifacts read (working tree at HEAD `2613b0b`, F0009 package uncommitted):

- `planning-mds/features/F0009-provenance-and-human-correction-lineage/`: PRD.md, README.md, STATUS.md, GETTING-STARTED.md, personas.md, acceptance-criteria-checklist.md, the six F0009-S000{1..6} stories, feature-assembly-plan.md, contract-inventory.yaml, contract-examples.json, migration-design.sql, worked-examples.md
- `planning-mds/architecture/decisions/ADR-0080-bounded-provenance-and-correction-reservations.md`
- `planning-mds/schemas/provenance-query-v1`, `provenance-result-v1`, `learning-candidate-reservation-v1`, `review-submission-attempt-v1` (untracked), and `review-decision.schema.json` (unchanged)
- `planning-mds/kg-source/features/F0009.yaml`; diffs of BLUEPRINT.md, ROADMAP.md, domain/glossary.md and examples/README.md
- Product checklist `docs/plan-review-checklist.md` and `docs/agent-instructions.md` (via project_context.py)
- Shipped code examined for plan claims (read-only):
  - engine/packages/brain-review/src/brain_review/decisions.py
  - engine/packages/brain-persistence/src/brain_persistence/{repositories.py, models.py, authx.py}
  - engine/packages/brain-security/src/brain_security/execution.py
  - engine/apps/api/src/brain_api/routes/reviews.py and schemas/review.py
  - engine/migrations/versions/0002, 0006, 0007 and the version list
  - scripts/contracts/sources.yaml and the directory listing
  - experience/package.json

No plan, KG, tracker, story, contract, schema, architecture, or source file was modified. No feature evidence package was written.
