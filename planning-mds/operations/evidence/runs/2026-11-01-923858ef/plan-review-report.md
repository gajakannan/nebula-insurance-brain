# Plan Review Report — F0006 (run 2026-11-01-923858ef)

- **PLAN_SCOPE / TARGET:** feature / F0006 — Assertion plane + origin + interpretation basis
- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (product HEAD `8228fec`; framework pin `308c81d`)
- **Plan run reviewed:** `2026-11-01-7d6d19ce` (A+B, manifest `approved`)
- **Reviewer mode:** single-session, read-only. Raw artifacts and the current engine source were inspected directly. Approval tokens were not relied on.

## Decision

**CONDITIONALLY READY.** Computed by `gate_policy.py --profile review-family --variant plan` with critical 0 and high 1 (artifacts/gate-policy-PR4.txt).

F0006's plan is thorough and buildable. Every PR2 validator passed, and the plan's code references match the live engine. One High gap remains: the interpretation basis on v2 review corrections (AR-1). Before `feature.md` starts, either:

- route AR-1 (and preferably AR-2) to targeted Architect rework through plan.md; or
- record explicit operator risk acceptance with an owner and a target date (for example, settle it at feature G0 Step 0).

Reviewers repaired nothing.

## Findings By Severity

| ID | Severity | Owner | Finding | Citation |
|---|---|---|---|---|
| AR-1 | High | Architect | **Correction interpretation basis unspecified for v2 corrections.** The plan's v2 review-correction rule lists the fields to preserve: subject/object identity, kind, mode, property/release, source phrase, qualifiers/mood and evidence restriction snapshots. It omits `interpretation_basis`. The live repository hard-codes `interpretation_basis="EXPLICIT"` on every correction. S0001 AC4 forbids silently converting `INFERRED`/`AMBIGUOUS` to `EXPLICIT`. The implementer must invent one of three rules: inherit the original basis, take a reviewer-supplied basis, or keep EXPLICIT for HUMAN_REVIEW. The v1 behaviour is also undecided: keep it as the legacy boundary, or change it. | feature-assembly-plan.md §Eligibility and Existing Consumers ("Review correction: …"); `engine/packages/brain-persistence/src/brain_persistence/repositories.py:246-269`; F0006-S0001 AC4/AC6 |
| AR-2 | Medium | Architect | **v2 correction and carrier persistence mapping incomplete.** (a) The deferred integrity trigger requires every v2 assertion to have one extension with matching evidence rows. `assertion_semantics.raw_item_sha256` and `admission_sha256` are NOT NULL CHAR(64). The plan never defines these hashes for a HUMAN_REVIEW correction child, which has no raw model item. It also does not say whether the child gets newly inserted AssertionEvidence rows or references the original's. (b) The legacy carrier column `assertion.subject_type` (NOT NULL) has no stated v2 mapping. `slot_type` and `value` are mapped. | feature-assembly-plan.md §Data Model (table rows `assertion`, `assertion_semantics`) and "Create `brain_assertion_v2_integrity()`…"; `models.py:144-178` |
| PR-1 | Low | Product Manager | S0004 AC4 names a `DESCRIBED_EVIDENCE` review. The plan routes it through the existing `PROVENANCE_CORRECTION` item type and keeps the specific reason code in the semantic extension. This satisfies the AC only if QE asserts the retained reason code, not the item type. The AC text does not state this mapping. | F0006-S0004 AC4; feature-assembly-plan.md §Atomic Writer ("Review hook: …"); `brain_domain/review.py:18-21` |
| CR-1 | Low | Code Reviewer | The STATUS Story × Role table marks the AI lane "Not Started" for S0002/S0003/S0005. Required Signoff Roles omits AI Engineer, while the assembly plan gives AI Engineer a DTO-compatibility review duty. Settle at feature G0 whether AI signoff is required. | STATUS.md §Story × Role Progress, §Required Signoff Roles; feature-assembly-plan.md §Build Order (ownership paragraph) |
| CR-2 | Info | Code Reviewer | The plan says to create `engine/packages/brain-security/tests/test_execution.py` "if it does not exist". It already exists, so extend it. Not a defect. | feature-assembly-plan.md §Authorization facade integration |

Counts: critical 0 · high 1 · medium 1 · low 2 · info 1.

## Product Readiness (owner: product-manager)

| Rule | Outcome | Evidence |
|---|---|---|
| User value and non-goals | Pass | PRD Feature Statement, Business Objective, explicit Out of Scope (F0066/F0016/F0007–F0019/F0022/F0026/F0052–53) |
| Testable ACs (BRAIN-SCOPE) | Pass | 35 ACs across S0001–S0005 (7/7/8/6/7, matching PRD table and checklist); each names observable outcomes, negative paths and zero-effect checks |
| Mutation contracts | Pass | Every story has an Interaction Contract table with entry point, editable state, mutation result, reload evidence and role constraints; audit expectations explicit |
| UI / screen readiness | Pass (No UI) | PRD §UX/Screens and §Screen Layouts give a written "No UI" justification; F0022 owns display |
| Personas / priorities | Pass | personas.md reuses three existing personas and grants no permissions |
| No invented business rules / placeholders | Pass with note | Bounded design choices are assigned to the Architect in each story's Q&A. No TODO or placeholder text in build-critical sections. PR-1 is a traceability note. AR-1 touches S0001 AC4 semantics, and its resolution may need PM confirmation. |
| Trackers | Pass | REGISTRY row F0006 Planned/v0.1A; STATUS stories Not Started; ROADMAP remains Next (validators below) |

## Architecture Readiness (owner: architect)

| Rule | Outcome | Evidence |
|---|---|---|
| BRAIN-AUTHORITY | Pass | ADR-0075 and ADR-0065 stay Proposed with explicit runtime proof gates. ADR-0005/0035/0063 are cited as accepted. |
| API contracts | Pass | No new route (ADR-0075 §4). brain-api.yaml documents the commit `ASSERTION_INELIGIBLE` 422 (lines ~243-288) and the v2 review restriction (line 144). The in-process contract is three JSON Schemas plus Python signatures. |
| Data model / workflow | Pass with findings | Three new append-only tables, SQL CHECKs, a deferred integrity trigger, a version discriminator and a migration down-revision of `0010`. Verified as the current head in `engine/migrations/versions/`. Gaps: AR-1 and AR-2. |
| Authorization | Pass | Uses existing grants. policy.csv gives ServicePrincipal `content_artifact:interpret/read` and `fact_slot:commit`, so the commit-time source READ needs no new grant. The `additional_reads` callback design matches the live `AuthorizationExecution.mutate` signature (`brain_security/execution.py:388`). Non-disclosure is 404 before 422. |
| BRAIN-EVIDENCE / PARSE-ONCE / TEMPORAL | Pass | Server-derived evidence, zero conversion/OCR calls, and claimed valid time kept separate from canonical bitemporal ranges (PRD §Data Requirements; plan §Admission Logic) |
| BRAIN-EXAMPLES | Pass | worked-examples.md EX-ASSERT-001..009 with definitions, boundary cases, owners and contract links; 16 schema cases in contract-examples.json labelled illustrative |
| NFRs | Pass | ≥80% changed-code coverage; zero model/OCR calls; zero unauthorized disclosure; latency recorded as observation without an invented SLO |
| KG alignment | Pass (see PR2) | lookup.py feature:F0006 affects/governed_by/uses_schema match the ADR and schema files on disk |
| Assembly plan derivable | Pass | It exists and is detailed. Not required as a plan deliverable. |

## Buildability Challenge (owner: code-reviewer)

| Rule | Outcome | Evidence |
|---|---|---|
| Vertical-slice size | Pass | Seven build steps (0–6) with per-step stories and checkpoints; backend-only; no deployable or UI |
| Role handoffs (BRAIN-BUILDABILITY) | Pass with note | Backend/AI/QE/Security/DevOps/Architect duties stated; Frontend N/A; CR-1 |
| File/API direction | Pass | All nine existing paths in §Existing Code verified on disk. Guard placement matches the live `CanonicalCommitService.commit` (between `current_versions` and `register_commit`, `brain_temporal/commit.py:105-127`). The facts route tuple-unpacks one decision (`routes/facts.py:113`), and the plan explicitly changes this. |
| Testability | Pass | Validation matrix maps every story's ACs to PG/unit/integration/regression checks. The proposed commands reference existing suites (test_reviews.py, test_facts.py, test_document_process_recovery.py, alembic.ini). |
| Dependencies / sequencing | Pass | F0001–F0005 delivered. Future consumers are named without reverse dependency. Migration head must be rechecked at G0. |
| Risk hotspots | Flagged | (1) The commit guard sits on the only canonical write path. Mixed v1/v2 and correction-ancestry bypass tests are mandatory. (2) The `mutate` facade change affects every caller. No-callback regression is required. (3) The original-field immutability triggers on `assertion`/`assertion_evidence` must not break the existing staleness `version` bump. (4) The v2 correction path (AR-1/AR-2). |

## Validation Evidence

All seven commands ran through `run-gate.py --stage PR2` from the framework (pin 308c81d), with `--product-root`, `--plan-scope feature` and `--target F0006`. Results are journaled in gate-state.json and lifecycle-gates.log.

| Command | Exit | Result |
|---|---|---|
| check-plan-approvals.py --plan-scope feature --target F0006 | 0 | PASS: current planning approval present; no active rework |
| validate-stories.py {FEATURE_PATH} | 0 | PASS: 5 stories |
| validate-trackers.py | 0 | PASS |
| scripts/kg/validate.py | 0 | PASS |
| scripts/kg/validate.py --check-drift | 0 | PASS: no KG drift found |
| validate_templates.py | 0 | PASS |
| project check `plan-readiness` (scripts/validation/validate_plan_readiness.py) | 0 | PASS, 0 findings (artifacts/project-checks/PR2-plan-readiness-*.json) |

Additional read-only checks: `lookup.py F0006` returned an exact feature match (artifacts/lookup-F0006.txt). All referenced existing engine paths and the migration head `0010` were verified on disk.

## Artifact Trace

See artifact-trace.md.
