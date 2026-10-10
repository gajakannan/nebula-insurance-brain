# Commercial P&C example — scope and KG handoff

**Status:** Synthetic teaching expansion, 2026-10-08; review fixes 2026-10-09. It proposes representations for F0012/F0013 planning and establishes no feature plan, runtime behavior, production namespace or ADR acceptance. The user selected the contractor-account scenario.

## Read in this order

1. [Cedar Bridge walkthrough](../examples/commercial-pc-account/README.md): one account, two organizations, a BOP, standalone GL, auto and umbrella, plus WC and inland-marine requests.
2. [Source package](../examples/commercial-pc-account/source-package.md), [structured records](../examples/commercial-pc-account/records.json) and [worked and boundary cases](../examples/commercial-pc-account/cases.md).
3. [F0012](../features/F0012-foundation-ontology/README.md), [F0013](../features/F0013-insurance-core-gl-ontology/README.md), [F0015](../features/F0015-extraction-profile-compiler/README.md), [ADR-0045](decisions/ADR-0045-ontology-release-compatibility.md) and [ADR-0064](decisions/ADR-0064-time-interpretation-and-valid-time-precision.md).

## Modeling decisions to carry into planning

- **Account, parties and roles.** Account grouping, legal parties and policy-term named-insured roles are separate. One party can be broker, carrier, MGA or underwriter in different scopes; domain roles grant no application access. Whether Account is a party or a grouping, and what an account-scoped grant reaches, is an [open decision](../BLUEPRINT.md#48-open-decisions).
- **Product versus coverage.** A BOP packages property and liability; standalone GL reuses liability vocabulary without equating contracts or wording.
- **Qualified values.** Keep scoped identifiers, qualified money and exact term, location and vehicle references with their evidence. An account-wide sum of limits has no meaning.
- **Readings versus outcomes.** Requests, reported losses, accepted source readings and coverage or assessment outcomes stay distinct.
- **Time.** Every property declares `ETERNAL`, `STATE` or `EVENT`. State bounds carry granularity and `attested_from`; ends are `OPEN`, `BOUNDED` or `UNKNOWN`. Undated relationships have an unknown start rather than the policy year, and an undated ending stays `UNKNOWN` with `attested_to` (EX-PC-014). The endorsement separates valid, attested and recorded time (EX-PC-006).
- **Completeness per consumer.** Named-consumer completeness is separate from malformed supplied values; property-summary gaps are not F0065 GL assessments.
- **Schedule review.** An umbrella naming an insured whose primary liability term is unscheduled is a review prompt, not a coverage conclusion (EX-PC-013).

The account grouping, scoped role assignment and time encoding are **draft refinements**. Accepted entity and authorization contracts stay in force until F0012/F0013 decide, and the separate namespace leaves EX-INTEROP's terms unchanged.

## Delivery ownership

F0012 owns shared authoring, identity and release contracts; F0013 insurance core and GL; F0015 TEMPLATE packaging; F0017 scoped identifier resolution; F0008/F0010 temporal storage, with F0016 time mentions; F0018/F0022 governed admission and review; F0065 bounded GL assessment; F0034 the eventual AGE projection.

BOP property, auto, umbrella, WC/employers liability and inland marine are illustrative breadth with no feature or release assigned. Product planning assigns that scope before these examples become requirements; F0013's GL commitment and F0065's evaluator stay as planned.

## Maintaining the two graphs

The **example graph** holds the invented Cedar Bridge account and policies. It lives under `planning-mds/examples/commercial-pc-account/` and is never imported as runtime truth.

The **planning KG** holds shared concept and schema nodes and routes to feature and architecture documents. Author `kg-source` shards, rationale and file bindings, then compile; fictional companies, policy numbers, evidence rows and fact versions never become planning nodes. Examples are reachable through bindings. Node `source_docs` cite this handoff, the glossary and feature READMEs, because examples sit outside the KG's allowed source-document roots.

The validation scripts belong to `capability:semantic-example-validation`, which covers both teaching bundles. The `semantic_examples` gate checks records, lineage, time and generated snapshots; the `semantic_rdf` gate executes the RDF expectations, and [expected-results.yaml](../examples/commercial-pc-account/expected-results.yaml) records its status. EX-GL-001 and EX-INTEROP keep their own evidence.

After any source, fixture or documentation edit:

```bash
python3 scripts/validation/build_commercial_pc_snapshot.py --refresh-digests
python3 scripts/validation/validate_semantic_examples.py
python3 scripts/validation/validate_semantic_rdf.py --require
python3 scripts/kg/compile.py
python3 scripts/kg/validate.py --regenerate-symbols
python3 scripts/kg/validate.py --write-coverage-report
python3 scripts/kg/validate.py
python3 scripts/kg/validate.py --check-drift
python3 scripts/kg/validate.py --check-reproducible
python3 scripts/kg/lookup.py F0012 --tier 3 --fields full
python3 scripts/kg/lookup.py --file planning-mds/examples/commercial-pc-account/snapshot.jsonld
python3 scripts/run-lifecycle-gates.py
```

Edit `records.json`, never the generated snapshots; `--refresh-digests` rewrites the release digests, which identify bytes and say nothing about compatibility. Refresh coverage after the final documentation edit, because freshness hashes cover source content. Run the framework tracker validator with the explicit product root and `--skip-feature-evidence`.

## History

- **2026-10-08.** Structural, KG, lifecycle and tracker checks passed. RDF execution did not run because the optional tools could not be installed.
- **2026-10-09, review fixes.**
  - First RDF run: isomorphism, inferences and queries matched, but the snapshot failed both completeness shapes. An uncommitted generator had typed strings as `xsd:string`, which rdflib and pySHACL do not match against simple-literal `sh:hasValue`. The generator is now committed and emits simple literals, and the structural check fails when snapshots drift from `records.json`.
  - Time model: every fact had taken the policy year, including relationships the sources never date. Facts now follow ADR-0064 kinds, sources carry document dates, and the yard shows an undated ending.
  - KG binding: the shared validator was bound to this example's schema, and a sidecar name match falsely linked it to `vllm_graph_client.py`. It moved to `capability:semantic-example-validation`, and the entry point became `validate_examples`.
  - Account: the account question was logged as an open decision.
  - Added: EX-PC-013 and its schedule-review query; carrier marketing links removed.
