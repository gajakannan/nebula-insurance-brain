# Provide agent instructions and the review checklist

**Story ID:** F0064-S0002
**Feature:** F0064 — Repository instructions and planning-check adoption
**Title:** Provide agent instructions and the review checklist
**Priority:** Medium
**Phase:** Infrastructure
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** Brain-local working instructions and a plan-review checklist that point at the Brain's authoritative sources
**So that** agents and reviewers apply Brain rules from the Brain's own documents, never from a copy held in the framework.

## Context & Background

Delivered 2026-09-07. The instructions orient sessions to the blueprint, ADRs, KG and tracker conventions. The checklist is the local review contract used by plan-review PR1 reviewers and validated structurally by S0003.

## Acceptance Criteria

- [ ] **AC1:** `docs/agent-instructions.md` names the source order (`planning-mds/BLUEPRINT.md`, then `planning-mds/architecture/master-blueprint.md` with its ADRs, then feature folders). It requires an explicit `--product-root` or `NEBULA_PRODUCT_ROOT`, and it states that `planning-mds/kg-source/**` is authored while generated regions are produced by `scripts/kg/compile.py`.
- [ ] **AC2:** Each local validation command in `docs/agent-instructions.md` runs from the repository root at closeout and exits with the documented code (0 for the current repository).
- [ ] **AC3:** `docs/plan-review-checklist.md` has the columns `Rule ID | Owner | Criterion | Governing source | Planning evidence to inspect` and exactly the eight rules BRAIN-SCOPE, BRAIN-AUTHORITY, BRAIN-EVIDENCE, BRAIN-PARSE-ONCE, BRAIN-TEMPORAL, BRAIN-AUTHORIZATION, BRAIN-BUILDABILITY and BRAIN-EXAMPLES. Each rule has an owner in {product-manager, architect, security, code-reviewer} and a governing source that resolves to an existing file.
- [ ] **AC4:** The checklist states that a script pass is not approval or regulatory compliance, and that each inapplicable rule needs an explicit rationale in the review report.
- [ ] **AC5:** The framework at the pinned revision contains no Brain checklist rule ID and no Brain instruction text outside test fixtures that use synthetic products.

**Edge cases:**

- A stale statement in either document (for example a removed command or a renamed governing source) is a defect, repaired before closeout.

## Interaction Contract

N/A — read-only story. The documents are authored guidance with no capture or save flow.

## Data Requirements

Markdown documents only.

## Role-Based Visibility

Not applicable: repository documentation.

## Non-Functional Expectations

No performance target. Both documents stay short enough to load as session context; no other non-functional expectation applies.

## Dependencies

- F0064-S0001 (the manifest declares both documents).

## Out of Scope

Rewriting review criteria, adding rules, or judging whether a given plan satisfies a rule.

## Questions & Assumptions

**Assumptions (to be validated):**
- The eight-rule set is the delivered set. Changing it is new scope for a separate decision.

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — documentation)
- [ ] Audit/timeline logged (N/A — no runtime events)
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] Story filename matches `Story ID` prefix (`F{NNNN}-S{NNNN}-...`)
- [ ] Story index regenerated if story file was added/renamed/moved

## Review Provenance

Recorded in the parent feature `STATUS.md` (`Required Signoff Roles (Set in Planning)` and `Story Signoff Provenance`).
