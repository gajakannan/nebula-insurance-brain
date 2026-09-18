# Data Model — Nebula Insurance Brain

**Status:** Baseline (extracted from the master blueprint on 2026-09-05); refined per feature in Phase B.

PostgreSQL is the authoritative runtime store (ADR-0002). Graph and vector stores are projections (ADR-0022, ADR-0023). Semantics of the tables below are defined in the master blueprint: canonical world model (section 12), FactSlot (section 13), bitemporal facts (sections 14 to 16), provenance (section 17), content versus evidence identity (section 18), and flexible schema representation (section 20). Every authoritative row carries `tenant_id` and `knowledge_base_id` (ADR-0030) and audit fields (`created_at`, `recorded_at`, actor).

The baseline sections below are reproduced from the master blueprint so implementers have one file to read; when they diverge, the master blueprint plus accepted ADRs win until this document is promoted by a Phase B decision. The F0065 addition below is explicitly a proposed feature contract rather than an existing runtime schema.

## Core PostgreSQL Tables (master blueprint section 78)

```text
tenant
workspace
knowledge_base
principal
membership
role
permission

source_document
document_version
content_artifact
content_block
content_table
content_table_cell

document_profile
document_classification_assertion

ontology
ontology_version
ontology_module
ontology_concept
ontology_property
ontology_relation
ontology_axiom
ontology_label
ontology_alias

extraction_profile
extraction_profile_module
semantic_interpretation_run

assertion
assertion_value
assertion_relationship
assertion_evidence

entity
entity_type
entity_alias

fact_slot
fact_slot_qualifier
canonical_fact_version
canonical_relationship_version
canonical_fact_evidence
canonical_fact_change

derivation
derivation_input

learning_candidate
learning_evidence
knowledge_gap
reasoning_pattern_candidate

conversation
conversation_turn
conversation_turn_citation
conversation_attachment
conversation_feedback
conversation_context
conversation_knowledge_artifact
conversation_hypothesis
conversation_derivation

entity_merge
entity_merge_history
conflict
review_item
review_batch
review_decision
review_decision_evidence

process_type
process_instance
process_state_definition
process_transition_definition
process_event
process_constraint
normative_constraint
hypothetical_scenario

decision
decision_input

embedding

audit_event
outbox_event
```

## AGE Graph Labels (master blueprint section 79)

Potential vertices:

```text
Entity
Document
Concept
Process
Decision
ConversationArtifact
```

Potential edges:

```text
RELATED_TO
CONTAINS
MENTIONS
SUBMITTED_BY
INSURED_BY
BROKERED_BY
HAS_COVERAGE
HAS_LOCATION
ARISES_UNDER
DERIVED_FROM
EVIDENCED_BY
SUPERSEDES
PART_OF
```

Graph labels are ontology-mapped semantic relationships.

## Content Storage Format (master blueprint section 80)

Recommended artifact set:

```text
manifest.json
docling-document.json
normalized.md
blocks.jsonl
tables.jsonl
layout.jsonl
```

Why:

```text
Markdown/text
    easy human + LLM consumption

JSONL
    streaming
    row-wise processing
    easy targeted reinterpretation

manifest JSON
    versions / hashes / parser metadata
```

Original source binary is retained separately through the provider-neutral `ContentArtifactStore` port. The initial
implementation is `LocalFilesystemObjectStore`, configured by committed `config/local.yaml` and writing runtime
bytes below the ignored `./content/` directory. PostgreSQL stores the authoritative artifact metadata and lifecycle
state; future S3, Azure Blob, GCS, or other adapters can satisfy the same storage port.

## Bounded v0.1B assessment records (F0065)

Master blueprint section 124 adds two proposed record types alongside the canonical kernel:

| Record | Purpose and authority boundary | Exact references |
|---|---|---|
| GuidelineRuleVersion | Reviewed immutable rule release, scoped by tenant/KB, policy/coverage, basis, currency, authority, effective interval, and release time | Rule/source/authority and ontology release |
| AssessmentRecord | Immutable on-demand evaluation at an explicit snapshot; outside canonical facts and separate from business approval | Subject, input fact versions, rule version, valid/known coordinates, comparison or gap/conflict context, evidence/derivation lineage, evaluator version, actor, and audit |

Current permissions govern both records and the complete relevant input/evidence lineage. Reassessment creates a new record; a saved historical result is not returned as a new current result. General dependency propagation remains F0056.

The [assessment contract](../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md) defines semantics and proof obligations. Runtime DTOs, OpenAPI bindings, and persistence migrations must be settled against the proven upstream kernel in the [assembly plan](../features/F0065-grounded-gl-guideline-assessment/feature-assembly-plan.md). The [synthetic records](../examples/neurosymbolic-gl/records.json) use an educational schema and must not be imported as authoritative production data.

## Example Manifest (master blueprint section 81)

Illustrative layout; the accepted wire shape is `planning-mds/schemas/content-artifact-manifest.schema.json`. The parser remains Docling under ADR-0060. F0004/F0016 must version any new pipeline/run metadata contract rather than add undeclared fields to the current strict schemas.

```json
{
  "document_id": "doc_123",
  "document_version_id": "docv_456",
  "source_hash": "...",
  "parser": {
    "name": "docling",
    "version": "...",
    "config_hash": "..."
  },
  "artifacts": {
    "native_document": "docling-document.json",
    "normalized_text": "normalized.md",
    "blocks": "blocks.jsonl",
    "tables": "tables.jsonl",
    "layout": "layout.jsonl"
  },
  "artifact_hash": "..."
}
```

## Planned pipeline and run metadata (ADR-0060)

Docling-Graph does not change source, content, and interpretation identity. F0004/F0016 must settle the following contract additions before implementation:

| Record | Required information and owner |
|---|---|
| Content artifact | Native document/schema hash, Docling parser version/configuration, producing pipeline revision, immutable bundle file hashes, and durable publication state — F0004/F0005 |
| Interpretation run | Artifact reference, selected block scope, profile/template/schema/prompt hashes, pipeline revision/configuration and chunking/extraction settings, model identity, attempts, status, token/cost counters — F0016 |
| Interpretation output manifest | Hashes and authorized store references for upstream graph, provenance ledger, effective configuration, and chunk/item-to-Nebula evidence mapping — F0016 |
| Document job | Tenant/KB-scoped idempotency key, lease/heartbeat, failure stage, parse checkpoint, cancellation, and retry state — F0005 |

The current manifest and InterpretationResult schemas reject undeclared fields. Version additions with compatible readers and retain old bundles; do not relabel F0001 files as new-pipeline outputs. Original graph IDs remain run-local. Nebula entity resolution, evidence bindings, and commit services remain authoritative; no graph export becomes a canonical database import.
