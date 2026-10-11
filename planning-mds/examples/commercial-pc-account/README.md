# Cedar Bridge — commercial P&C account walkthrough

**EX-PC-001 · Synthetic development example · Proposed representation · 2026-10-08, time model revised 2026-10-09, account model (ADR-0070) 2026-10-10, revised the same day for one account per policy and broker of record, and again after the PR #19 review**

> **Status.** Everything here is invented and hand-authored: organizations, documents, policies, amounts, interpretation runs, reviews and commits. No extraction model, commit service, assessment engine, authorization service or AGE writer produced it. The representation is a proposal for F0012/F0013 to accept, change or reject; it changes no feature status, ADR or roadmap phase. The RDF, OWL-RL, SHACL and query expectations are executed by the `semantic_rdf` gate, and [expected-results.yaml](expected-results.yaml) records that execution.

This companion to the [small interchange example](../ontology-interchange/README.md) follows a contractor account from documents to scoped parties, policies, coverages, assertions, reviewed facts and a historical projection. It uses its own vocabulary namespace, `https://example.invalid/nebula/ont/commercial-example/`, so EX-GL-001 and EX-INTEROP keep their meanings. Aligning terms with the production namespace is an F0012 decision.

## 1. One account per organization, distinct insureds and roles

Under proposed [ADR-0070](../../architecture/decisions/ADR-0070-account-party-and-role-model.md), every organization has its own account. **Cedar Bridge Holdings LLC** owns all of **Cedar Bridge Workshop LLC** and 60 percent of **Cedar Bridge Contracting LLC**, a joint venture with **Example Ridge Builders Inc.** (40 percent). The Workshop and Contracting accounts have the Holdings account as their designated parent. Ridge Builders has its own account, which is not a parent.

Workshop has a BOP and Contracting a standalone GL policy. Both are named on the auto and umbrella declarations: Workshop as first named insured, Contracting as an additional named insured. Every policy belongs to exactly one account: BOP, auto and umbrella to the Workshop account, GL to the Contracting account. A small property program belongs to the Holdings account, with a master policy for Holdings and a local policy for each subsidiary, each under its own entity's account and linked to the program. Named-insured status comes from each policy term's role assignments, never from the account hierarchy or ownership. Each account has Harbor as broker of record and its own broker contact.

| Participant | Represented as | Boundary |
|---|---|---|
| Holdings account | Root of the hierarchy; Holdings owns Workshop and 60% of Contracting; owns the property program and its master policy | Parentage never makes it a named insured on its children's policies |
| Workshop / Contracting accounts | One account per organization, each with the Holdings account as designated parent | Workshop owns BOP, auto, umbrella and a local program policy; Contracting owns GL and a local program policy, and is also a named insured on auto and umbrella |
| Ridge Builders | 40% owner of Contracting, with its own account | A minority owner is not the account parent |
| Workshop LLC | First named insured on the BOP, auto and umbrella terms and its local program policy | Named on the GL term only if the GL declarations say so; they don't |
| Contracting LLC | First named insured on the GL term and its local program policy; additional named insured on the auto and umbrella terms | Covered by the BOP only if named on it; it isn't |
| Harbor Example Brokerage and its Riverside branch | Broker of record for the Holdings, Workshop and Contracting accounts and placement broker on the BOP, GL, umbrella and master program terms; the branch is an organization under it, with its own office | Broker of record is dated, so a change keeps history; the local program policies name no placement broker and show the broker of record |
| Example Fleet Brokers and Drew Example | Placement broker on the auto term only; Drew is its broker contact on that policy | A per-line override; Drew reaches the auto policy, not the accounts behind it |
| Jordan Example | Broker contact for the Holdings and Workshop accounts, employed by the Riverside branch | Works for neither the insured nor a carrier; reaches no Contracting record |
| Sam Example | Broker contact for the Contracting account and on the umbrella policy, employed by Harbor's head office | Reaches the umbrella because named on it; not auto, which names Contracting but not Sam |
| Casey Example | Risk manager for the Holdings account and account contact for the Workshop account, employed by Holdings | One person, two roles, two accounts |
| Example Maple Mutual / Example Granite Casualty | Carrier roles on specific policy terms; underwriters Morgan (the whole BOP), Quinn (BOP property section only) and Avery (GL) | Carrier staff can see the tenant; the underwriter role, narrowed by coverage where given, says who may act |
| Example Delegated Underwriting MGA and Rowan Example | MGA handling the contracting submission; Rowan underwrites for it | Granite is the GL carrier; the fixture shows no delegated authority |
| Shop, yard, Riverside office and van | Location and vehicle references | Insured only where a coverage names them |

Party roles are `RoleAssignment` nodes with a party, a role kind, a scope (account, submission or policy term) and, for a person, the organization acted for. Under ADR-0070 they also feed access: an external person reaches only what their roles name (an account and its own policies, or a single policy), and carrier staff may act only where they hold the role. No authorization code runs in this fixture ([EX-PC-018](cases.md#ex-pc-018--external-contacts-reach-what-their-roles-name-carrier-staff-see-but-act-by-role)).

```mermaid
flowchart TD
    H["Holdings account"] --> WA["Workshop account"]
    H --> CA["Contracting account"]
    R["Ridge Builders account"]
    HO["Holdings LLC"] -.->|owns 100%| W
    HO -.->|owns 60%| C
    RO["Ridge Builders Inc."] -.->|owns 40%| C
    WA --> W["Workshop LLC"]
    CA --> C["Contracting LLC"]
    R --> RO
    B["Harbor Brokerage / Riverside branch"] -->|broker of record| H
    B -->|broker of record| WA
    B -->|broker of record| CA
    BP["BOP"] -->|belongs to| WA
    AU["Auto (Fleet Brokers)"] -->|belongs to| WA
    U["Umbrella"] -->|belongs to| WA
    GL["Standalone GL"] -->|belongs to| CA
    C -.->|additional named insured| AU
    C -.->|additional named insured| U
    PG["Property program"] -->|belongs to| H
    PM["Master policy"] -->|part of| PG
    PM -->|belongs to| H
    PW["Local policy W"] -->|part of| PG
    PC["Local policy C"] -->|part of| PG
    PW -->|belongs to| WA
    PC -->|belongs to| CA
    U -->|scheduled underlying| GL
    U -->|scheduled underlying| AU
```

The diagram summarizes; the snapshot keeps the role-assignment, ownership, term and monetary nodes it flattens.

## 2. Two coverage lines in depth, with a wider program

**Product/package type** and **coverage line** are separate concepts. A BOP packages property and liability sections. The BOP's liability section and the standalone GL policy share vocabulary while keeping their own forms, scope and terms; a shared class says nothing about equivalent wording.

| Product / line | Represented | Values in the source |
|---|---|---|
| Standalone GL | Contractor, term, carrier, broker, occurrence trigger, two qualified limits | USD 1M each occurrence; USD 2M general aggregate |
| BOP liability | Workshop's liability section | USD 1M each occurrence; USD 2M general aggregate; form and trigger text not supplied |
| BOP property | Workshop BPP at the shop, limit, deductible, endorsement | USD 150k, then USD 200k from July 1; USD 1k per-loss deductible |
| Commercial auto | Both insureds, scheduled van, liability CSL | USD 1M combined single limit per accident; physical-damage terms not supplied |
| Umbrella | Both insureds, own limit, scheduled GL and auto terms | USD 2M each occurrence; attachment and exhaustion undetermined |
| Workers compensation / employers liability | Broker's quotation request | Requested only |
| Inland marine tools | Separate quotation request | Requested only; workshop BPP says nothing about tools at job sites |

The example encodes this account's declarations only: no eligibility rules, limit ratios, form editions, state rules or umbrella responses. Determining coverage for a claim needs the forms, the facts of the claim and evidence of attachment; the schedule is context.

## 3. Follow the documents into the graph

1. Read the nine excerpts in [source-package.md](source-package.md): account and hierarchy record, BOP, GL, auto, umbrella, property program, broker request, endorsement and loss notice. Each states its document date.
2. Inspect [records.json](records.json): **111 identity rows, 10 evidence excerpts, 238 assertions, 234 slots, 237 fact versions**, with interpretation runs, reviews and commits. Its [JSON Schema](../../schemas/commercial-pc-example.schema.json) describes these teaching records.
3. Follow a fact's `assertion_ref` to `run_ref` and `evidence_ref`, and its `commit_ref` to the review that accepted the reading. Accepting a reading records what the source says; it issues no policy and decides no coverage.
4. Read [snapshot.ttl](snapshot.ttl) or [snapshot.jsonld](snapshot.jsonld): **233 business statements** plus type and label metadata, at `valid_as_of = 2026-07-05` and `known_as_of = 2026-07-11`. Both are generated from `records.json`.
5. Use [snapshot-index.json](snapshot-index.json) to recover each statement's fact, assertion, evidence and commit. Type and label rows cite their evidence in `records.entities`.

All rows sit in one synthetic tenant/KB context, which authorizes nothing. The snapshot is a scoped view of accepted facts, not the PostgreSQL kernel's schema. Relationship slots distinguish target identities; money slots keep currency and basis qualifiers.

The `runs` illustrate interpretation routes. An `OPEN` run's release reference records interpretation context; the ontology stays out of OPEN prompts. The two coverage requests stay as `REQUEST`-mood assertions and never become facts about issued coverage.

## 4. Time: kinds, precision and unknown bounds

Each property declares a `temporal_kind` in [ontology.yaml](ontology.yaml), following proposed ADR-0064:

| Kind | Properties | Valid time |
|---|---|---|
| `ETERNAL` | policy number, product type, term period, coverage-of, monetary basis and currency, role kind and scope, an account's organization, an ownership interest's owner and owned organization | none; identity and structure |
| `STATE` | limits, deductibles, schedules, location, role party and acted-for organization, a policy's or submission's account, a policy's program, parent account, ownership percentage, parent organization, employment, operating location | an interval with per-bound granularity, `attested_from`, and an `OPEN`, `BOUNDED` or `UNKNOWN` end |
| `EVENT` | the loss notice, coverage requests | a point at its stated granularity |

Policy-term facts are `BOUNDED` by the declared period at `DAY` granularity. Relationships the sources never date (parent accounts, ownership, employment, operating locations, broker of record, a policy's account, contact and MGA roles) have an unknown start: `from` is null and `attested_from` is the document date. Before that date they read `UNKNOWN`, never "since always".

**The endorsement** shows three times: valid from July 1, attested July 8 (its document date), recorded July 10. Its commit closes the full-year BPP version in recorded time and adds a retained January–June version and a revised July–December version. Intervals are half-open; UTC is a teaching simplification.

| Valid as of | Known as of | BPP reading | Fact version |
|---|---|---|---|
| July 5 | July 8 | USD 150,000 | `EX-PC-F-BPP-ORIGINAL` |
| July 5 | July 11 | USD 200,000 | `EX-PC-F-BPP-REVISED` |
| June 30 | July 11 | USD 150,000 | `EX-PC-F-BPP-RETAINED` |
| Dec 31, 2025 | July 11 | absent (before the term) | — |

**The yard** shows an unknown end. The broker's May 15 request says Contracting no longer operates there, without a date. That reading closes the open version and adds one whose end is `UNKNOWN` with `attested_to: 2026-05-15`, so March reads `UNKNOWN` and July reads absent ([EX-PC-014](cases.md#ex-pc-014--unknown-start-and-unknown-end)). The yard relationship is therefore missing from the July snapshot.

A snapshot includes `ETERNAL` facts, `STATE` facts that read as a value, and `EVENT` facts that occurred by `valid_as_of`. [expected-results.yaml](expected-results.yaml) lists ten timeline readings with their exact fact versions. Liability limits do not change; property-summary completeness is a separate consumer from F0065's GL rule. Historical reads still require current authorization.

## 5. Files, modules and release composition

| File | Purpose |
|---|---|
| [ontology.yaml](ontology.yaml) | Proposed class/property ownership, temporal kinds, rule subset and per-consumer constraint execution |
| [foundation.ttl](foundation.ttl) | Parties, organization hierarchy, accounts, ownership, employment, roles, places and vehicle identity |
| [insurance-core.ttl](insurance-core.ttl) | Policies, terms, product types, coverages and qualified money |
| [general-liability.ttl](general-liability.ttl) | GL coverage specialization |
| [property.ttl](property.ttl) | Property coverage and location scope |
| [program-extensions.ttl](program-extensions.ttl) | Lightweight auto and umbrella concepts |
| [release.yaml](release.yaml) | Illustrative module versions, dependency locks and artifact digests |
| [projection-mapping.yaml](projection-mapping.yaml) | Proposed graph mappings, explicit omissions and lineage obligations |
| [shapes.ttl](shapes.ttl) | Supplied-value, scoped-role-record, role-coverage, account (including parent cycles), policy-account, program, ownership and ownership-total checks |
| [gl-completeness.ttl](gl-completeness.ttl) | GL each-occurrence input completeness; an aggregate does not substitute |
| [property-completeness.ttl](property-completeness.ttl) | BPP amount and location completeness for a property summary |
| [expected-inferences.ttl](expected-inferences.ttl) | Six selected type/inverse consequences |
| [cases.md](cases.md), [expected-results.yaml](expected-results.yaml) | Worked and boundary cases with authored outcomes |
| [queries/](queries/) | Account roll-up, Account 360, broker contact reach, underwriter decision rights, program, ownership, account team, coverage money, umbrella schedule and schedule review |
| [boundaries/](boundaries/) | Independent missing-input, malformed-value, account-structure, ownership and role-coverage graphs; one conforming joint venture |

Module version IRIs differ from the composed release IRI, and dependencies resolve through the manifest rather than remote `owl:imports`. The YAML and OWL files are hand-maintained counterparts. Release digests identify bytes; compatibility is a separate judgment. Domain and range declarations infer types only; no axiom creates a coverage from a product label.

Run the queries against the **asserted snapshot**, without the inferred closure. [expected-results.yaml](expected-results.yaml) lists every expected row, and forbidden rows for reach and decision rights, so a query that returns the right count but the wrong people fails:

- [account roll-up](queries/account-program.rq): seven policies under the Holdings hierarchy, each once under the account it belongs to, with carrier and placement broker, or the account's broker of record when the term names none ([EX-PC-001](cases.md#ex-pc-001--account-versus-insured));
- [Contracting Account 360](queries/account-360-contracting.rq): the GL and local program policies it owns as first named insured and the two Workshop policies naming it as additional named insured ([EX-PC-016](cases.md#ex-pc-016--a-policy-belongs-to-exactly-one-account));
- [broker contact reach](queries/broker-contact-reach.rq): nine rows; each broker contact reaches only what their roles name ([EX-PC-018](cases.md#ex-pc-018--external-contacts-reach-what-their-roles-name-carrier-staff-see-but-act-by-role));
- [decision rights](queries/decision-rights.rq): four underwriter and coverage rows; Quinn decides BOP property, not BOP liability (EX-PC-018);
- [ownership](queries/ownership.rq): two owners of Contracting, only one of them the account parent ([EX-PC-015](cases.md#ex-pc-015--ownership-is-not-the-account-hierarchy));
- [program](queries/program.rq): the Holdings program's master and two local policies, each under its own account ([EX-PC-019](cases.md#ex-pc-019--a-program-links-its-policies-it-does-not-own-them));
- [account team](queries/account-team.rq): eleven person/role/scope rows across the hierarchy ([EX-PC-017](cases.md#ex-pc-017--brokers-are-parties-and-roles-show-who-does-what));
- [coverage money](queries/coverage-money.rq): eight qualified values, which must never be summed across coverage, basis or layer;
- [umbrella schedule](queries/umbrella-schedule.rq): the GL and auto terms;
- [schedule review](queries/umbrella-schedule-review.rq): one row, Workshop's unscheduled BOP liability, a prompt for an underwriter's question ([EX-PC-013](cases.md#ex-pc-013--an-unscheduled-primary-is-a-review-prompt)).

## 6. Reproduction

From the product root, `python3 scripts/validation/validate_semantic_examples.py` checks the schema, IDs, evidence quotes and document dates, review/commit lineage, temporal kinds and attestations, version overlap, the timeline readings, and that the three snapshot files match the generator. It is a fixture check, not Nebula's historical-query engine.

The snapshot files are generated: edit `records.json`, never the snapshots.

```bash
python3 scripts/validation/build_commercial_pc_snapshot.py --refresh-digests  # regenerate snapshots, refresh release.yaml digests
pip install -e '.[semantic-rdf]'                                           # optional planning tools; no runtime dependency
python3 scripts/validation/validate_semantic_rdf.py --require              # isomorphism, OWL-RL, SHACL, queries
```

Without the optional tools, `validate_semantic_rdf.py` reports `skipped`; CI runs it with `--require`. Generated snapshots write strings as simple literals because rdflib and pySHACL compare terms: `sh:hasValue "EachOccurrence"` does not match `"EachOccurrence"^^xsd:string`.

A pass establishes the selected checks only. SHACL emits no `UNKNOWN`, decides no claim, establishes no authority and sums no program.

## 7. Ownership and the planning KG

| Contract | Planning owner |
|---|---|
| Shared identity, account/party roles, module/release schema | F0012, under proposed ADR-0070 |
| Insurance core and GL vocabulary | F0013, with the product/coverage distinction |
| Profile packaging and route separation | F0014/F0015; OPEN prompts stay ontology-free |
| Scoped identifiers; account versus organization identity | F0017 |
| Account 360 root and hierarchy roll-up | F0023 |
| Valid-time kinds, precision, unknown bounds, temporal storage | F0008/F0010, F0016 time mentions, ADR-0064 |
| Authorized admission and evidence | F0018/F0022 within F0002's accepted boundaries |
| Role-based reach and decision rights | F0002-successor scope amendment (ADR-0070 section 5) |
| GL assessments | F0065 only; property, auto and umbrella are outside it |
| AGE projection | F0034, v0.2A |
| BOP property, auto, umbrella, WC and inland-marine runtime delivery | Unassigned; illustrative breadth |

The planning KG indexes shared concepts, this example's schema, feature owners and source documents; the Cedar Bridge parties and policies stay in this folder. [The handoff](../../architecture/commercial-pc-example-handoff.md) covers source precedence, compilation and lookup checks.
