# ADR-0068: Decision Basis Fingerprints Define Staleness

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0016](ADR-0016-semantic-reinterpretation-is-incremental.md), [ADR-0017](ADR-0017-knowledge-evolution-is-first-class.md), [ADR-0026](ADR-0026-derived-facts-have-dependency-lineage.md), and [ADR-0045](ADR-0045-ontology-release-compatibility.md)
**Source:** Master blueprint sections 29, 30, 56, 112. Informed by Utopia decision 0053 (see References).

## Context

The Brain caches many decisions that depend on inputs that can change:

- interpretation runs;
- alignment bindings (ADR-0063);
- entity-resolution verdicts;
- derived facts and assessments;
- ontology impact analyses.

Knowledge evolution (sections 29–30) and derived invalidation (section 56) both need to know which cached decisions are no longer valid.

Utopia first compared timestamps ("was the input updated after the decision?") and found four failures:

1. **An inherited input.** A property declared on a parent class was never among the inputs considered, so no edit to it ever made the decision stale.
2. **A structural edge without a timestamp.** Adding or removing a subclass edge silently changed which candidates were admissible.
3. **An edit during the model call.** It committed before the decision, so the decision looked newer than the edit.
4. **Structural non-decisions were skipped rather than recorded.** Examples are "no candidate" and "too many candidates". So a lost support never retired its projection, and an overflow re-queued forever.

## Proposed Decision

### 1. A decision stores a fingerprint of what it considered

Every cached or automated decision that depends on mutable inputs stores a `basis_hash`. It is computed over the canonical serialization of every input the decider saw, and it is computed before any model is called.

| Decision | Basis includes |
|---|---|
| Interpretation run (F0016) | Artifact hash, selected blocks, profile/template/schema/prompt hashes, pipeline revision and configuration, model identity, document time context (ADR-0064) |
| Alignment binding (ADR-0063) | Ancestor closures of both endpoint classes, the value flag, and the admitted candidate properties with each property's version |
| Entity-resolution verdict (F0017, F0027) | Both entity profiles as read (name facts, identifiers, classes, neighbours), and the precedent set shown (ADR-0067) |
| Derived fact or assessment (F0055, F0065) | Exact input fact versions, rule version, ontology release, and evaluator version |
| Ontology/profile impact analysis (F0032) | The release diff and the dependency index version it was computed against |

### 2. Staleness is a changed fingerprint

A decision is stale when the fingerprint of its current inputs differs from the stored one. It is never judged against a clock. Workers recompute fingerprints for live decisions from data they already load.

- **A decision whose subject no longer exists** is orphaned. It is not consulted, and its projections retire through the normal materialization rules.
- **Unchanged inputs leave no queued work.**

### 3. Structural outcomes are decisions

"No admissible candidate", "too many candidates", and "input missing" are recorded as decisions with their reason and basis. They take part in staleness like any other decision: a candidate added later reopens a `NONE`.

### 4. A person's decision is never re-evaluated automatically

A human decision stores its basis for display and audit. When the basis changes, the decision is marked "inputs changed since decision". It may raise a review item. An agent never overwrites it.

## Consequences

- **F0016** and **F0066** (alignment) store bases.
- **F0032** uses fingerprints to schedule targeted reinterpretation.
- **F0056** uses fingerprints to find the derived facts to invalidate.
- **F0065** already pins exact input versions; its assessment records add the hash.
- **F0027** keys its verdict cache on the basis, including precedents.

## Proof gates before acceptance

Each gate runs against a real PostgreSQL, with a scripted model where one is needed.

- **Inheritance:** a property declared on an ancestor becomes admissible, and removing the parent edge retires the dependent projection without a model call.
- **Concurrent edits:** an edit committed while the model call is in flight leaves the decision stale on the next run.
- **Structural outcomes:** overflow is recorded as undecided, with no model call and no re-queue, and shrinking the candidate set makes it executable again.
- **Human decisions:** a person's decision is never overwritten, and it shows "inputs changed" after an input edit.
- **Derived facts:** changing one input fact version re-flags only the derived facts and assessments whose basis includes it.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0053 — A phrase decision records the inputs it considered](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0053-a-phrase-decision-records-the-inputs-it-considered.md)
- [0060 — A rule's definition has a history](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0060-a-rule-definition-has-a-history.md) (a conclusion names the definition version it was drawn under; F0065 already requires this)

Worked and boundary examples: [EX-SEM-010](../../examples/statements-time-and-governance.md#decision-basis).
