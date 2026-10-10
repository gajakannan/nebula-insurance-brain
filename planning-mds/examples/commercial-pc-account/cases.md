# Cedar Bridge worked and boundary cases

All cases are synthetic. [The source package](source-package.md) supplies the readings; [records.json](records.json) supplies illustrative lineage. Outcomes below are authored, not runtime observations.

## EX-PC-001 — account versus insured

Each organization has its own account (ADR-0070): Holdings, Workshop, Contracting and Ridge Builders. Each policy belongs to exactly one account: BOP, auto and umbrella to Workshop, the first named insured on each; GL to Contracting; the property program and its master policy to Holdings, and its local policies to Workshop and Contracting (EX-PC-019). Named-insured role assignments are a separate fact: Contracting is also a named insured on auto and umbrella without owning them. [account-program.rq](queries/account-program.rq) rolls the Holdings hierarchy up to seven policies, each listed once. Holdings is a parent, an owner and the master policy's insured, but being a parent never makes it a named insured on its children's policies. Owner: F0012/F0013, scoped identity F0017.
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

## EX-PC-011 — domain roles are not grants by themselves

The MGA handled a submission while Granite issued the GL policy. Underwriter Rowan acts for the MGA; Morgan underwrites the BOP for Maple and Avery the GL for Granite. A role assignment read from a document authenticates no one and authorizes no canonical commit. Under ADR-0070 section 5, role assignments that come from an authoritative source do feed access (EX-PC-018), but the access decision stays with the authorization service. A second tenant using the same broker must not see this account; current revocation also applies to old snapshots and their evidence. No authorization code is exercised here. Owner: F0002/ADR-0061/ADR-0062 boundaries, an F0002-successor scope amendment, and F0012's role vocabulary.
## EX-PC-012 — conflict is not absence

Hypothetical extension, not present in the accepted snapshot: two unresolved source readings claim USD 1M and USD 2M for the same GL occurrence slot and overlapping context. Preserve both assertions and conflict state; do not choose the larger amount or higher model score. Applicable assessment handling is `CONFLICT`, not a missing-input `UNKNOWN`. Owner: F0018/F0065. The fixture validator rejects conflicting accepted versions in both time dimensions; it is not the runtime conflict workflow.

## EX-PC-013 — an unscheduled primary is a review prompt

The umbrella names both organizations. Its supplied schedule lists the GL and auto terms, but not the BOP on which Workshop is the only named insured. [umbrella-schedule-review.rq](queries/umbrella-schedule-review.rq) returns that BOP liability coverage as one row. An underwriter would ask whether the BOP liability should be scheduled, or whether the umbrella form addresses it another way. The fixture records neither answer. Employers liability, which umbrella carriers often require underneath, cannot be checked: the WC/EL line is only requested (EX-PC-005). Owner: F0012's relation contract; umbrella runtime semantics remain unassigned.

## EX-PC-014 — unknown start and unknown end

The account record (dated 2025-12-15) says Contracting operates at the yard but not since when. Its fact has `from: null`, `attested_from: 2025-12-15` and an `OPEN` end. Before December 15 the reading is `UNKNOWN`, not "since always" (EX-PC-014-B). The broker's request (dated 2026-05-15, accepted May 18) says Contracting no longer operates there, without a date. That reading has time shape `ENDED_UNDATED`. It closes the open version in recorded time and adds a version whose end is `UNKNOWN` with `attested_to: 2026-05-15`. Known as of July 11, March reads `UNKNOWN` (014-C) and July reads absent (014-D). Known as of April 1, March still reads the open version (014-A). The yard relationship is therefore missing from the July snapshot. Nothing here invents an end date. Owner: F0008 (`valid_to_state`, attestation bounds), F0016 (time mentions), ADR-0064.

## EX-PC-015 — ownership is not the account hierarchy

Holdings owns all of Workshop and 60 percent of Contracting; Ridge Builders owns the other 40 percent. Each owner has its own account. Contracting's account names Holdings' account as its designated parent; Ridge Builders' account is not a parent. [ownership.rq](queries/ownership.rq) returns both owners with their percentages and whether each is the account parent. Every owner is recorded with a percentage, so 50/50, three-way or four-way joint ventures need no winner. Majority is computed from the percentage, never stored. An account has at most one parent so a family roll-up never counts a joint venture twice: with a majority owner, the parent is usually that owner's account; with none, the joint venture is a root account, and each owner's Account 360 lists it as an ownership interest outside its roll-up. [two-parent-accounts.ttl](boundaries/two-parent-accounts.ttl) names two parents and fails the account shape. [duplicate-organization-account.ttl](boundaries/duplicate-organization-account.ttl) gives one organization two accounts and fails too. Owner: F0012 (ADR-0070), F0017 for account and organization identity.
## EX-PC-016 — a policy belongs to exactly one account

The auto and umbrella declarations name Workshop first and Contracting as an additional named insured. Each policy belongs to the Workshop account; Contracting stays a named insured on the term. [account-360-contracting.rq](queries/account-360-contracting.rq) returns GL and the local program policy as Contracting's own and auto and umbrella as policies it is named on. [policy-two-accounts.ttl](boundaries/policy-two-accounts.ttl) files one policy under two accounts and fails the policy-account shape. An additional named insured is not an additional insured: the latter is a third party, such as a landlord, added by endorsement with narrower rights, and would be its own role kind. A master program is the other pattern: see EX-PC-019. Owner: F0012 relation contract, F0023 Account 360.
## EX-PC-017 — brokers are parties, and roles show who does what

Harbor Example Brokerage is broker of record for the Holdings, Workshop and Contracting accounts. A change of broker of record would close that dated role and open a new one; the fixture does not model one. Harbor's Riverside branch is an organization under it and operates from its own office location. Jordan, employed by the branch, is the broker contact for Holdings and Workshop; Sam, employed by Harbor itself, is the broker contact for Contracting. Drew, employed by Fleet Brokers, is broker contact on the auto policy only. A broker contact works for neither the insured nor a carrier. Casey, employed by Holdings, is risk manager for the Holdings account and account contact for the Workshop account: one person, two roles, two accounts. The auto policy came through a different placement broker, Example Fleet Brokers, a per-line override of the account's broker of record. [account-team.rq](queries/account-team.rq) lists ten person, role, scope and acted-for rows across the hierarchy. Owner: F0012 role vocabulary, F0023 Account 360.

## EX-PC-018 — external contacts reach what their roles name; carrier staff see, but act by role

A role decides reach by its scope. An account role reaches that account and the policies it owns. A policy-term role reaches that policy only. [broker-contact-reach.rq](queries/broker-contact-reach.rq) returns nine rows:

- Jordan, on the Holdings and Workshop accounts, reaches the master policy and Workshop's BOP, auto, umbrella and local program policy;
- Sam, on the Contracting account, reaches GL and Contracting's local program policy, and, named on the umbrella, the umbrella too. Sam is not named on auto, so Sam does not reach it, though it names Contracting;
- Drew, named only on the auto policy, reaches that policy and nothing of the Workshop or Contracting accounts.

Nothing cascades. Holdings being the parent account gives Jordan nothing of Contracting, a program or master policy gives no one its local policies, and a policy role never opens the account behind it. Carrier staff are different: Morgan and Avery can read everything in the tenant, but only Morgan may make BOP decisions and only Avery GL decisions, because only they hold those underwriter roles. The query shows the data an access check would read. No authorization code runs here, and a role read from a document must be confirmed by an authoritative source before it grants anything (EX-PC-011). Owner: F0002-successor scope amendment under ADR-0070 section 5; ADR-0062 for grants and revocation.

## EX-PC-019 — a program links its policies; it does not own them

Maple and Holdings set up property program EX-PROG-100, which belongs to the Holdings account. Under it, master policy EX-PROP-100 belongs to the Holdings account, local policy EX-PROP-100-W to the Workshop account and EX-PROP-100-C to the Contracting account. Each policy links to the program. [program.rq](queries/program.rq) returns the three policies with the program's account and each policy's own account. The family view comes from those links, so no policy needs two accounts. [two-programs.ttl](boundaries/two-programs.ttl) puts one policy under two programs and fails the policy shape. The excerpt supplies no limits, locations or premium allocation, so nothing here says how master and local limits interact. The program mirrors the data contracts' `MASTER_PROGRAM` Agreement and `Policy.agreement_uid`. Owner: F0012 relation contract, F0023 Account 360.
