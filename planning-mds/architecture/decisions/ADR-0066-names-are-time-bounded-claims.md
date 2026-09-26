# ADR-0066: Names Are Time-Bounded Claims

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0006](ADR-0006-factslot-defines-canonical-semantic-identity.md) (names become FactSlots) and [ADR-0025](ADR-0025-deterministic-er-ships-before-probabilistic-er.md) (the role names play in resolution)
**Source:** Master blueprint sections 53, 70, 78 (`entity_alias`). Informed by Utopia decision 0041 and its identity design (see References).

## Context

Section 78 plans `entity_alias` as a table beside `entity`. Insurance names change and are contested, and that change is information:

- a named insured is amended by endorsement;
- a company trades under a DBA;
- a policy lists "formerly known as";
- a broker writes an abbreviation;
- a loss run spells a name one way and the application another.

A plain alias table cannot tell you when a name was used, which document said so, or whether the claim was later corrected. It rebuilds, outside the ledger, what the ledger already does for everything else.

Utopia replaced its alias array with name facts for these reasons. It also found that identity keyed on the surface string fails two ways:

- **a namesake** is one string for several things;
- **an alias** is several strings for one thing.

Batch model verdicts on similar-looking names produced confident wrong merges.

## Proposed Decision

### 1. Names are assertions and facts

- **The name FactSlots.** A name is a typed assertion on one of the system name properties:
  - `hasLegalName`: single-valued per valid time;
  - `hasTradeName`: multi-valued, DBA;
  - `hasFormerName`;
  - `knownAs`: multi-valued; abbreviations and informal names.
- **What a name carries.** Its value, a qualifier for the name kind where needed, a verbatim quote (admitted under ADR-0065), both clocks, and the normal change semantics.
- **The display name.** An entity's display name is selected from its current accepted name facts. It is not a separate authority.
- **`entity_alias`.** A rebuildable search projection over name facts.

### 2. A rename keeps the entity

An endorsement that changes the named insured does not create a new entity. It asserts a new legal name valid from the endorsement's effective date (ADR-0064), and the prior legal name ends there. "What was the named insured on March 3?" is an ordinary valid-time query.

### 3. Names propose identity; they never decide it alone

- **v0.1 deterministic resolution (F0017)** keys on identifiers: policy number, FEIN, NAIC, and stable source identifiers. An exact name match with no identifier creates a review pair. It never merges.
- **Similarity is only a proposal.** Name-vector, abbreviation, containment ("Acme" inside "Acme Holdings"), and cross-script matches (F0027) only propose pairs. A pair proposed by similarity is never merged on a batch model verdict alone. It needs a tool-assisted second look that reads the evidence of both sides, or a person.
- **A name another entity of a compatible type already holds** creates a shared-name review pair, never a merge.
- **A role is not an entity.** "The named insured", "the first named insured", and "the additional insured" are roles that point at entities.

### 4. A merge moves name facts with everything else

Merges and reverts (section 53) move name facts with every other fact. A read at a recorded time before a merge shows both entities, each with its own names.

## Consequences

- **F0007** defines the name FactSlots. **F0013** declares the name properties and their kinds.
- **F0017** implements identifier-first resolution and shared-name review pairs.
- **F0027** adds similarity channels as proposals only, with the second-look requirement.
- **F0023** lists an entity's names with their sources and validity.
- **`entity_alias`** in section 78 is recast as a projection.

## Proof gates before acceptance

- **A named-insured change by endorsement** answers the legal name as of dates before and after the change, with evidence for each.
- **Two entities with the same legal name and different FEINs** stay apart. A DBA shared with another entity creates a review pair.
- **An abbreviation arriving before the full name,** and the reverse order, resolve to the same outcome. Measure pairwise precision and recall in both arrival orders and report the difference.
- **A name absent from its quote,** or claimed by another entity in the same document, is dropped with its reason (ADR-0065).

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0041 — A name is a claim about an entity](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0041-a-name-is-a-claim-about-an-entity.md)
- [design/identity](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/identity.md), including #889 (a similarity-proposed pair is never auto-merged on the batch verdict alone)

Worked and boundary examples: [EX-SEM-008](../../examples/statements-time-and-governance.md#names).
