# Ontology prerequisite amendment — planning handoff

**Status:** Architecture prerequisites and KG routing only. Features remain Planned; ADR-0045 remains Proposed. This amendment is not a completed feature plan or phase approval.

## Framework path and outstanding planning

The initial edit updated feature dependencies and prose, compiled the KG, refreshed coverage, and passed structural checks. It did not execute the framework's formal `plan` action. A subsequent retrieval audit found that `coverage_excluded` suppressed those features' dependencies and ADR links from the generated mappings. The correction follows the framework's direct Architect guidance for targeted artifact revisions and the structural requirements of plan G4/G5: author shards, capture shared nodes and rationale, compile, check drift/reproducibility, and verify actual retrieval.

The framework's `agents/docs/AGENT-USE.md` permits direct-role work for a known artifact scope. Its `agents/docs/KNOWLEDGE-GRAPH.md` requires backfilling mappings when lookup returns only an excluded target. F0012/F0013/F0015/F0024/F0030/F0062 now have explicit planning mappings instead of coverage exclusions. These mappings do not establish PRD completeness, approved architecture, implemented persistence, or runtime proof. Feature statuses, delivery phases, and the v0.1 scope guard are unchanged.

For the next formal F0012 plan, use `agents/actions/spec/plan.yaml` with `FEATURE_ID=F0012`, `PHASE=A+B`, `FEATURE_MODE=existing`, and the explicitly selected Brain product root. The existing folder is a reserved feature with prerequisite notes; its PRD, stories, STATUS and assembly plan still need authoring. Record Phase A approval before Phase B, then the ontology sync and Phase B approval gates. Do not infer approval from this amendment or fabricate a prior plan run. Repeat for F0013 and F0015 in dependency order.

## Source context to load

1. [F0012 prerequisites](../features/F0012-foundation-ontology/README.md) and [F0013 prerequisites](../features/F0013-insurance-core-gl-ontology/README.md): identities, semantics, constraint execution, missingness and release metadata before vocabulary authoring.
2. [ADR-0045](decisions/ADR-0045-ontology-release-compatibility.md): proposed compatibility, impact, replay and acceptance contract; the production namespace, authoring schema, physical storage and consumer version policy remain to be settled.
3. [Release records](data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045), [glossary](../domain/glossary.md#ontology-release-vocabulary-proposed-adr-0045-contract), [synthetic cases](../examples/ontology-release-contracts.md), and [GL interchange examples](../examples/ontology-interchange/README.md). The interchange bundle illustrates the same vocabulary/facts in YAML, RDF/OWL Turtle and JSON-LD, with separate SHACL value/completeness constraints. It is a proposal, not a production schema or implementation.
4. [F0065 assessment contract](../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md): missing required inputs yield `UNKNOWN`; first-result lineage and exact historical reconstruction already apply.
5. [F0030](../features/F0030-ontology-workbench/README.md) and [F0062](../features/F0062-advanced-reasoners/README.md): deferred mapping/module tooling and optional reasoner providers. OPEN extraction stays ontology-free under F0066; PostgreSQL remains authoritative under ADR-0002.

## Dependency evidence audit

The dependency relationships are explicit planning requirements. Their implementation/approval evidence is **audit pending** for the formal feature plan; KG integrity is not dependency readiness.

| Consumer | Added prerequisites | Scope |
|---|---|---|
| F0013 | F0012 | Foundation authoring and release contracts before GL vocabulary |
| F0015 | F0011, F0012, F0013 | JSON Schema contracts and exact foundation/GL vocabulary releases before compiler implementation |
| F0024 | F0013 | GL vocabulary for the integrated interpretation/assessment slice |

Existing prerequisites remain in each authored feature shard. F0030→F0012 and F0062→F0055 retain their existing inferred provenance pending formal planning. This amendment does not certify any upstream feature as ready.

## Follow-up review dispositions (2026-10-07)

| Review finding | Disposition |
|---|---|
| Blueprint §20 `parents:` versus §82 `parent:` | F0012 now explicitly requires a canonical cardinality/schema and migration or rejection of the alias before authoring. Teaching YAML uses plural `parents:` as a proposal; the PRD must settle the conflict. |
| Unspecified ontology-to-AGE mapping | Data model, §79/§112 and ADR-0045 now require a versioned, hashed projection mapping in the release artifacts. The GL example proposes `hasLimit → HAS_LIMIT`, `hasForm → HAS_FORM`, `hasTrigger → HAS_TRIGGER`, with endpoint/lineage/context obligations and explicit omissions. No runtime writer or final physical schema is claimed. |
| Accepted ADR-0012 lists undefined OKF | Its accepted decision is preserved. A dated note points to the scoped clarification proposed in ADR-0045. Formal reconciliation is pending ADR-0045 acceptance; neither edit asserts an implemented OKF adapter. |
| Unsupported `explicit` edge provenance hidden by coverage exclusions | Corrected to schema-supported `extracted` in F0025/F0026/F0056 and the additional occurrence in F0055. F0024 was already corrected. Dependencies/confidence are unchanged; the four features retain their coverage exclusions. |
| Mapped features may be planning-only | Product agent instructions and this handoff explain that coverage measures retrieval mappings, not completed Phase B, approval, or implementation. Six newly mapped features retain explicit planning-only notes. |

The semantic fixture checks were run on 2026-10-07 under Python 3.14.4 with rdflib 7.1.4, pySHACL 0.30.1 and owlrl 7.1.4, and all matched the authored expectations. The example README's [observed results](../examples/ontology-interchange/README.md#observed-results-2026-10-07) record the commands, outcomes and fixture digests separately from the authored expectations. SHACL shows the missing-input versus malformed-value distinction; it does not execute Nebula's assessment engine or show that it returns `UNKNOWN`. JSON/YAML parsing and repository/KG checks do not establish RDF equivalence, OWL consequences, SHACL outcomes, assessments, or AGE behavior.

## Retrieval and structural verification

Run from the Brain product root:

```bash
python3 scripts/kg/compile.py
python3 scripts/kg/validate.py --write-coverage-report
python3 scripts/kg/validate.py --check-drift
python3 scripts/kg/validate.py --check-reproducible
python3 scripts/kg/lookup.py F0013 --tier 2 --fields summaries
python3 scripts/kg/lookup.py F0015 --tier 3 --fields full
python3 scripts/kg/lookup.py adr:0045 --tier 3 --fields full
python3 scripts/kg/lookup.py entity:ontology-release --tier 3 --fields full
python3 scripts/kg/lookup.py glossary_term:ontology-projection-mapping --tier 3 --fields full
python3 scripts/kg/lookup.py --file planning-mds/examples/ontology-interchange/facts.jsonld
python3 scripts/kg/blast.py entity:ontology-release
```

Expected routing: F0013 returns F0012 as a dependency; F0015 returns F0011/F0012/F0013; F0024 returns F0013; ADR-0045 and the seven shared ontology nodes return the current source paths and Proposed/planning-only context. The release node's `related_entities` links interpretation, rule versions and assessments. F0030/F0062 preserve the deferred boundaries. Raw feature docs, ADRs and contracts govern if a routing summary disagrees.

Run the framework tracker validator with the explicit product root and `--skip-feature-evidence`, as specified for plan closeout. No story files changed, so there is no new story index content. Full feature plans must still execute their required story and approval gates; a passing project-structure check is not a substitute.

### Observed initial amendment checks

| Check | Result |
|---|---|
| KG compile, integrity, drift, reproducibility | Passed; 11 mapped features, 55 excluded, zero uncovered. No generated projection was hand-edited. |
| F0012/F0013/F0015/F0024/F0030/F0062 lookup | Passed; all remain Planned, expose ADR-0045/source context, and state that phase approvals and dependency evidence audit are pending. All five added prerequisite edges were returned. |
| ADR-0045, release and compatibility-node lookup | Passed; the handoff and current source documents are retrievable. |
| Example file reverse lookup | Passed; `ontology-release-contracts.md` resolves through its compatibility-analysis binding to feature context. |
| Tracker validation and project structure | Passed; tracker validation used the explicit Brain root and `--skip-feature-evidence`. |
| Modified Markdown links | Passed for the initial amendment; 14 documents checked, zero missing paths or anchors. |

### Observed follow-up checks (2026-10-07)

| Check | Result |
|---|---|
| KG integrity, drift and reproducibility | Passed after compiling authored shards; 11 mapped features, 55 excluded, zero uncovered, 17 bindings. Existing two unused-edge warnings remain. |
| Planning lifecycle, tracker, project-structure and template validators | Passed; all three configured planning lifecycle gates passed. Tracker validation used the explicit product root and `--skip-feature-evidence`. No formal plan-review run or phase approval is claimed. |
| New projection-mapping node and example reverse lookup | Passed; the shared node returns F0012/F0013/F0015/F0030 and source documents. `facts.jsonld` resolves through the compatibility-analysis binding to planning context. |
| Authored dependency provenance, including excluded features | Passed; all 60 explicit provenance annotations use supported values. |
| Markdown links and JSON/YAML syntax | Passed; 17 changed/new Markdown documents had zero missing local paths or anchors. Both new YAML files and the JSON-LD document parse as YAML/JSON. |
| RDF/OWL/SHACL semantics | Passed 2026-10-07 on Python 3.14.4 (3.12 not verified): Turtle/JSON-LD isomorphic, both selected OWL-RL consequences present, five SHACL runs at expected exit codes. Third-party tools only; no Nebula assessment, storage or AGE behavior exercised. See the example README's observed results. |

Retrieval limits observed: `blast.py entity:ontology-release` returns five direct feature mappings, but its current neighbor walk does not traverse canonical `related_entities`/`related_nodes`; inspect the canonical lookup for those relationships. `diff-impact.py HEAD` analyzes code symbols and reports these Markdown/YAML paths as unresolved; its empty symbol impact is not proof of no planning impact. Neither limitation is changed by this amendment. Example bindings list exact files because wildcard expansion only includes Git-tracked files and these additions are still uncommitted. F0024's previously excluded F0065 edge used unsupported provenance `explicit`; it now uses the schema's `extracted` value, with the same dependency and confidence.
