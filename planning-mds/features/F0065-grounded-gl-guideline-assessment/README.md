# F0065 — Grounded GL guideline assessment

**Status:** Planned — PRD, six stories, and draft assembly/contract authored 2026-09-07; runtime not started, formal review pending.
**Phase:** v0.1B
**Roadmap:** Later (after canonical commits/temporal reads; before F0024/F0025 integration acceptance)

A bounded neurosymbolic workflow interprets a policy into evidence-backed assertions, accepts qualified canonical facts, and evaluates a versioned minimum-limit guideline. The result is traceable to exact facts, rules, and evidence and supports current/historical contexts.

Read the [worked example](../../examples/neurosymbolic-gl/README.md), [PRD](PRD.md), [assessment contract](assessment-contract.md), [assembly plan](feature-assembly-plan.md), [getting started](GETTING-STARTED.md), and [status](STATUS.md). Proposed [ADR-0056](../../architecture/decisions/ADR-0056-bounded-neurosymbolic-assessment.md) records the proof obligations.

## Stories

| ID | Title | Status |
|---|---|---|
| [F0065-S0001](F0065-S0001-versioned-guideline-rule.md) | Versioned guideline rule | Not Started |
| [F0065-S0002](F0065-S0002-evaluate-accepted-facts.md) | Evaluate accepted facts | Not Started |
| [F0065-S0003](F0065-S0003-preserve-assessment-lineage.md) | Preserve assessment lineage | Not Started |
| [F0065-S0004](F0065-S0004-temporal-reassessment.md) | Temporal reassessment | Not Started |
| [F0065-S0005](F0065-S0005-explain-assessment-in-entity-360.md) | Explain assessment in Entity 360 | Not Started |
| [F0065-S0006](F0065-S0006-reproducible-worked-examples.md) | Reproducible worked examples | Not Started |

**Total Stories:** 6

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Assessment records add a `basis_hash` over their exact inputs, rule version, ontology release, and evaluator version. This refines existing lineage and does not change the approved outcomes (ADR-0068).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
