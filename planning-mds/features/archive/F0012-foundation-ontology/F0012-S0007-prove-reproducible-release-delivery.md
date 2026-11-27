# F0012-S0007 — Prove reproducible release delivery

**Story ID:** F0012-S0007
**Feature:** F0012 — Foundation ontology
**Title:** Prove reproducible release delivery
**Priority:** High
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** persistence engineer (Ingrid)
**I want** recorded evidence that the release contract is reproducible, interchangeable and compatible with the shipped kernel
**So that** ADR-0045 and ADR-0070 can be judged on executed results and downstream features can rely on the foundation release.

## Context & Background

ADR-0045 lists acceptance evidence that must be executed with recorded commands and results; F0012 owns the identity/locks, inference-change, constraint-change, split/rollback and scope cases. ADR-0012 keeps RDF/OWL and JSON-LD as interchange formats. F0011 supplies the offline contract pipeline. The migration must preserve all F0007–F0009 data.

## Acceptance Criteria

- [x] **AC1:** The F0012-owned ADR-0045 cases (identity and locks, inference change, constraint change, split and rollback, scope) each run with recorded commands, inputs, outputs and exit codes in the feature run evidence. The missing-limit case is recorded as owned by F0013/F0065.
- [x] **AC2:** The compiler exports each release as RDF/OWL Turtle and JSON-LD; the two graphs are isomorphic (a non-isomorphic pair is rejected by the gate), the declared inference rules produce the expected entailments on the foundation fixtures, and the `semantic_rdf` gate passes with `--require` in CI.
- [x] **AC3:** Every new payload schema (for example the release manifest and impact report) is delivered through the F0011 offline contract pipeline and passes the shared Python/AJV conformance suite.
- [x] **AC4:** The migration applies on a database holding F0007–F0009 data without altering existing data or audit rows, the full existing engine test suite passes unchanged, and downgrade behavior after release rows exist follows the Phase B rule (refuse or proven safe), with the result recorded.
- [x] **AC5:** Changed executable code reaches at least 80% coverage; compile, install, report and activation runs record zero Docling parses and zero model calls.
- [x] **AC6:** Each new or changed concept has a glossary entry, a worked example, a boundary case and owning feature/story links in `planning-mds/examples/README.md`. ADR-0045 and ADR-0070 record the evidence produced; their status is not changed by this feature.

## Edge Cases & Error Scenarios

A non-isomorphic export fails the story even if both files parse (AC2). A conformance mismatch between Python and AJV for any example fails AC3. A downgrade attempted after install that would lose release rows must be refused, not partially applied.

## Interaction Contract

N/A — verification story. Entry points are the existing CI gates, migration commands and test suites; completion is recorded evidence. No editable state or save action is introduced.

## Data Requirements

Recorded commands/results, RDF and JSON-LD exports, conformance results, migration logs, coverage report, example registrations. Evidence locations follow the feature-run evidence contract.

## Role-Based Visibility

No runtime role, permission or authorization change. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

All checks are deterministic and repeatable from a fresh clone with the documented commands. At least 80% changed executable-code coverage.

## Dependencies

S0001–S0006; F0011 contract pipeline; existing `semantic_examples` and `semantic_rdf` gates; PostgreSQL integration fixtures.

## Out of Scope

Formal acceptance of ADR-0045 or ADR-0070 (separate operator decision); production rollout; F0013 GL release evidence.

## Questions & Assumptions

No open business-rule question. The downgrade rule and contract inventory are Phase B decisions.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] ADR-0045 case log, RDF isomorphism and entailment output, conformance results, migration and full-suite logs, coverage report.
- [x] Error scenarios and persistence expectations pass.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Feature run `2026-11-26-54387a08`: Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect signoffs are recorded in [STATUS.md](STATUS.md#story-signoff-provenance) and the run's signoff ledger.
