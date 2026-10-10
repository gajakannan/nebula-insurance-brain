# Cedar Bridge worked and boundary cases

All cases are synthetic. [The source package](source-package.md) supplies the readings; [records.json](records.json) supplies illustrative lineage. Outcomes below are authored, not runtime observations.

## EX-PC-001 — account versus insured

The account groups two organizations. Named-insured role assignments select Workshop for BOP and Contracting for GL; auto and umbrella name both. Traversing account membership cannot create a missing named-insured relationship. Owner: F0012/F0013, scoped identity F0017.

## EX-PC-002 — package versus coverage

BOP contains a GL-like liability section and a property section, each with its own monetary terms. The standalone GL policy shares `GLCoverage` terminology, not a contract identity. The BOP's full form/trigger wording and business-income terms are unknown in this excerpt. Never infer building coverage or a business-income amount from the product label. Owner: F0012/F0013; property runtime scope remains unassigned.

## EX-PC-003 — policy number collision

Both carriers use `EX-2042`: Granite for GL and Maple for auto. They retain distinct policy and term identities. A bare-number join would combine different carriers, insured sets and coverages. Production identifier scope belongs to F0017; this does not select a universal insurer numbering convention.

## EX-PC-004 — money needs context

USD 1M each occurrence, USD 2M general aggregate, USD 200k BPP and a USD 1k per-loss deductible are distinct values. `snapshot-index.json` links each to its subject, predicate and source fact; the monetary node's basis and currency have their own facts. Do not add these values or compare BPP to a GL minimum. Owner: F0013, proposed ADR-0039 and F0065's bounded GL contract.

## EX-PC-005 — requested is not issued

The broker requests WC/employers-liability and inland-marine quotations. Both assertions retain `mood: REQUEST` and have no accepted issued-coverage fact. The package does not establish either existence or absence of an issued policy elsewhere. Owner: F0014/F0016, ADR-0065; those lines' runtime vocabularies are future work.

## EX-PC-006 — endorsement with two clocks

The endorsement shows ADR-0064's three times: valid from July 1, attested July 8 (its document date), recorded July 10. At July 5 as known July 8, BPP is USD 150k. At July 5 as known July 11, it is USD 200k. At June 30 as known July 11, it remains USD 150k. Before the policy term starts, the BPP limit does not hold. The original version closes in recorded time; retained and revised intervals carry exact source assertions and a new commit. Liability limits remain unchanged. See the three independent expectations in [expected-results.yaml](expected-results.yaml). Owner: F0008/F0010; F0025 owns integrated endorsement proof, not this fixture.

## EX-PC-007 — underlying schedule is not attachment

Umbrella references exact GL and auto terms. The BOP is not in the supplied schedule. This records the supplied schedule's membership, not a global negative coverage conclusion. An umbrella limit cannot simply be added to every policy's limit; attachment, exhaustion, insured status, exclusions and the applicable claim require their own evidence. Owner: F0012's relation/qualifier contract; umbrella runtime semantics remain unassigned.

## EX-PC-008 — an aggregate does not fill an occurrence gap

[missing-occurrence.ttl](boundaries/missing-occurrence.ttl) has a valid aggregate amount but no each-occurrence input. Supplied-value shapes should conform and the GL completeness shape should fail. Under the separately applied F0065 contract, missing required canonical input yields `UNKNOWN` after authority, applicability and conflict checks. SHACL itself does not produce that outcome. Owner: F0013/F0065.

## EX-PC-009 — property completeness has a different consumer

[missing-location.ttl](boundaries/missing-location.ttl) has valid BPP money without the location needed by the named property-summary consumer. Supplied-value shapes should conform and property completeness should fail. Report incomplete property context; do not claim F0065 assessed it. [malformed-amount.ttl](boundaries/malformed-amount.ttl) is a separate candidate whose string amount should fail supplied-value validation. Owner: F0012's constraint execution contract; property runtime owner remains to be assigned.

## EX-PC-010 — reported loss is not coverage adjudication

A loss notice reports an event and a GL policy reference. It does not prove insurer acceptance, coverage, liability, a reserve or payment. The notice is an `EVENT` fact on its June 21 document date, recorded June 22. It is absent when known as of June 21 and present when known as of July 11 (EX-PC-010-A/B). The identity catalog is authored metadata and must not be treated as a historical disclosure API. Owner: F0012's document/event distinction; claims runtime scope remains separately planned.

## EX-PC-011 — role and access are separate

The MGA handled a submission while Granite issued the GL policy. Underwriter Rowan acts for the MGA. None of those domain relationships authenticates Rowan, grants access to this KB or authorizes a canonical commit. A second tenant using the same broker must not see this account; current revocation also applies to old snapshots and their evidence. No authorization code is exercised here. Owner: accepted F0002/ADR-0061/ADR-0062 boundaries and F0012's role vocabulary.

## EX-PC-012 — conflict is not absence

Hypothetical extension, not present in the accepted snapshot: two unresolved source readings claim USD 1M and USD 2M for the same GL occurrence slot and overlapping context. Preserve both assertions and conflict state; do not choose the larger amount or higher model score. Applicable assessment handling is `CONFLICT`, not a missing-input `UNKNOWN`. Owner: F0018/F0065. The fixture validator rejects conflicting accepted versions in both time dimensions; it is not the runtime conflict workflow.

## EX-PC-013 — an unscheduled primary is a review prompt

The umbrella names both organizations. Its supplied schedule lists the GL and auto terms, but not the BOP on which Workshop is the only named insured. [umbrella-schedule-review.rq](queries/umbrella-schedule-review.rq) returns that BOP liability coverage as one row. An underwriter would ask whether the BOP liability should be scheduled, or whether the umbrella form addresses it another way. The fixture records neither answer. Employers liability, which umbrella carriers often require underneath, cannot be checked: the WC/EL line is only requested (EX-PC-005). Owner: F0012's relation contract; umbrella runtime semantics remain unassigned.

## EX-PC-014 — unknown start and unknown end

The account record (dated 2025-12-15) says Contracting operates at the yard but not since when. Its fact has `from: null`, `attested_from: 2025-12-15` and an `OPEN` end. Before December 15 the reading is `UNKNOWN`, not "since always" (EX-PC-014-B). The broker's request (dated 2026-05-15, accepted May 18) says Contracting no longer operates there, without a date. That reading has time shape `ENDED_UNDATED`. It closes the open version in recorded time and adds a version whose end is `UNKNOWN` with `attested_to: 2026-05-15`. Known as of July 11, March reads `UNKNOWN` (014-C) and July reads absent (014-D). Known as of April 1, March still reads the open version (014-A). The yard relationship is therefore missing from the July snapshot. Nothing here invents an end date. Owner: F0008 (`valid_to_state`, attestation bounds), F0016 (time mentions), ADR-0064.

