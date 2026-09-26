# Semantic examples and contributor reading path

Start with the [GL neurosymbolic walkthrough](neurosymbolic-gl/README.md), then use the [domain glossary](../domain/glossary.md) and [feature registry](../features/REGISTRY.md). The [Review Panel prototype](nebula-review-panel-live-files.html) is the one runnable artifact here. Persona files describe who contributes; these examples explain what the Brain represents and does.

## Example contract

Every introduced or changed semantic concept needs a plain-language definition, a worked example, a failure/boundary example, and a link to its owning feature/story and contract. Reuse stable example IDs across prose, structured records, tests, and review comments. Examples explain the authoritative requirements; they do not silently establish new insurance business rules.

Each example declares synthetic/licensed provenance, delivery phase, and whether its outputs are illustrative or observed. Structured records declare their schema. Expected outcomes are authored independently from implementations. Once the corresponding runtime ships, its story must supply a reproduction command and compare actual output against those expectations. A planning schema pass is not runtime proof, model accuracy, or feature completion.

Documentation/development examples remain outside the frozen evaluation holdout. Runtime evidence is recorded under operations evidence runs, with a link from the example; never replace an illustrative output with an unlabeled claim of observed execution.

## Coverage map

| Concept / boundary | Example | Owner / release |
|---|---|---|
| Neural interpretation plus symbolic evaluation | [EX-GL-001](neurosymbolic-gl/README.md) | F0065 S0001–S0006, v0.1B |
| Concept versus instance; relationship versus requirement | [Representation notes](neurosymbolic-gl/README.md#representation-notes) | F0012/F0013/F0065, v0.1 |
| Source, artifact, assertion, review, canonical fact, confidence | [Source to fact](neurosymbolic-gl/README.md#source-to-fact) and CASE-05/06 | F0004–F0018/F0022, v0.1 |
| FactSlot, typed money, basis, currency | CASE-01/02/03/09/10 | F0007/F0011/F0013/F0065 S0002, v0.1 |
| Valid time, recorded time, correction, retraction | [Temporal walkthrough](neurosymbolic-gl/README.md#temporal-walkthrough), CASE-11–15 | F0008/F0010/F0019/F0025/F0065 S0004, v0.1 |
| Derivation, rule authority, assessment versus approval | [Assessment](neurosymbolic-gl/README.md#assessment), CASE-16/17 | F0009/F0018/F0065 S0001/S0003, v0.1 |
| Unknown, explicit negative, conflict | CASE-04/07/08 | F0006/F0018/F0065 S0002, v0.1 |
| Structural tenancy, tenant entity identity and explicit KB access | [EX-AUTHX-001–003](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/worked-examples.md) | F0002 S0001/S0003; ADR-0061; AuthX v1 schema |
| Verified principal, membership and current resource scope | [EX-AUTHX-004–011](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/worked-examples.md) | F0002 S0002–S0004; glossary F0002 refinements; AuthX v1 schema |
| Resource envelope, delegation and durable decision/authentication events | [EX-AUTHX-012–018](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/worked-examples.md), [structured shapes](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/contract-examples.json) | F0002 S0004–S0006; ADR-0062; synthetic planning examples, no runtime proof |
| Derived-result and evidence authorization | CASE-18/19 | F0002/F0018/F0065 S0005/F0026, v0.1 |
| Evidence anchoring, selector shapes, declared precision, unresolved evidence | [Review Panel prototype](nebula-review-panel-live-files.html) | F0001 S0004/F0022, v0.1B |
| Open statements, typed assertions, signature alignment, implication rules | [EX-SEM-001/002](statements-time-and-governance.md#open-statements-and-alignment) | F0006 storage, v0.1A; F0066 alignment, v0.2B; ADR-0063 |
| Time mentions, document time context, resolution grade, precision, unknown ends, temporal kind | [EX-SEM-003/004](statements-time-and-governance.md#time-interpretation) | F0004/F0008/F0016/F0019/F0025, v0.1; ADR-0064 |
| Admission checks, drops, text origin, statement mood | [EX-SEM-005–007](statements-time-and-governance.md#admission-origin-and-mood) | F0004/F0006/F0016/F0022, v0.1; F0052 routing, v0.3; ADR-0065 |
| Names as time-bounded claims; similarity only proposes | [EX-SEM-008](statements-time-and-governance.md#names) | F0007/F0017, v0.1A; F0027, v0.2B; ADR-0066 |
| Impact holds, human precedent, automation fuse | [EX-SEM-009](statements-time-and-governance.md#automation-and-impact) | F0027/F0043, v0.2B; F0059, v0.4+; ADR-0067 |
| Decision basis fingerprints and staleness | [EX-SEM-010](statements-time-and-governance.md#decision-basis) | F0016/F0066/F0032, v0.1–v0.2B; F0056, v0.4+; ADR-0068 |
| External action attempts and uncertain outcomes | [EX-SEM-011](statements-time-and-governance.md#action-attempts) | F0050, v0.3; F0059, v0.4+; ADR-0069 |
| Vector similarity versus accepted facts | [EX-FUTURE-001](future-semantics.md#retrieval-projection) | F0033/F0035, v0.2A |
| Learned candidates and repeated model claims | [EX-FUTURE-002](future-semantics.md#learning-candidate) | F0041/F0042, v0.2B; F0060 rule promotion, v0.4+ |
| Obligations versus observed facts | [EX-FUTURE-003](future-semantics.md#normative-obligation) | F0052, v0.3 |
| Hypothetical assumptions versus canonical state | [EX-FUTURE-004](future-semantics.md#hypothetical-scenario) | F0053, v0.3 |

## Review Panel prototype

[`nebula-review-panel-live-files.html`](nebula-review-panel-live-files.html) is a self-contained page that embeds four real files — a declarations PDF, an endorsement DOCX, an SOV XLSX, and a loss-run CSV — and parses them in the browser at load: pdf.js reads the PDF, fflate unzips the OOXML, `TextDecoder` handles the CSV. Every coordinate, paragraph path, cell reference, and character offset it displays is derived from the bytes at runtime, including the anchoring failures. It also accepts a dropped file of your own, and its anchor probe shows the locator any piece of text in that file resolves to.

It is design evidence for [ADR-0057](../architecture/decisions/ADR-0057-nebula-owns-the-native-evidence-review-panel.md) and [ADR-0058](../architecture/decisions/ADR-0058-evidence-anchoring-and-selector-contract.md) and illustrative under this document's contract: synthetic documents, no server, no persistence, no authorization, and no OCR path. It demonstrates that the selector crosswalk survives real parser output; it demonstrates nothing about the governed loop. Observed runtime evidence for that loop belongs to F0001-S0004 and is recorded under operations evidence runs.

CASE identifiers refer to the [challenge table](neurosymbolic-gl/cases.md). F0065 owns the continuing example; upstream features own their domain contracts and cite the relevant step rather than duplicating the fixture.

## Checks

From the repository root, run `python3 scripts/validation/validate_semantic_examples.py`. It validates the educational JSON against its local schema and checks record and planning references. Reviewers still judge the meaning, the accuracy of expected outcomes, and completeness of concept coverage. The product checklist makes that review explicit.
