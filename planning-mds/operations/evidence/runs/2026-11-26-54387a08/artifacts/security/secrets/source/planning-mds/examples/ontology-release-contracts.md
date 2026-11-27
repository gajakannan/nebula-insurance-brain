# Ontology release contracts — synthetic planning examples

All identities, releases, values, and results below are synthetic and illustrative. These cases describe expected behavior for the proposed [ADR-0045](../architecture/decisions/ADR-0045-ontology-release-compatibility.md); they are not runtime evidence. F0012/F0013 own the initial contracts in v0.1A, F0015 owns TEMPLATE compilation, and F0065 owns stored assessments in v0.1B. Their PRDs must assign the outstanding stories and acceptance evidence. Advanced evolution/reasoning tooling remains F0030/F0062.

For concrete YAML, RDF/OWL, Turtle, JSON-LD and SHACL representations, read [EX-INTEROP-001–004](ontology-interchange/README.md). It reuses the complete-limit teaching case, separates asserted and inferred facts, and declares example projection mappings. The namespace and authoring shape remain proposed.

## Stable term identity

**EX-ONT-001.** A fictional namespace maps `insurance.coverage.limit` to `https://example.invalid/ont/insurance/coverage/limit`. Changing its display label from “Coverage limit” to “Limit” preserves that IRI. A release records the revised label and definition alongside its original version. This illustrates a mapping, not the selected production namespace.

**Boundary:** The same IRI does not make a new definition compatible. If a general limit concept splits into occurrence and aggregate concepts, preserve the old definition in its release, assign distinct identities to the new concepts, and record the split/migration mapping. Do not reinterpret old facts by looking up today's definition. Owner: [F0012](../features/F0012-foundation-ontology/README.md), ADR-0045 identity/change classes.

## Constraint execution and missing values

**EX-ONT-002.** A document supports a GL coverage assertion but provides no usable limit amount. If the assertion meets its own evidence and admission requirements, the absence of the amount alone does not prevent acceptance. An on-demand guideline assessment that needs the amount returns `UNKNOWN` with its missing-input context, as in [CASE-04](neurosymbolic-gl/cases.md). The requirement declares its assessment consumer/stage, applicability, outcome, and accepted-input data basis.

**Boundary:** A malformed supplied amount can fail its structural admission check. An absent amount is neither zero nor an explicit denial of coverage; absence of an applicable comparison is also different from conflicting amounts. Owner: [F0013](../features/F0013-insurance-core-gl-ontology/README.md) and the [F0065 assessment contract](../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md).

## Reproducibility and compatibility

**EX-ONT-003.** Release R1 has existing classes A and B and an accepted instance of A. R2 adds the rule `A subClassOf B`. Within a supported subclass ruleset, the same instance now also belongs to B. The impact report records that changed conclusion about existing terms; calling the edit additive does not remove its impact. An earlier result pinned to R1 still uses R1's definitions and exact inputs.

**Boundary:** Retaining R1 makes historical reconstruction possible even when R2 changes conclusions. It does not establish R2's compatibility with every consumer. A check limited to one ruleset or fixture cannot prove all possible conclusions unchanged, and a truncated/unsupported check remains unresolved. Owner: F0012/F0013 and ADR-0045 compatibility/impact gate.

**EX-ONT-004.** In a separate comparison, a candidate release changes one consumer's shape from allowing an unspecified currency to requiring an explicit currency. The inference rules and closure stay the same, but an input previously admitted by that consumer now fails its declared validation boundary. The impact report records the constraint tightening, affected profiles/data, and required consumer migration or review.

**Boundary:** Passing an inference comparison cannot erase that validation impact. Historical assessments retain their original releases and missing-value semantics. This fictional shape change is not a change to F0065's existing currency requirements. Owner: F0012/F0013/F0015 and ADR-0045.

## Composed releases and packages

**EX-ONT-005.** A GL release manifest selects foundation module version 1 and GL module version 2 at exact digests, plus their dependency lock and the associated constraint, profile/template/compiler, and evidence contracts. A TEMPLATE interpretation run stores the composed release ID. Rollback selects an earlier compatible release for new runs and preserves the newer runs and assessments already recorded.

**Boundary:** A floating foundation dependency cannot define a reproducible release. A logical module containing all relevant axioms can still be an incomplete extraction package if it omits constraints or evidence requirements. This packaging example does not put ontology content into OPEN prompts. Owner: [release records](../architecture/data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045), F0012/F0013/F0015; optional extraction tooling F0030/F0062.

## First stored assessment lineage

**EX-ONT-006.** A saved assessment references accepted fact versions FV1/FV2, immutable rule version G1, ontology release R1, its evaluator version, valid/known coordinates, and the evidence/derivation links behind those inputs. A later assessment using FV3 creates a distinct record.

**Boundary:** A source-document link, a rule name without a version, or an input digest alone cannot identify the exact premises for historical reconstruction. General dependency propagation may ship later; recording these dependencies cannot. Owner: [ADR-0026](../architecture/decisions/ADR-0026-derived-facts-have-dependency-lineage.md) and [F0065](../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md).

## Foundation release runtime (F0012)

**EX-ONT-007 — release reference and installation.** The foundation module (`ontology/modules/foundation/module.yaml`) compiles to `foundation@1`. Its release reference is `ontrel:sha256-` followed by the manifest digest, so it names the exact content: 53 terms, 15 predicates such as `fnd:accountOrganization@v1` (ETERNAL) and `fnd:accountStatus@v1` (STATE), and the projection mapping. Installing it into one tenant/KB writes immutable rows in one transaction. Installing the same reference again changes nothing; installing it into another KB writes that KB's own rows. A slot created with `predicate_release_ref = ontrel:sha256-…` keeps that reference when a later release is installed or activated.

**Boundary:** A relabelled module that keeps `foundation@1` as its version is new content under an old version and is refused (`MODULE_VERSION_IMMUTABLE`). A predicate key from a release installed only in another KB stays `PREDICATE_UNREGISTERED`. Installation never selects a release.

**EX-ONT-008 — impact report, review and selection.** A steward reports `foundation@1` → candidate, reviews the report and activates the candidate. One candidate splits `foundation.organization.operates-at` into premises and office properties. The report classifies the old and new IRIs as `split`, counts the existing `fnd:operatesAt@v1` slot against all identity-v1 slots in the KB, and lists profiles/templates (F0015), assessments (F0065) and projections (F0034) as unexamined. After activation, the existing slot still resolves through `foundation@1`; a rollback appends a third selection and returns new work to `foundation@1`.

**Boundary:** A report with an unclassified change or an unresolved closure is `incomplete` and cannot be activated. A rejected review, a report for another candidate, or a report whose predecessor is no longer the selected release each refuses activation with a typed reason, and the refusal is audited. Selections are appended; no release, slot, version or assertion row is rewritten.

Runtime reproduction: feature run `2026-11-26-54387a08`, engine suites `test_ontology_release_install.py`, `test_ontology_activation.py` and `test_temporal_kind_activation.py`, and the account-scoped Cedar Bridge cases on foundation IRIs in [commercial-pc-account/foundation](commercial-pc-account/foundation/README.md). Synthetic development data, outside the frozen holdout. Owner: [F0012](../features/F0012-foundation-ontology/README.md) S0002/S0004–S0007; proposed [ADR-0081](../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md).
