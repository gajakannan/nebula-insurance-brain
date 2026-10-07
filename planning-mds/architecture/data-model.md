# Data Model — Nebula Insurance Brain

**Status:** Baseline (extracted from the master blueprint on 2026-09-05); refined per feature in Phase B.

PostgreSQL is the authoritative runtime store (ADR-0002). Graph and vector stores are projections (ADR-0022, ADR-0023). Semantics of the tables below are defined in the master blueprint: canonical world model (section 12), FactSlot (section 13), bitemporal facts (sections 14 to 16), provenance (section 17), content versus evidence identity (section 18), and flexible schema representation (section 20). Every authoritative row carries `tenant_id` and `knowledge_base_id` (ADR-0030) and audit fields (`created_at`, `recorded_at`, actor).

The baseline sections below are reproduced from the master blueprint so implementers have one file to read; when they diverge, the master blueprint plus accepted ADRs win until this document is promoted by a Phase B decision. The ontology release and F0065 additions below are explicitly proposed contracts rather than existing runtime schema.

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
ontology_release                proposed composed release (ADR-0045)
ontology_release_module         proposed exact module-version membership (ADR-0045)
ontology_concept
ontology_property
ontology_relation
ontology_axiom
ontology_label
ontology_alias

extraction_profile
extraction_profile_module
semantic_interpretation_run

assertion                       assertion_kind: OPEN_STATEMENT | TYPED_ASSERTION (ADR-0063)
assertion_value
assertion_relationship
assertion_evidence
assertion_qualifier             role-word qualifiers on open statements; includes mood (ADR-0065)
typed_assertion_source          open statements behind a materialized typed assertion (ADR-0063)
time_mention                    verbatim time expression, interpretation, computed interval, grade (ADR-0064)
document_time_context           per document version and run (ADR-0064)
interpretation_drop             refused / truncated / uninterpreted items with reason (ADR-0065)

kind_word_binding               (ADR-0063, F0066)
signature_binding               with decision basis (ADR-0063, ADR-0068)
implication_rule
implication_rule_version
phrase_reading

entity
entity_type
entity_alias                    search projection over name facts (ADR-0066)

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

automated_decision              action, confidence, precedents, trace, undo, status (ADR-0067)
automation_fuse                 per KB and automation type (ADR-0067)
action_definition               revisioned (ADR-0069)
action_attempt                  request identity, dispatch token, state (ADR-0069)

embedding

audit_event
outbox_event
```

## Proposed ontology release records (F0012/F0013, ADR-0045)

An authored module version and a composed release have different identities. A release fixes the complete set of module versions used together. F0012/F0013 Phase B must settle the following logical records and ownership constraints under [ADR-0045](decisions/ADR-0045-ontology-release-compatibility.md), which remains Proposed. These are planning targets, not persistence migrations.

| Record | Proposed contract |
|---|---|
| `ontology_module` | Stable module identity and namespace; labels are separate from immutable term identities. |
| `ontology_version` | Immutable revision of one module, with its module reference, version, content digest, authoring-schema version, supported semantics, constraints and dependency declarations. F0012 must make this module-version role explicit in its schema. |
| `ontology_release` | Immutable composed release ID, ownership scope, manifest/dependency-lock digest, references and hashes for ontology and associated profile/template/compiler/validation/projection-mapping artifacts, and creation actor/time. Retain the compatibility report and migration mappings for each reviewed predecessor-to-candidate comparison. |
| `ontology_release_module` | Exact release-to-module-version membership; one selected version per module per release. Every declared dependency resolves to a member at an exact version and digest. No runtime resolution of a floating `latest` reference. |

Semantic content retains tenant/KB ownership and audit requirements under ADR-0002/ADR-0030, subject to the identity-control exceptions in ADR-0061. Shared vocabulary distribution must not bypass scoped release installation or tenant-extension isolation; F0012 Phase B settles those references. Content hashes establish artifact identity, not authorization or semantic compatibility.

Interpretation runs pin the composed ontology release and exact profile/template/compiler versions. Typed assertions and canonical fact versions retain their producing interpretation/release context; rule versions, derived results, and saved assessments retain the exact releases and inputs used. Do not resolve historical records through the currently active release. Activation and rollback are separately audited selections for future processing; neither edits published release contents nor rewrites earlier facts or assessments.

Term IRIs identify concepts across releases, while the release identifies their definitions at a specific revision. Pair stable IRIs with explicit semantic-change, split, merge, retirement, and migration records. Worked and boundary examples: [ontology release contracts](../examples/ontology-release-contracts.md).

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
HAS_LIMIT
HAS_FORM
HAS_TRIGGER
HAS_LOCATION
ARISES_UNDER
DERIVED_FROM
EVIDENCED_BY
SUPERSEDES
PART_OF
```

Graph labels are ontology-mapped semantic relationships.

The following proposed GL mapping makes that phrase concrete. F0012/F0013 and the projection consumer must freeze a mapping version in the release manifest before computing projection impact; these are planning labels, not claims that AGE edges exist today.

| Ontology relation ID | Blueprint shorthand | Proposed AGE label | Direction |
|---|---|---|---|
| `insurance.coverage.has-limit` | `hasLimit` | `HAS_LIMIT` | coverage → limit |
| `insurance.coverage.has-form` | `hasForm` | `HAS_FORM` | coverage → form |
| `insurance.coverage.has-trigger` | `hasTrigger` | `HAS_TRIGGER` | coverage → trigger |

Each mapping records the predicate IRI, source/target type and identity rules, projected qualifiers, and mapping version/digest. It specifies how each projected record retains exact source fact/relationship versions and evidence references, tenant/KB scope, valid/recorded context and asserted/derived basis. Those per-record values belong to the projection's lineage context, not the immutable mapping definition. Scalar properties and inverse predicates explicitly declare their projection or omission. A flat edge must not erase conflicts, time, qualifiers, provenance or ownership. Changes to labels/direction/payload require declared rebuild/invalidation behavior in the release impact report; unknown mappings cannot be reported as unaffected. The [interchange manifest](../examples/ontology-interchange/ontology.yaml) shows a small proposed mapping, with synthetic evidence context in [expected results](../examples/ontology-interchange/expected-results.yaml).

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

## F0002 proposed structural ownership and AuthX substrate

The [feature ERD](../features/archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/README.md#feature-erd--proposed-ownership-and-security-substrate) and [assembly plan](../features/archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md#step-1--ownership-identity-substrate-and-migration-s0001) define the exact proposed registries, ownership constraints and backfill. ADR-0061 clarifies that tenant/entity identity and global principal control records do not acquire a fabricated KB owner; authoritative semantic content remains KB-owned. Tenant entity associations do not grant access. Existing IDs and audit history survive migration.

New structural tables: tenant, workspace, knowledge_base, entity_identity, entity_knowledge_base, external_identity, principal_authority, resource_access and delegation. Existing membership gains current validity/restrictions; append-only audit supports the v1 decision payload. Source/content/assertion/review/fact/job descendants gain explicit composite ownership constraints. These are proposed migration targets, not claims about the current schema.

## Statements, time, and governance additions (ADR-0063 to ADR-0069)

These are proposed contract additions, not claims about the current schema. The feature named for each record settles its columns in Phase B.

| Record | Required information | Owner |
|---|---|---|
| Assertion (kind) | `assertion_kind`; for open statements: nullable `predicate_id`, source relation phrase, subject/object references or literal, mandatory quote with server-computed selector; typed assertions carry the ontology release | F0006 |
| Assertion qualifier | Role word as written, value or entity reference; `mood` holds the passage's own words | F0006 |
| Typed assertion source | Typed assertion ↔ open statement(s), with binding or implication-rule version; retirement when no source holds | F0066 |
| Time mention | Text, block, offsets, run, shape/reference/anchor/offset/granularity, computed interval, resolution grade, assertions dated | F0016 |
| Document time context | Document date and its source (`CONTENT`, `SOURCE_METADATA`, `HUMAN`), defined periods and calendars, anchors, time-of-day/time-zone convention | F0004/F0016 |
| Canonical fact version (time) | Per-bound granularity; `valid_to_state` (`OPEN`, `BOUNDED`, `UNKNOWN`); `attested_from`, `attested_to` | F0008 |
| Content block (origin) | `text_origin`, producing engine/model/version, origin-specific anchor; no mixed origins | F0004 |
| Interpretation drop | Run, block, reason code, model/prompt identity, raw-item hash, access-controlled excerpt | F0016 |
| Signature binding | Signature (phrase, subject classes, object classes or VALUE), property, direction or `NONE`/`UNDECIDED` with reason, ontology release, basis hash, decider, confidence | F0066 |
| Implication rule / phrase reading | Signature or kind-word key, concluded property, object source, version; reading cached per distinct phrase including "no answer" | F0066 |
| Name facts | `hasLegalName`, `hasTradeName`, `hasFormerName`, `knownAs` FactSlots; `entity_alias` becomes a projection | F0007/F0013/F0017 |
| Automated decision | Target, action, confidence, model sentence, precedents shown, trace, undo data, status; impact-hold reason | F0027/F0043 |
| Decision basis | `basis_hash` on interpretation runs, bindings, resolution verdicts, derived facts/assessments, impact analyses | F0016/F0027/F0032/F0056/F0065/F0066 |
| Action attempt | Execution request id (unique `NULLS NOT DISTINCT` with action and scope), definition revision, dispatch token, state, response capture, timestamps, safe request snapshot | F0050/F0059 |
