# F0012-S0001 — Validate foundation module authoring

**Story ID:** F0012-S0001
**Feature:** F0012 — Foundation ontology
**Title:** Validate foundation module authoring
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** domain steward (Sameer)
**I want** every ontology module file checked against one versioned authoring contract before it can be compiled
**So that** a term's meaning, semantics and constraints are explicit and reviewable, and nothing unsupported is silently approximated.

## Context & Background

Master blueprint §20 and §82 disagree on `parents:` versus `parent:`; §19 lists constructs without separating inference from validation; §112 requires each constraint's execution context. Operator decisions D3 and D8 (G1, 2026-11-25) settle the supported subset and the canonical field. ADR-0063 requires a definition, examples and regression cases per class and property; ADR-0064 requires `temporal_kind` per property.

## Acceptance Criteria

- [x] **AC1:** Given a module file that satisfies the authoring schema (module ID, version, dependencies, classes, object and datatype properties, labels, definitions, examples, regression cases, `temporal_kind` and constraints), validation reports zero errors and records the authoring-schema version it validated against.
- [x] **AC2:** `parents:` is the only parent field and accepts zero or more term IDs. A term using singular `parent:` is rejected with a stable error code naming the file, term and the replacement field `parents:`; no compiled output is produced.
- [x] **AC3:** Every class and property must have a non-empty definition, at least one example reference and at least one regression-case reference, and each reference must resolve to an existing file or case ID. Each missing or unresolved item produces its own error naming the term.
- [x] **AC4:** Labels use BCP 47 language tags. Each term has exactly one preferred `en-US` label and at most one preferred label per tag; aliases are listed separately. A missing `en-US` label, a duplicate preferred label in one tag or an invalid tag is rejected.
- [x] **AC5:** Every property declares `temporal_kind` as exactly one of `STATE`, `EVENT` or `ETERNAL`. A missing value or any other value is rejected.
- [x] **AC6:** Only `subClassOf`, `subPropertyOf` and `inverseOf` are accepted as inference rules, and only `domain`, `range`, `disjoint`, `minCardinality` and `maxCardinality` as validation constraints. `symmetric`, `transitive` or any other construct is rejected as unsupported with the construct name. A `domain` or `range` declaration never infers a type.
- [x] **AC7:** Every validation constraint declares lifecycle stage, consumer, applicability, severity/action and data basis (`asserted`, or `inferred` with the named ruleset). A missing field is rejected. Validation reports all errors in a deterministic order (file, path, code), exits non-zero on any error and writes no partial output.

## Edge Cases & Error Scenarios

A file with several errors lists every error, not only the first (AC7). An empty `parents: []` is valid and means a root term. A YAML parse failure is reported as one error naming the file and position, with no compiled output.

## Interaction Contract

Entry point: an offline validation command run on authored module files by a developer or CI. It reads files only and has no database effect. Success is exit 0 with a validation summary; failure is a non-zero exit with the complete error list. There is no editable state, save action or audit record.

## Data Requirements

Module and term IDs, version, dependency declarations, labels/aliases with language tags, definitions, example and regression references, property `temporal_kind`, cardinality and value type where a FactSlot is implied, and constraint execution context. Error codes and the authoring-schema format are designed in Phase B.

## Role-Based Visibility

No runtime principal is involved and no authorization decision is made; validation is offline and reads files only. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Deterministic output: the same files give the same error list and order on repeated runs. Zero network calls, database connections, parses or model calls. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

F0011 offline schema conventions for the authoring schema itself. S0002 adds identity checks to the same validation pass.

## Out of Scope

OWL constructs beyond the supported subset (F0030/F0062); OKF import/export; a workbench editor (F0030).

## Questions & Assumptions

No open business-rule question. Operator decisions D3 and D8 and PM assumption A3 (labels) are in the [PRD](PRD.md#risks--assumptions). The authoring-file syntax, error codes and schema location are Phase B decisions.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] Positive module fixture and one negative fixture per rejection rule, with expected error codes and order.
- [x] Error scenarios and determinism checks pass.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Feature run `2026-11-26-54387a08`: Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect signoffs are recorded in [STATUS.md](STATUS.md#story-signoff-provenance) and the run's signoff ledger.
