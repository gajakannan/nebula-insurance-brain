# F0009 provenance and correction examples

Synthetic development examples, illustrative expectations only; no F0009 runtime has executed. These extend the continuing [EX-GL-001 case](../../examples/neurosymbolic-gl/README.md) and ADR-0037's $20M/$2M correction. IDs below are explanatory aliases, not actual database IDs. No JSON payload shape is invented before Phase B. These examples stay outside the frozen evaluation holdout.

## EX-PROV-001 — Explain a source claim

**Definition:** source provenance connects an assertion to its persisted source and interpretation context. Confidence is a supplied interpretation attribute, not proof or canonical acceptance.

**Worked:** assertion A104 interprets an EachOccurrence limit as $20M from immutable artifact D1/page 2, with evidence E1 and the stored parser/run/model/profile metadata. A permitted internal read of A104 returns that exact chain, HUMAN_REVIEW is not asserted and no current ontology/model version is substituted for the stored one.

**Boundary:** an old row has no model digest or an evidence reference is missing. Its explanation says unavailable/incomplete, rather than claiming a complete source chain. No Docling or model call repairs it implicitly. A stored derivation/input reference stays a derivation reference and never becomes a fabricated document locator.

**Owner:** F0009-S0001 AC1–7. **Contracts:** ADR-0010, shipped F0006 assertion-record-v2/evidence; the internal result is [provenance-result-v1](../../schemas/provenance-result-v1.schema.json) under proposed ADR-0080.

## EX-PROV-002 — Correct without erasing or accepting

**Definition:** a human correction is a new assertion linked to the original and its governed decision. It is not a canonical acceptance.

**Worked:** Rosa, currently permitted to annotate, submits CORRECT after seeing E1 at its stored precision: $20M → $2M. R88 links A104 to HUMAN_REVIEW A105 and retains the evidence/revision/verified reviewer. A104 and D1 remain unchanged. No canonical version is created by this submission.

**Boundary:** replay R88 produces no extra child/decision/audit effect. A stale or different competing submission remains attributable and non-applied, without replacing A105. Unresolved evidence requires BLOCKED/EVIDENCE_UNRESOLVED and produces no child.

**Owner:** F0009-S0002 AC1–8. **Contracts:** ADR-0037, accepted ADR-0044, ADR-0058's accepted PDF BoxSelector amendment; existing review-decision and v2 assertion contracts.

## EX-PROV-003 — Explain an unchanged temporal remainder

**Definition:** a split remainder preserves an earlier accepted version's value/evidence over an unaffected valid interval; its split link is not an assertion-correction edge.

**Worked:** use the shipped F0008 retroactive split fixture. V1 carries a $2M limit; an independently authorized later commit introduces $5M on a proper subinterval and creates remainder V3 with split_of_version_id=V1. Reading V3 identifies V1, V1's original evidence/timestamps and the actual canonical change links/reason. Ending evidence is separately identified from supporting evidence.

**Boundary:** an asserted cross-slot predecessor or missing change endpoint cannot be labelled a complete lineage. This read never mutates a version or changes the PRESENT succession guard. A105 with no independently authorized commit remains merely a corrected assertion.

**Owner:** F0009-S0003 AC1–7. **Contracts:** accepted ADR-0077/0078, fact-answer/v1, fact-temporal/v1; no new change vocabulary.

## EX-PROV-004 — Current access controls old history

**Definition:** lineage access requires current authority for the root and every required linked source, even at a historical recorded-time coordinate.

**Worked:** a principal can read a fact and its source chain. Revoke READ on one correction ancestor's artifact, an ending source or the split predecessor's attestation source while retaining fact READ. Repeating the historical explanation returns the existing non-disclosing not-found outcome for the entire result.

**Boundary:** no partial excerpt, hidden source ID, edge/count or denial detail is returned. Cross-tenant/KB targets behave like missing targets. A duplicate decision lookup also checks current authority before returning stored results.

**Owner:** F0009-S0004 AC1–7. **Contracts:** F0002 current authority/structural scope, F0006 metadata-first discovery, F0007 read-before-reason and F0008 attestation-source remediation.

## EX-PROV-005 — Reserve future learning, with zero dataset effect

**Definition:** a reserved LearningCandidate reference is a durable future-consumer identity attached to an effective correction. It does not assert that a learning candidate has been processed, approved or added to a benchmark.

**Worked:** effective R88/A105 receives one reserved identity LC88 atomically with its correction and audit. A later authorized read returns LC88; replay returns the same identity. An injected reservation write failure rolls back the whole correction transaction.

**Boundary:** ACCEPT/REJECT/BLOCKED/stale/losing submissions have no reservation; historical rows get no fabricated identity. No model/learning/promotion job runs and no Golden Corpus or frozen-holdout bytes change. F0041 later adopts the reserved identity under its own plan; F0026 governs benchmark inclusion.

**Owner:** F0009-S0005 AC1–6 and S0006 AC1–6. **Contracts:** master blueprint §§88/106.3; reservation shape is [learning-candidate-reservation-v1](../../schemas/learning-candidate-reservation-v1.schema.json), with exact storage in the assembly plan; this is not the full F0041 candidate model.

## Required runtime reproduction

The later feature action must supply exact commands, fixture-to-database identity mappings and observed expected/actual comparisons for each example on PostgreSQL, including negative and rollback cases. Documentation consistency is the only validation claimed at Phase A.
