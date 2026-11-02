# Retain open statements and version contracts

**Story ID:** F0006-S0002
**Feature:** F0006 — Assertion plane + origin + interpretation basis
**Title:** Retain open statements and version contracts
**Priority:** High
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Mateo the Document Intelligence Engineer
**I want** source wording to remain representable alongside typed claims
**So that** a later ontology decision can use the retained wording without rereading the physical document.

## Context & Background

ADR-0063 is accepted direction. The README's 2026-09-25 amendment admits storage and contracts in F0006, while F0066 owns live open extraction and alignment. The existing result schema rejects unknown properties.

## Acceptance Criteria

- [ ] **AC1:** An authorized fixture/service caller can persist and reload `OPEN_STATEMENT` with subject, source relation phrase, object reference or literal, role-word qualifiers, time-mention references, mandatory quote and source/evidence identity unchanged.
- [ ] **AC2:** An open statement has a null predicate and `EXPLICIT` basis; a non-null predicate, missing quote, invalid subject or incompatible basis is rejected with no assertion write.
- [ ] **AC3:** A typed assertion requires an ontology property and release; an open statement requires neither an invented property nor a release. Both kinds retain mode, origin and evidence independently.
- [ ] **AC4:** The versioned schema addition represents assertion kind, source phrase, quote/server selector, role qualifiers including mood and time-mention references. Existing valid result fixtures still validate against the unchanged legacy version and remain readable.
- [ ] **AC5:** New-version payloads cannot silently lose semantics through old readers; unsupported versions/kinds produce an explicit compatibility error before mutation. No fabricated quote or ontology release is backfilled into legacy results.
- [ ] **AC6:** New open statements remain ineligible for entity resolution, FactSlot selection and canonical commit. A fixture can store one without invoking a model, alignment or conversion.
- [ ] **AC7:** Unauthorized or cross-tenant/KB source, object or time-mention references are denied without content disclosure; existing authorization audit is retained. Dangling local references are rejected; document-local descriptive entities remain local rather than being silently merged. Accepted writes retain actor and source/run identity for audit.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Authorized versioned claim service / fixture harness | Submit open candidate | New candidate only | Append grounded open record or reject | Fresh scoped query retains quote, qualifiers and null predicate | Existing granted service principal; fixture support does not enable a live producer |

Malformed or unsupported inputs produce explicit errors and no partial claim. Keep existing authorization/import audit; runtime audit details are set in Phase B. Schema validation alone cannot establish storage delivery.

## Data Requirements

PRD kind-specific fields; role words and quote are source text, not invented ontology vocabulary. Time-mention references carry no time-resolution execution.

## Role-Based Visibility

F0002 principal/scope restrictions apply to payloads, statements, evidence and errors. No new role or grant.

## Non-Functional Expectations

Legacy fixture compatibility, lossless reload and zero physical reparse. Compatibility must reject unsupported semantics before writing.

## Dependencies

S0001 supplies durable claim dimensions; F0004 evidence; F0002 authorization. F0016 will produce time mentions; F0066 will produce/align open statements. Their runtimes are not prerequisites for this bounded storage contract.

## Out of Scope

Live open extraction, signature binding, implication rules, materialization, time resolution and enabling a new writer default.

## Questions & Assumptions

No open business question. Architect chooses schema version identity, dispatch, migration and compatible-reader mechanics without widening the legacy strict contract.

## Definition of Done

- [ ] Seven ACs pass with old/new payload and PostgreSQL fixtures.
- [ ] Unsupported-version and ownership errors are observed; no silent field loss.
- [ ] Contract documentation, semantic examples and feature signoff provenance align.
