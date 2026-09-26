# Statements, time, and automated governance: semantic examples

**Status:** Every example below is synthetic and illustrative. No runtime execution, model output, or measured rate is claimed. The examples explain [ADR-0063](../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) to [ADR-0069](../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md). Where they fit, they reuse the continuing [EX-GL-001](neurosymbolic-gl/README.md) case.

The glossary has the definitions. The owning feature and delivery phase are shown on each example and in the [coverage map](README.md). These are development and documentation examples; they stay outside the frozen holdout.

## Open statements and alignment

**EX-SEM-001 — F0006 storage (v0.1A); F0066 alignment (v0.2B); ADR-0063.**

A broker email in the EX-GL-001 package says: *"Acme Roofing subcontracts all tear-off work to Dalton Crews LLC."*

Open interpretation stores one open statement:

- subject: Acme Roofing;
- phrase: "subcontracts all tear-off work to";
- object: Dalton Crews LLC;
- the verbatim quote, located by the admission service;
- no predicate.

Later, the ontology release defines `usesSubcontractor` with domain `Contractor` and range `Organization`. The kind words "roofing" and "LLC" are already bound to classes. Alignment then decides the signature ("subcontracts … to", `Contractor`, `Organization`) once:

- two votes, with candidates in opposite orders, both choose `usesSubcontractor`, forward;
- materialization writes one typed assertion with `typed_assertion_source` pointing at the statement;
- a second email with the same phrasing adds a source row, not a second assertion;
- no document is re-read.

**Boundary (EX-SEM-001b).** An underwriter's note says *"Acme may subcontract tear-off work next season."* That statement carries `mood = "may … next season"` and is never materialized.

A different boundary: if the ontology has no admissible property, the signature is recorded as `NONE`. The statement stays in the open layer and counts toward ontology suggestions. It is not bound to a generic "related to" property.

**EX-SEM-002 — F0066, v0.2B; ADR-0063 implication rules.**

A statement says *"Dalton Crews LLC, a Texas limited liability company …"*. An approved implication rule concludes `jurisdictionOfFormation`, taking the object from a cached reading of "Texas". The implied assertion carries `interpretation_basis = INFERRED`, the rule version, and the statement's evidence.

**Boundary.** "A Texas-based roofer" names a location, not a jurisdiction of formation. The reading must not be reused across different phrases. It is cached per distinct phrase, and "Texas-based" has its own reading, which says nothing about formation.

## Time interpretation

**EX-SEM-003 — F0016/F0019/F0025, v0.1; ADR-0064.**

The EX-GL-001 endorsement reads *"Effective as of 12:01 a.m. on July 1, 2026, the Each Occurrence limit is amended to $2,000,000."* The policy's time context holds:

- the policy period from 01/01/2026 to 01/01/2027;
- the policy's convention: 12:01 a.m. standard time at the address of the named insured.

The mention is interpreted as a `POINT`, reference `ABSOLUTE` "July 1, 2026", granularity `MINUTE`. Code applies the time-zone convention and computes the start. The resolution grade is `A`.

The document is attested by its issue date, taken from its content. Recorded time is canonical acceptance on July 10. Receipt on July 9 is a recorded-time-family fact, not the document date. The EX-GL-001 temporal walkthrough answers follow unchanged.

**Boundary (EX-SEM-003b).** A second endorsement says *"effective as of inception"*. Its reference is `ANCHORED` to the policy period's start. If that policy's declarations are not in the package, the anchor is unknown: the mention is grade `C`, the assertion carries no valid time, and a review item asks for the anchor. It must not take the upload date, or January 1 of the current year.

**EX-SEM-004 — F0008, v0.1A; ADR-0064 unknown bounds.**

A loss run *"valued as of 06/30/2026"* is an `AS_OF` attestation of the listed losses. It is not the validity interval of each loss. Each loss occurrence is an `EVENT` at its stated date and granularity.

A broker note dated 2026-08-02 says *"the prior carrier is no longer on the account"*. This ends the prior-carrier state with `valid_to_state = UNKNOWN` and `attested_to = 2026-08-02`.

**Boundary.** A query at 2026-07-15 must answer `UNKNOWN`, not "still held" and not "ended". A missing start date on the prior-carrier fact reaches back only to the earliest attesting document, never to negative infinity.

## Admission, origin, and mood

**EX-SEM-005 — F0006/F0016, v0.1A; ADR-0065 admission.**

The model returns the quote *"Each Occurrence Limit $500,000"*, but the declarations block reads *"EACH OCCURRENCE LIMIT $ 500,000"*. Normalization handles the case and whitespace difference. The server locates the quote, computes the offsets itself, and admits the assertion.

**Boundary (EX-SEM-005b).** Two failures look alike but are handled differently.

- **A fabricated quote.** The model returns the quote *"Each Occurrence Limit $5,000,000"*, which appears nowhere in the block. The item is dropped as `QUOTE_NOT_IN_SOURCE`, the drop row is written, and the run reports it.
- **A misread value (CASE-05 of EX-GL-001).** The model quotes the genuine $500,000 wording but emits the value 5,000,000. Admission checks that the quote is present, not that the value was read correctly, so the assertion is admitted and reaches review, where the reviewer corrects it.

Admission refuses evidence that does not exist. It does not replace review.

**EX-SEM-006 — F0004/F0022, v0.1; ADR-0065 text origin.**

An SOV attachment includes a bar chart of building values. Docling produces a `DESCRIBED` block, and the model reads the tallest bar as $5.2M for Building 3. The SOV table, a `STATED` source, says $2.5M.

The described assertion opens a review item with reason `DESCRIBED_EVIDENCE`. It cannot supersede the stated value.

**Boundary.** An OCR block from a scanned declarations page is admissible evidence at its declared precision. OCR is not treated like a description.

**EX-SEM-007 — F0006 (v0.1A); routing to F0052 (v0.3); ADR-0065 mood.**

A binder says *"Binding is subject to receipt of a signed and dated application within 10 days."* The statement carries `mood = "subject to"` and becomes a subjectivity candidate. The Brain does not assert that the application was received.

**Boundary.** An issued policy's condition *"This insurance does not apply unless the insured maintains automatic sprinklers"* is an operative provision. It is asserted as a fact about the policy: the policy has that condition. The embedded content, that the insured maintains sprinklers, is not asserted as a fact about the insured's premises.

## Names

**EX-SEM-008 — F0007/F0017, v0.1A; F0027, v0.2B; ADR-0066.**

The declarations name *"Acme Roofing Inc."* with FEIN 12-3456789. An endorsement effective 2026-09-01 amends the named insured to *"Acme Roofing & Restoration Inc."*, with the same FEIN.

- `hasLegalName` records the first name valid until September 1 and the second from September 1.
- The entity is unchanged.
- "Who was the named insured on August 15?" returns the first name, with its evidence.

**Boundary.** A loss run lists *"Acme Roofing"* with no FEIN, and another account in the tenant is *"Acme Roofing Supply LLC"*.

- Name similarity proposes pairs and merges nothing.
- A batch model verdict of "same" is not applied without a second look that reads both entities' evidence.
- "The named insured" in a letter is a role pointing at an entity. It is not a name fact.

## Automation and impact

**EX-SEM-009 — F0027/F0043, v0.2B; F0059, v0.4+; ADR-0067.**

With automated merging enabled, the resolver is 0.97 confident that two coverage-holder entities are one. The F0065 assessment EX-ASSESS-001 rests on one of them. The merge is held for a person as `IMPACT_HOLD:DERIVED 1 assessment`, and the card says why. A different merge with nothing downstream applies automatically, and can be reverted from the queue.

**Boundary.** A person earlier kept "Acme Roofing" and "Acme Roofing Supply" apart and wrote a reason: "different FEINs on the ACORD". That decision is precedent and blocks an automatic merge verdict on the same pair. The resolver's own earlier verdicts are never precedent.

When two automatic merges are reverted within seven days, automated merging turns itself off for that knowledge base and raises an alert.

## Decision basis

**EX-SEM-010 — F0066/F0032, v0.2B; F0056, v0.4+; ADR-0068.**

The signature ("subcontracts … to", `Contractor`, `Organization`) was bound when `usesSubcontractor` was declared on `Organization`. A later release moves the property's domain to a new parent class `LegalEntity`, and `Contractor` is made a subclass of it. The ancestor closure changes, so the stored basis no longer matches and the signature is reconsidered. Nothing compares timestamps.

**Boundary.** Relabelling the property's display name does not change the basis, so no work is queued. A person's binding on another signature shows "inputs changed since decision" after a relevant edit, and is never overwritten by the aligner.

## Action attempts

**EX-SEM-011 — F0050, v0.3; F0059, v0.4+; ADR-0069.**

An approved agent action requests an endorsement in the policy administration system. The attempt is `PREPARED` with `execution_request_id` R-17, then `DISPATCHING`. The worker dies after sending, and before the response is stored. Recovery finds `DISPATCHING`, marks it `OUTCOME_UNKNOWN`, and does not send again. A person checks the remote system.

**Boundary.** A Temporal activity replay of the same step must not re-send R-17. A later 200 response carrying R-17's dispatch token updates the attempt to `RESPONSE_RECEIVED`. Any new endorsement data it carries enters as a `SYSTEM_OBSERVATION` assertion; it is never written into canonical state directly.
