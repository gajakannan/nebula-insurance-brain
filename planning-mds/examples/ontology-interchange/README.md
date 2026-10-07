# GL ontology interchange — one example in several representations

**Status:** Synthetic, proposed teaching fixtures. No production namespace, authoring schema, exporter, AGE writer, or supported OWL profile is selected here. The RDF equivalence, inference and SHACL checks below were run on 2026-10-07 under Python 3.14.4 and matched the authored expectations; see [Observed results](#observed-results-2026-10-07). They exercise these fixtures with third-party RDF tools only. They do not execute any Nebula component, and they are not acceptance evidence for a feature.

**Owners:** F0012/F0013 authoring and semantics, F0015 TEMPLATE profile packaging, F0065 assessment boundaries. F0030/F0062 own later interoperability tooling. F0012 must assign the conformance stories when its PRD is written. These development fixtures stay outside the frozen evaluation holdout.

## What each file does

| File | Read it for |
|---|---|
| [ontology.yaml](ontology.yaml) | Proposed Nebula authoring: stable IDs, hierarchy, inference semantics, constraint execution context and projection mappings |
| [ontology.ttl](ontology.ttl) | The example vocabulary expressed as RDF/OWL in Turtle |
| [facts.ttl](facts.ttl) | One synthetic GL coverage with a USD 500,000 each-occurrence limit |
| [facts.jsonld](facts.jsonld) | The same asserted fact graph in JSON-LD, with a local inline context |
| [shapes.ttl](shapes.ttl) | Validation of supplied limit values; absence alone is allowed |
| [assessment-shapes.ttl](assessment-shapes.ttl) | Completeness for the named assessment consumer; missing required inputs are a gap |
| [missing-limit.ttl](missing-limit.ttl) | A coverage with no extracted limit |
| [malformed-amount.ttl](malformed-amount.ttl) | A supplied amount with the wrong datatype |
| [expected-inferences.ttl](expected-inferences.ttl) | Two selected inferred triples, kept separate from assertions |
| [expected-results.yaml](expected-results.yaml) | Expected case outcomes and references to the existing evidence/assessment example |

The YAML and Turtle vocabulary are hand-authored counterparts, not generated compiler output. YAML uses the proposed plural `parents:` field; master blueprint sections 20 and 82 disagree on `parents:`/`parent:`, so F0012 must settle that contract. The YAML's `temporal_kind: STATE` annotations, execution context and projection mapping remain application metadata in this example, with no corresponding OWL axioms. This small vocabulary omits full definition/example/regression annotations, dependency composition, and production ownership/storage contracts.

## Formats and semantics

RDF represents a graph of subject–predicate–object statements. Turtle and JSON-LD are serializations of that graph. OWL vocabulary gives ontology statements a formal meaning; an `.owl` extension is not needed for `ontology.ttl` to contain OWL. SHACL expresses validation constraints in a separate RDF graph. See the W3C specifications for [Turtle](https://www.w3.org/TR/turtle/), [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/), [OWL 2](https://www.w3.org/TR/owl2-primer/), and [SHACL](https://www.w3.org/TR/shacl/).

The example ID `insurance.coverage.has-limit` maps to `https://example.invalid/nebula/ont/insurance/coverage/has-limit`. Turtle's `cov:has-limit` and JSON-LD's `hasLimit` expand to that exact IRI. The module revision has its own version IRI (`…/modules/insurance.general-liability.example/1`, the `owl:versionIRI` in `ontology.ttl`); the illustrative composed release `…/releases/gl/v1` selects that module version in `ontology.yaml` and is not the module's identity. All example IRIs are illustrative and need not resolve over HTTP. Local JSON-LD context declarations and absence of `owl:imports` avoid remote document loading when parsing these files.

`"500000.00"` is carried as an `xsd:decimal` typed value in both serializations. The JSON-LD string preserves the decimal lexical form; it must not become a binary floating-point amount. The [F0065 contract](../../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md) governs actual money comparison, basis/currency applicability, evidence and authorization.

## Inference versus validation

**EX-INTEROP-004:** The asserted coverage has type `cov:general-liability`. Its subclass axiom implies type `ins:coverage`. The asserted `cov:has-limit` relationship and the OWL inverse-property axiom imply `lim:of-coverage`. [Expected inferences](expected-inferences.ttl) list these two consequences, not a complete closure or a conservativity proof. The broader OWL-RL tool below is only an optional demonstration provider; its supported behavior does not define Nebula's v0.1 supported subset.

Domain/range declarations also have inference semantics. They do not express a requirement that the source document supplied a value. There is no OWL cardinality axiom pretending that an unobserved limit has been extracted, and no inference supplies a missing amount or evidence.

Validation intentionally uses **no inference**. A supplied limit must have an asserted type and well-formed supplied values. The two shapes graphs run separately according to `ontology.yaml`'s consumer/stage metadata. That YAML metadata is an application proposal; it is not part of SHACL and the SHACL processor does not dispatch lifecycle stages or produce business assessments.

| Case | Supplied-value shapes | Assessment completeness | Expected application handling |
|---|---|---|---|
| EX-INTEROP-001: complete | Conforms | Conforms | Given the existing authorized/applicable USD 1M example rule and exact accepted input, `BELOW_GUIDELINE` |
| EX-INTEROP-002: missing limit | Conforms | Does not conform: missing input | F0065 returns `UNKNOWN`; the absence alone does not block an otherwise admissible coverage fact |
| EX-INTEROP-003: malformed amount | Does not conform | Not run on a rejected candidate | Reject the malformed supplied value; do not treat it as an accepted input or a zero amount |

SHACL nonconformance does not by itself reject a policy. Completeness failure maps to `UNKNOWN` only for missing inputs under the declared consumer policy. Known incompatible basis/currency remains `NOT_APPLICABLE`, conflicts remain `CONFLICT`, and authorization/configuration/validator errors remain errors. These shapes do not implement that entire outcome table. A conformance result alone also cannot prove a valid shape selected the intended population: for the missing-limit fixture, supplied-value conformance has no limit focus nodes, while the assessment shape targets the coverage and detects the gap.

## Evidence, time and projection boundaries

The complete case reuses EX-GL-001's illustrative EX-COV-001, EX-F-001, EX-A-001 and EX-EV-001 through [expected-results.yaml](expected-results.yaml). At the declared February snapshot, the accepted limit amount in that teaching example is USD 500,000. The form/trigger relationships are synthetic additions for illustrating edge mapping; they have no claimed source evidence. The missing/malformed cases are separate hypothetical inputs and must not be attributed to EX-F-001.

The RDF graph is a deliberately partial view. The sidecar identifies its source release and the illustrative interchange release separately; it does not overwrite the source records' release. It does not encode the full bitemporal kernel, grants or review history. A production export must preserve exact fact/relationship versions, evidence, ownership and time in its agreed envelope/dataset representation; a direct triple cannot replace that lineage. PostgreSQL remains authoritative, and none of these files can be imported as accepted canonical data. No ontology content is added to OPEN extraction prompts.

The YAML proposes `hasLimit → HAS_LIMIT`, `hasForm → HAS_FORM`, and `hasTrigger → HAS_TRIGGER`, all directed outward from coverage. Amount/currency/basis are declared projected properties; the derived inverse is explicitly omitted to avoid a duplicate edge. Mapping version/digest, endpoint identity, qualifiers, source lineage and time/ownership requirements must be locked with a production release. Per-record lineage values belong to each projected record's context, not the immutable mapping definition. The [release contract](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) requires changed mappings to participate in projection impact/rebuild analysis. These mappings have no AGE execution proof yet.

## Reproduce the semantic checks

The checks were observed under Python 3.14.4 only; other Python versions, including 3.12, have not been verified. These optional teaching dependencies do not alter Brain's runtime dependencies. Install the pinned tools in an environment with package access:

```bash
python3 -m venv /tmp/nebula-ontology-example-tools
/tmp/nebula-ontology-example-tools/bin/python -m pip install rdflib==7.1.4 pyshacl==0.30.1 owlrl==7.1.4
cd planning-mds/examples/ontology-interchange
```

Compare the two fact serializations and check the two expected inferred triples:

```bash
/tmp/nebula-ontology-example-tools/bin/python - <<'PY'
from rdflib import Graph
from rdflib.compare import isomorphic
from owlrl import DeductiveClosure, OWLRL_Semantics

asserted = Graph().parse('facts.ttl', format='turtle')
jsonld = Graph().parse('facts.jsonld', format='json-ld')
assert isomorphic(asserted, jsonld), 'Fact serializations differ'
expected = Graph().parse('expected-inferences.ttl', format='turtle')
assert all(triple not in asserted for triple in expected), 'Expected inference was asserted'
closure = Graph().parse('ontology.ttl', format='turtle') + asserted
DeductiveClosure(OWLRL_Semantics).expand(closure)
assert all(triple in closure for triple in expected), 'Expected consequence is missing'
print('Fact graphs equivalent; two selected expected consequences present')
PY
```

Run each SHACL command independently. The two commands marked exit 1 are expected nonconformance, not tool failure; any other exit status needs investigation. `-m` also checks shape syntax against the SHACL meta-shapes.

```bash
# Expected exit 0: complete supplied values and complete assessment inputs.
/tmp/nebula-ontology-example-tools/bin/python -m pyshacl -m -i none -s shapes.ttl facts.ttl
/tmp/nebula-ontology-example-tools/bin/python -m pyshacl -m -i none -s assessment-shapes.ttl facts.ttl
# Expected exit 0: no malformed supplied limit value.
/tmp/nebula-ontology-example-tools/bin/python -m pyshacl -m -i none -s shapes.ttl missing-limit.ttl
# Expected exit 1: missing assessment input; consumer handles this as UNKNOWN.
/tmp/nebula-ontology-example-tools/bin/python -m pyshacl -m -i none -s assessment-shapes.ttl missing-limit.ttl
# Expected exit 1: supplied string fails the decimal constraint.
/tmp/nebula-ontology-example-tools/bin/python -m pyshacl -m -i none -s shapes.ttl malformed-amount.ttl
```

Tool interfaces: [RDFLib 7.1.4](https://pypi.org/project/rdflib/7.1.4/) and [pySHACL 0.30.1](https://pypi.org/project/pyshacl/0.30.1/). Record tool versions, actual results and fixture hashes for each execution separately from the authored expectations, as below. These commands verify selected interchange/shape behavior; Nebula acceptance, authorization, storage, assessments and projection rebuilding require their own feature evidence.

## Observed results (2026-10-07)

| Item | Value |
|---|---|
| Run | 2026-10-07 10:04 UTC, Linux (WSL2 kernel 6.18.33.1) |
| Python | 3.14.4, in an isolated venv outside the Brain repo |
| Packages | rdflib 7.1.4, pySHACL 0.30.1, owlrl 7.1.4 |
| Invocation | The equivalence/inference snippet above, saved as a script that takes the fixture directory as an argument (same assertions); the five pySHACL commands above as written, run from this directory |

| Check | Expected | Observed |
|---|---|---|
| `facts.ttl` and `facts.jsonld` isomorphic; both selected consequences absent from assertions and present after OWL-RL expansion | pass | pass, exit 0 |
| `shapes.ttl` on `facts.ttl` | exit 0 | exit 0, `Conforms: True` |
| `assessment-shapes.ttl` on `facts.ttl` | exit 0 | exit 0, `Conforms: True` |
| `shapes.ttl` on `missing-limit.ttl` | exit 0 | exit 0, `Conforms: True` |
| `assessment-shapes.ttl` on `missing-limit.ttl` | exit 1 | exit 1, `Conforms: False`, 1 result on `cov:has-limit` ("The selected assessment needs limit input.") |
| `shapes.ttl` on `malformed-amount.ttl` | exit 1 | exit 1, `Conforms: False`, 2 results on `lim:amount` (datatype and minimum) |

**What this shows:** the two fixture graphs are equivalent; the two selected OWL-RL consequences follow from the vocabulary; and the two SHACL graphs separate their concerns. A missing limit passes supplied-value validation but fails the named assessment-completeness shape, while a malformed supplied amount fails supplied-value validation.

**What this does not show:** SHACL nonconformance is not a Nebula outcome. These runs do not execute Nebula's assessment engine, and they do not demonstrate that it returns `UNKNOWN` for a missing limit, or that it rejects a malformed candidate. Those behaviors remain requirements of the [F0065 assessment contract](../../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md) and need their own feature evidence. The inference check covers only the two selected consequences, not a closure, a supported profile or a conservativity result.

Fixture SHA-256 digests at the time of the run:

```text
78a8ca228d7901d27c7a50078e07be1bf4e7b6ccf3fe57c95a39223e71446ad0  ontology.ttl
f99e1267e333c3ce556434fbde3d71f1dd6cd686c2f94ae4495e6765c783b3f1  ontology.yaml
361dff672965c09b96268511e9a5207031af9be0dcbfba44808f5ae8176b2976  facts.ttl
bae855fc1c665cc82d662bfce16d168833af54152c50260d343e8caae78f8365  facts.jsonld
b157eda6c71ce805db3237448319632018acc108761fa27687c63f761ab4b9cf  shapes.ttl
3b68303b99ebace9f64e76c32d956196e3f7d8c510fec1844748f42cf5abb55f  assessment-shapes.ttl
d0a4703860f1cb667366acfa718a6d242498a63059dee588198a21c2a70afd19  missing-limit.ttl
196bae5e687b0bee2e2f4f4134660b1bb8cb3a1e6b8f3ca6ef8819e05d92c758  malformed-amount.ttl
7972ef4677680bb14893c60176ac11e702b0b73a3fdd733c65ee71c558f55f8b  expected-inferences.ttl
565e120a13ea05ea5510ed8a7abae5ba4ec5df3f206e0092be6a270b6723db95  expected-results.yaml
```
