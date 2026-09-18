## Story Header

**Story ID:** F0005-S0003
**Feature:** F0005 — One-time document ingestion
**Title:** Reinterpret saved JSON and map evidence
**Priority:** High
**Phase:** v0.1A
**Status:** In Progress

## User Story

**As a** document intelligence engineer
**I want** new interpretations over saved native content with usable evidence
**So that** a profile change enriches knowledge without reparsing or inventing locations.

## Context & Background

Implements the [PRD](PRD.md) and [assembly plan](feature-assembly-plan.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). F0001 measured Docling plus a direct full-document vLLM request; it did not prove the Graph pipeline.

## Acceptance Criteria

Edge cases covered below include unresolved or multi-region evidence, synthesized/merged nodes, oversized prompts, and unsupported selected-block scope.

- **Given** each native/scanned bundle after worker restart, **when** two fixed profiles execute through the real Graph package, **then** pass saved DoclingDocument JSON, assert no physical conversion/OCR entry point is called, and preserve all content hashes while recording distinct run/configuration identities.
- **Given** Graph chunks, nodes, properties, and relationships, **when** the adapter creates InterpretationResult, **then** retain the full provenance ledger and stable original item/block mappings; graph IDs and local merges cannot become enterprise identity or canonical facts.
- **Given** limit amount, currency, basis, effective date, table headers, repeated values, or multi-region support, **when** evidence is resolved, **then** check every value against its actual source regions and declared precision, including Unicode offsets and geometry conventions; a node-identifier match cannot ground all its properties.
- **Given** source text does not support an exact binding, **when** an assertion candidate is produced, **then** keep coarse or unresolved evidence explicit and preserve ADR-0058 review behavior; synthesized or merged nodes do not gain stronger support.
- **Given** a selected block scope or an oversized request, **when** interpretation begins, **then** exclude unselected content, reject unsupported targeting, and enforce prompt/schema/input/output budgets before every call, including fill, repair, and reconciliation; F0032 later proves evolution scheduling.

- **Given** a job, artifact, run, or activation state changes, **when** the operation succeeds or fails, **then** append an audit event with actor/job identity, correlation and attempt IDs, relevant artifact/run references, outcome, and timestamp; omit secrets and source text.

## Data Requirements

Source/version and tenant/KB identity; native document/schema and file hashes; parser/conversion recipe separate from pipeline/template/model/run metadata; parse quality; declared evidence precision; attempts and outcomes. Preserve accepted six-file bundles and strict schema versioning.

## Role-Based Visibility

Only authorized principals/jobs can read source or run outputs. Model calls receive authorized content, never user credentials or authorization authority. Review and canonical acceptance remain engine responsibilities.

## Non-Functional Expectations

Enforce explicit concurrency/context budgets and durable job recovery. Keep source text and secrets out of routine logs; retain evidence outputs under tenant access and retention controls. Report costs and failures without claiming unmeasured quality.

## Dependencies

S0001/S0002; fixed proof profiles in this feature, with the production compiler and run services delivered by F0015/F0016; ADR-0040/ADR-0058.

## Out of Scope

Full profile workbench, enterprise entity resolution, canonical commits, AGE projection, and Temporal business workflows retain their owning features. This story cannot bypass those services.

## Questions & Assumptions

This story proves the adapter result contract and scoped capability. F0016 persists the full production run model; F0032 owns targeted evolution jobs. Evidence remains tied to the immutable original artifact.

## Definition of Done

- [ ] Acceptance and failure cases have observed evidence against the pinned package.
- [ ] Applicable runtime tests, authorization checks, and contract validation pass.
- [ ] STATUS, metadata, documentation, and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded; planning checks are not runtime proof.

## Review Provenance

Pending in [STATUS.md](STATUS.md). No implementation or lifecycle approval is claimed.
