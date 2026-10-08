# Commercial P&C example — scope and KG handoff

**Status:** Synthetic architecture teaching expansion, 2026-10-08. No feature plan, runtime implementation, production namespace or ADR acceptance is established. User selected the contractor account scenario.

## Read in this order

1. [Cedar Bridge walkthrough](../examples/commercial-pc-account/README.md): one account, two organizations, a BOP, standalone GL, auto and umbrella, with WC/inland-marine requests.
2. [Source package](../examples/commercial-pc-account/source-package.md), [structured records](../examples/commercial-pc-account/records.json), and [worked/boundary cases](../examples/commercial-pc-account/cases.md).
3. [F0012](../features/F0012-foundation-ontology/README.md), [F0013](../features/F0013-insurance-core-gl-ontology/README.md), [F0015](../features/F0015-extraction-profile-compiler/README.md), and [ADR-0045](decisions/ADR-0045-ontology-release-compatibility.md).

## Modeling decisions to carry into planning

- Distinguish account grouping, legal parties, and policy-term named-insured roles. A party can act as broker, carrier, MGA or underwriter in different scopes. These roles never grant application access.
- Distinguish product/package type from coverage line. The BOP contains property and liability; standalone GL can reuse liability vocabulary without equating contracts or form wording.
- Retain scoped identifiers, qualified money, exact term/location/vehicle references, evidence and two-time context. An account-wide sum of GL, property, auto and umbrella limits has no declared meaning.
- Keep requests, reported losses, accepted source readings and coverage/assessment outcomes distinct. The source text and synthetic record metadata identify their respective claims.
- Represent the endorsement by exact fact versions and interval splitting. Historical views use the retained release and inputs under current permissions.
- Keep named consumer completeness separate from malformed supplied values. Property-summary gaps are not F0065 GL assessments.

The fixture's account grouping and scoped-party-role representation are **draft refinements** for F0012/F0013. They do not silently replace accepted entity/authorization contracts. Its independent illustrative namespace also prevents changes to the original EX-INTEROP term definitions. Production alignment/migration requires the normal release contract.

## Delivery ownership

F0012 owns shared authoring/identity/release contracts; F0013 owns insurance core and GL; F0015 owns TEMPLATE packaging; F0017 owns scoped identifier resolution; F0008/F0010 own temporal storage; F0018/F0022 own governed admission/review; F0065 owns bounded GL assessment; F0034 owns eventual AGE projection. Existing feature phases and coverage exclusions outside the previously mapped ontology features remain unchanged.

Property/BOP extensions, auto, umbrella, WC/employers liability and inland marine are illustrative future breadth. No standalone runtime feature or release date is allocated for them here. Assign that scope through product planning before treating these examples as implementation requirements. Do not broaden F0013's GL delivery commitment or F0065's evaluator merely because the data includes other lines.

## Maintaining the two graphs

The **example graph** contains the invented Cedar Bridge account and policies. It stays under `planning-mds/examples/commercial-pc-account/` and is never imported as canonical runtime truth.

The **planning KG** contains shared concept/schema nodes and routing links to the feature/architecture documents. Author `kg-source` shards, rationale and file bindings; compile generated outputs. Do not add fictional companies, policy numbers, evidence rows or individual fact versions as canonical planning nodes. Examples are discoverable through bindings; stable `source_docs` point to this handoff, the glossary and feature READMEs because examples are outside the KG's allowed source-document roots.

The original EX-GL-001 and EX-INTEROP fixtures and their recorded evidence remain separate. This expansion has its own schema, expected outcomes and evidence status. The existing semantic-examples lifecycle gate now checks its structured records and lineage. RDF/OWL/SHACL/query execution remains pending after a temporary-environment install failed on DNS; do not borrow the prior example's passing semantic results.

After all source, fixture and documentation edits:

```bash
python3 scripts/validation/validate_semantic_examples.py
python3 scripts/kg/compile.py
python3 scripts/kg/validate.py --regenerate-symbols
python3 scripts/kg/validate.py --write-coverage-report
python3 scripts/kg/validate.py
python3 scripts/kg/validate.py --check-drift
python3 scripts/kg/validate.py --check-reproducible
python3 scripts/kg/lookup.py F0012 --tier 3 --fields full
python3 scripts/kg/lookup.py entity:insurance-party-role-assignment --tier 3 --fields full
python3 scripts/kg/lookup.py --file planning-mds/examples/commercial-pc-account/snapshot.jsonld
python3 scripts/run-lifecycle-gates.py
```

Run the framework tracker validator with the explicit Brain product root and `--skip-feature-evidence`. Refresh coverage **after the final documentation edit**: freshness hashes cover source content. When changing a teaching release artifact, refresh its deliberate fixture digest as well; a digest is not a compatibility result.

## Observed checks (2026-10-08)

- Teaching schema, reference, evidence, lineage, interval, selected-snapshot and fixture-digest validation: PASS.
- All three current planning lifecycle gates: PASS after refreshing coverage. KG drift, reproducibility and symbol checks: PASS. The two existing unused-edge warnings remain.
- Project plan-readiness, framework template alignment and tracker validation with the explicit product root: PASS. These checks do not approve an F0012/F0013 plan or supply missing PRDs.
- File lookup for `planning-mds/examples/commercial-pc-account/snapshot.jsonld` resolves `schema:commercial-pc-example` and F0012/F0013/F0015. Feature coverage remains 11 mapped, 55 excluded, zero uncovered; the expansion adds no feature approval.
- RDF graph equivalence, OWL-RL inference, SHACL and SPARQL expectations: NOT RUN. Installing the pinned optional tools into a temporary Python 3.12.13 environment failed because PyPI DNS resolution was unavailable.

The regenerated Python symbol sidecar uses name matching, not import/type resolution. Its candidate linking `vllm_graph_client.py`'s `validator.validate(value)` to this example validator is a false match: that receiver is a `jsonschema.Draft202012Validator`. Do not treat that diagnostic candidate as a runtime dependency on example data. The canonical feature links and exact file bindings above are the routing contract for this expansion.
