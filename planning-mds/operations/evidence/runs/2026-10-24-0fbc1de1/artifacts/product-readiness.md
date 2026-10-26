## Product Readiness

Owner: product-manager (root reviewer). Reviewed the current raw PRD, all five stories and all 34 acceptance criteria, checklist, STATUS, README, GETTING-STARTED, existing design/handoff, compatibility evidence, registry/roadmap/blueprint, tracker governance and raw planning approval record. Prior approval does not settle present inconsistencies.

### PM-1 — High — Rejection does not select the promised default engine

**Locations:** `planning-mds/features/F0005-one-time-docling-ingestion/PRD.md:19` (Business Objective); `F0005-S0004-evaluate-and-activate-proven-pipeline.md:35` (AC7); `feature-assembly-plan.md:117` (Step 6 configuration), `:125` (new direct-baseline worker path), `:149` (Step 7 rejection).

**Finding:** The PRD makes a measured rejection a valid completed outcome with the F0001 direct client retained, and AC7 explicitly requires the direct client to remain default. The planned initial selector is `extraction.pipeline: graph-direct`; rejection says both settings stay unchanged and the direct-baseline worker path merely remains available. Graph direct and the direct baseline are separate engines in the same selector and comparison. Following the rejection procedure therefore leaves the Graph engine selected rather than satisfying AC7. The raw prior plan's `gate-decisions.md` → Phase B Reconciliation also acknowledges the preexisting Graph-direct worker and the need to build the direct-baseline worker path; it does not remove the current conflict.

**Consequence:** An implementation agent must choose between conflicting accepted outcome rules, including what executes after failed qualification. That choice changes product behavior at the central activation boundary.

**Repair ownership:** product-manager owns reconciliation of the rejection outcome with the architect, who owns the selection/rollback design; backend-developer implements the resulting configuration contract. Through targeted plan rework, specify the final selector and writer state for acceptance, rejection and rollback, the fate of already pinned jobs, and a rejection-path restart/new-submission assertion. Keep the direct client selected on rejection if AC7 is retained. No repair or risk acceptance is recorded by this audit.

### Requirements, stories and interaction readiness

| Area | Outcome | Raw planning evidence |
|---|---|---|
| User value, MVP scope and exclusions | PASS | PRD → Feature Statement, Business Objective, Scope & Boundaries. Local synthetic-data qualification is explicit; production host, frozen corpus, profile compiler, date candidates and canonical acceptance have named owning features. |
| Testable acceptance | PASS with PM-1 and technical findings | S0001 AC1–6; S0002 AC1–7; S0003 AC1–7; S0004 AC1–8; S0005 AC1–6. Independent corpus expectations, distinct failure reasons, restart/count/hash evidence and gate decisions are specified. The design gaps identified by architect/code-reviewer still need repair. |
| Mutation entry points and persisted outcomes | PASS subject to PM-1 | Each story → Interaction Contract and Validation and audit: CLI submission/cancellation, worker/importer, immutable bundle/run, committed activation settings; current ServicePrincipal grants, state constraints, denial/failure behavior and reload evidence. Rejection setting remains inconsistent. |
| UI and screens | N/A, justified | PRD → Screen Layouts (ASCII) explicitly says No UI; F0022 owns review UI and existing consumers remain unchanged. No new desktop/narrow layouts or frontend implementation demanded. |
| Personas and workflow | PASS | PRD → Feature Statement and UX / Screens; S0001/S0003/S0005 document intelligence engineer, S0002 platform engineer, S0004 platform owner. Blueprint §3.2 carries engineering personas. |
| Measured qualification boundaries | PASS | PRD → Qualification Thresholds: nine explicit gates; reporting-only tokens/GPU memory; 12-document minimum and two profiles; Synthetic bias and Reviewer independence risks. Development synthetic proof is explicitly insufficient for live qualification. |
| Tracker state | PASS for F0005 review scope | REGISTRY F0005 Planned; ROADMAP Next; BLUEPRINT §3.3 and feature README/STATUS five-story inventory agree on S0001–4 In Progress and S0005 Not Started. No review-induced state transition or regeneration allowed. PR2 supplies mechanical coherence checks. |
| Planning approval | Inspected, PR2 determines history validity | Prior base run `2026-10-23-9a04b327/evidence-manifest.json` → action plan, run_scope base-run-only, approved_phases A/B; raw gate-decisions → G3 and G5 operator decisions. This review creates no approval or supersession. |
| Build-critical ownership | Present | Existing design → Ownership and package boundary, Steps 0–7 and Test inventory. No missing owner exception identified; remaining technical gaps require decisions by named owners, not invented implementation defaults. |

### Product checklist dispositions

- **BRAIN-SCOPE:** PARTIAL — PRD and five stories define requirements, exclusions and measurable criteria, with the rejection behavior conflict PM-1.
- **BRAIN-BUILDABILITY:** PARTIAL — role and test handoffs exist; see the independently owned Buildability Challenge and Architecture Readiness findings for technical gaps.
- Architectural checklist ownership remains in Architecture Readiness, including evidence, parse-once, temporal applicability, authorization and semantic-example rationale. No PM override of architect findings.

### PM self-review (PR3)

Rechecked PM-1 against the exact current story, selector values and rejection instruction; it is a concrete contract conflict, not a missing future runtime deliverable. No ambiguity in the corpus author/reviewer separation after reading the distinct QE sessions in the ownership table. The absence of implemented harness, corpus, migration 0009, live results and feature assembly approval is not a planning defect: these are explicitly future implementation/proof obligations. Runtime code-quality, execution coverage and release qualification are skipped for this read-only plan review; the plan explicitly requires ≥80% changed-runtime coverage at implementation. No plan, KG, tracker, story, source or feature evidence edits were made.

**PM recommendation:** CONDITIONALLY READY, subject to repair of PM-1 and the independent technical findings before starting dependent implementation. No critical PM finding and no missing build-critical owner identified.
