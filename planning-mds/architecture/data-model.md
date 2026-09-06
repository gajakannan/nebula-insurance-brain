# Data Model — Nebula Insurance Brain

**Status:** Baseline (extracted from the master blueprint on 2026-09-05); refined per feature in Phase B.

PostgreSQL is the authoritative runtime store (ADR-0002). Graph and vector stores are projections (ADR-0022, ADR-0023). Semantics of the tables below are defined in the master blueprint: canonical world model (section 12), FactSlot (section 13), bitemporal facts (sections 14 to 16), provenance (section 17), content versus evidence identity (section 18), and flexible schema representation (section 20). Every authoritative row carries `tenant_id` and `knowledge_base_id` (ADR-0030) and audit fields (`created_at`, `recorded_at`, actor).

The sections below are reproduced verbatim from the master blueprint so implementers have one file to read; when they diverge, the master blueprint plus accepted ADRs win until this document is promoted by a Phase B decision.

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
review_external_task
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

Original source binary is retained separately.

## Example Manifest (master blueprint section 81)

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
    "normalized_text": "normalized.md",
    "blocks": "blocks.jsonl",
    "tables": "tables.jsonl",
    "layout": "layout.jsonl"
  },
  "artifact_hash": "..."
}
```
