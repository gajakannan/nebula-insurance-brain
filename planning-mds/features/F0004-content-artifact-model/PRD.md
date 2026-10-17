# F0004 — Content artifact model — PRD

## Feature Header

**Feature ID:** F0004\
**Feature Name:** Content artifact model\
**Priority:** Critical\
**Phase:** MVP — v0.1A\
**Status:** Requirements approved by operator “proceed with Phase B” in plan run `2026-10-15-bbd8df01`. Implementation not started.

## Feature Statement

**As a** document intelligence engineer\
**I want** an immutable, attributable content artifact that downstream consumers can read after restart\
**So that** new interpretations reuse the same evidence without parsing the source again or silently changing its meaning.

## Business Objective

Make the accepted F0001 content contract an explicit, versioned product boundary for F0005 ingestion, F0016 interpretation, and F0022 evidence review. Preserve original source bytes, native DoclingDocument, normalized views, and their provenance independently of extraction results. Extend that boundary only with the document-date and text-origin storage amendments already authorized in BLUEPRINT §4.11.

## Problem Statement

The reserved feature has no approved requirements package. F0001 established a six-file parse bundle and F0005 exercised a separate Docling-Graph candidate. Neither proof alone defines the complete F0004 contract for content structure, document-date provenance, text origins, legacy compatibility, and consumer access. Without that contract, an extraction retry can mutate evidence, an upload timestamp can be mistaken for a document date, and generated descriptions can be mistaken for source text.

## Scope & Boundaries

**In Scope — all Must for this MVP:**

1. Separate source-document version, content-artifact version, and interpretation-run identities; preserve original bytes and source ownership.
2. Preserve the six required files: `docling-document.json`, `normalized.md`, `blocks.jsonl`, `tables.jsonl`, `layout.jsonl`, and `manifest.json`. Retain any assets required to read the native export; original source bytes are retained separately from the six-file parse set.
3. Record content contract/native schema versions, source and file hashes, parser/configuration identity, quality status, failed pages and warnings. Keep pipeline/extraction configuration and outputs attributable to their interpretation run.
4. Preserve block, table, cell, reading-order, page, and coordinate relationships actually supplied by the source/parser. Declare unavailable precision; do not invent locators.
5. Store each block's `text_origin` (`STATED`, `OCR`, `TRANSCRIBED`, `DESCRIBED`), producer identity/version and origin-specific anchor. A block cannot mix origins.
6. Store the document's own date with `CONTENT`, `SOURCE_METADATA`, or `HUMAN` provenance, or retain its absence. Preserve prior values and the basis of a correction without rewriting a published bundle.
7. Publish only verified bundles through ContentArtifactStore, protect metadata and byte access with existing F0002 authorization, and prove persisted reuse, compatibility, and restoration.

**Out of Scope:**

- New upload screens, Document 360, reviewer edit controls, or a new public document-management API; F0021/F0022 own those surfaces.
- F0005 job orchestration, leases, retries, model qualification, throughput tuning, or production activation of Docling-Graph. F0004 defines the artifact boundary those jobs consume.
- F0015 production profile compilation, F0016 full interpretation-run/time-context services, and F0032 scheduling.
- New OCR/transcription/description engines or new input-format onboarding. Native and scanned PDF remain the acceptance corpus established by F0001/F0005; other origins are storage/validation contracts with synthetic examples.
- The full W3C/OOXML locator expansion deferred by amended ADR-0058, frontend UTF-16 conversion, or claiming those proofs are complete.
- Assertion admission, mood routing, described-only evidence adjudication, entity resolution, canonical fact acceptance, bitemporal mutation, or time-mention resolution replacing template fields.
- Cloud storage adapters, distributed storage guarantees, new retention periods, legal-hold policy, automated deletion, or corpus-wide parser migration. Preserve existing restrictions and the restore unit; F0026 owns broader operational qualification.

## Acceptance Criteria Overview

| Requirement | Observable acceptance | Story |
|---|---|---|
| R1 — Identity and immutable bundle | The native export, normalized views, source reference, version metadata and hashes survive publication and restart; tampered/incomplete content is never returned as a verified artifact. | S0001 |
| R2 — Structure and origin | Every persisted block has one supported origin and attributable producer; real page/table relations and coordinate conventions survive round-trip; unsupported precision is explicit. | S0002 |
| R3 — Document date provenance | All three authorized source kinds round-trip; undated stays undated; receipt/upload timestamps never fill document date; a correction retains its earlier basis. | S0003 |
| R4 — Consumer safety and continuity | Authorized consumers reuse verified bytes, denied scopes receive no bytes, old bundles stay unchanged, and restore returns the same identities/hashes and restrictions. | S0004 |

All acceptance criteria in [the checklist](acceptance-criteria-checklist.md) are required implementation outcomes. They are unchecked until runtime evidence exists.

## UX / Screens

**Key workflows:** authorized ingestion handoff → validate/publish → authorized reload; content metadata lookup → original block/table/region; document-date provenance supplied by a trusted caller → retained record → reload; existing artifact → new interpretation → unchanged artifact plus separate run outputs.

System entry points are the existing ingestion publication boundary and authorized artifact/evidence services. Phase B must map each requirement to concrete interfaces and failure responses. F0004 supplies metadata that F0022 can display; it does not deliver those screens or a reviewer action.

## Screen Layouts (ASCII)

No UI — this feature defines persisted content and service contracts. There is no new or materially modified screen, so desktop and narrow layouts are not applicable. Existing review behavior must remain compatible.

## Data Requirements

**Core entities and relationships:** a source document has immutable document versions; a content-artifact version refers to exactly one source version and owner scope; blocks/tables/layout records refer to that artifact; interpretation runs refer to the accepted artifact without becoming part of its immutable parse payload. PostgreSQL holds authoritative metadata and ownership; bytes stay behind ADR-0059 storage ports.

**Required information:** artifact/source identity and hashes; tenant and knowledge-base ownership; parser name/version/configuration identity; content/native schema version; file inventory and checksums; publication/quality status with failed pages and warnings; stable artifact-local block/table references; page numbering, coordinate origin/units/dimensions/transform and Unicode code-point offset convention where applicable; one text origin and producer per block; document date with source/basis when present; audit actor and recorded timestamps.

**Validation rules:** reject unknown contract versions without guessing; distinguish an empty valid table set from failed extraction; reject dangling or cross-owner references, mixed-origin blocks, inconsistent hashes and invalid anchors. Preserve missing values as missing. An absent model for a non-model producer is explicit, never an invented model/version. New requirements must not retroactively relabel old content with unsupported origins or dates.

Document-date provenance is metadata about the source, not a canonical effective date. Conflicting candidate dates must remain distinguishable; F0004 does not choose a business precedence rule or run calendar arithmetic. A human-sourced value needs an attributable authorized human decision, not merely a caller-supplied `HUMAN` string. The storage boundary can accept that decision reference; the interactive authoring workflow remains F0022.

## Role-Based Access

Reuse verified F0002 principals, current membership and resource restrictions. An ingestion ServicePrincipal may publish only within its effective scope; no new grant is implied. TenantMember and Reviewer reads require the existing applicable artifact/evidence permissions and parent restrictions. Reviewer status grants neither universal document editing nor canonical acceptance. Every authorization decision retains its audit identity and policy version. Recheck current access on source bytes, artifact metadata, native/normalized files, and referenced run outputs; historical ownership is not a grant.

## Success Criteria

- All four stories pass with persisted readback, negative cases and actual evidence; documentation alone cannot satisfy them.
- After restart, two profile interpretations consume one saved artifact with zero converter/OCR entry-point calls and unchanged original/bundle hashes. This reuses the existing F0005 proof seam and is a consumer compatibility test, not production activation.
- Corruption, incomplete publication, unsupported versions, invalid origin/date metadata and unauthorized access produce explicit failures with no false ready/completed result.
- New-contract records pass their versioned validators; supported legacy bundles remain readable under their original contract and are never rewritten to manufacture provenance.
- The feature action records at least 80% coverage for changed runtime scope plus the required integration/security cases. Latency and throughput budgets belong to F0005/F0026; this feature makes no unmeasured performance promise.

## Risks & Assumptions

**Source authority:** ADR-0003/0004/0040/0059 are accepted. ADR-0058 is accepted as amended for the bounded PDF/BoxSelector contract. ADR-0060/0064/0065 remain Proposed; their feature README amendments authorize only the bounded carry-ins above. Planning approval does not accept those broader ADRs.

**Compatibility risk:** additional required fields can break strict old readers. Phase B must choose versioned schemas/readers and an explicit legacy path before approval. Missing historical origin/date evidence must remain missing.

**Publication risk:** object bytes and database readiness have separate failure points. Phase B must reconcile manifest-last publication, ownership, integrity checks, idempotency and restoration with the existing stores and F0003 persistence contract.

**Date/origin risk:** no reliable date or origin may be available for a legacy artifact. Absence is not permission to use receipt time or to label generated text as stated text.

No unresolved business question blocks this draft: the existing blueprint and amendments supply the scope. Physical schema shapes, supported-version matrix, service entry points, missing-anchor representation, and error contracts are Phase B design work, not permission to weaken these requirements.

## Dependencies

| Feature | Relationship / boundary |
|---|---|
| F0001 (archived) | Accepted native bundle, parse reuse, PDF evidence and local storage baseline. |
| F0002 (archived) | Verified principals, immutable ownership and current resource authorization. |
| F0003 (archived) | PostgreSQL metadata/reference integrity and migration/restore discipline; F0004 owns content-specific extensions. |
| F0005 | Downstream ingestion consumer and existing opt-in compatibility proof. Production qualification remains pending; F0004 must not depend on its production activation. |
| F0006/F0009/F0016/F0022 | Downstream origin, provenance, interpretation, and display consumers; their implementation is not a prerequisite to storage contracts. |
| F0026 | Broader operational/holdout qualification, not a substitute for F0004 integrity and authorization tests. |

Approved dependency manifest references and pending downstream audits are recorded in this run's [artifact trace](../../operations/evidence/runs/2026-10-15-bbd8df01/artifact-trace.md).

## Related Stories

- [S0001 — Publish and reuse an immutable content bundle](F0004-S0001-publish-and-reuse-content-bundle.md)
- [S0002 — Preserve content structure and text origin](F0004-S0002-content-structure-and-text-origin.md)
- [S0003 — Preserve document-date provenance](F0004-S0003-document-date-provenance.md)
- [S0004 — Protect artifact consumers and compatibility](F0004-S0004-authorized-consumers-and-compatibility.md)

## Example Library

[Worked examples](worked-examples.md) specialize the continuing EX-GL-001 case and EX-SEM-003/006. They are synthetic, illustrative planning expectations; no F0004 runtime result is claimed. Definitions come from the [glossary](../../domain/glossary.md) and [master blueprint §§5–6, 80–81, 108](../../architecture/master-blueprint.md). The architect must bind these cases to versioned contracts in Phase B; implementation must supply reproduction evidence outside the frozen holdout.
