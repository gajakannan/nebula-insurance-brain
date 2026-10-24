## Story Header

**Story ID:** F0005-S0005

**Feature:** F0005 — One-time document ingestion

**Title:** Qualify text origin and enable v2 publication

**Priority:** High

**Phase:** MVP — v0.1A

**Status:** Not Started

## User Story

**As a** document intelligence engineer

**I want** every published block to carry an observed text origin and exact OCR provenance before the v2 writer is switched on

**So that** downstream admission and review never rely on inferred origins or unidentified OCR models.

## Context & Background

F0004 delivered v2 content contracts, per-item origin projection, the `content.v2_writer_enabled` switch (default `false`) and the per-document v1 fallback, and its Step 1a spike passed on three synthetic fixtures. F0004 closeout assigned F0005 two obligations before broader activation: fixed Docling/hook qualification and exact OCR model-asset provenance. This story also satisfies the 2026-09-25 A-4 activation prerequisite under ADR-0065. See the [PRD](PRD.md).

## Acceptance Criteria

- [ ] **F0005-S0005-AC1:** Given every qualification-corpus document converted live, when per-item origin is projected, then each native text item is `STATED` with its observed producer, each OCR item is `OCR` with engine name/version, and items that cannot be attributed return `ORIGIN_UNAVAILABLE`; no origin is derived from page OCR counts.
- [ ] **F0005-S0005-AC2:** Given OCR ran, when the bundle is published, then the OCR model assets used are identified by name, revision and file SHA-256 read from the installed asset files; an unidentifiable asset blocks v2 publication for that document instead of recording a guessed identity.
- [ ] **F0005-S0005-AC3:** Given a document with any `ORIGIN_UNAVAILABLE` item and the v2 writer enabled, when it is published, then it falls back to a v1 bundle with `writer_fallback_reason=ORIGIN_UNAVAILABLE` audited, and the per-corpus fallback rate is reported.
- [ ] **F0005-S0005-AC4:** Given v2 bundles from the corpus, when every existing consumer reads them (authorized content reader, evidence resolver, Graph adapter saved-JSON path, importer, restore drill), then they pass with unchanged behavior; v1 bundles stay readable.
- [ ] **F0005-S0005-AC5:** Given AC1–AC4 pass and S0004 activation is accepted, when `content.v2_writer_enabled` is set to `true` in committed configuration, then new sources publish v2 bundles and existing artifacts are not rewritten.
- [ ] **F0005-S0005-AC6:** Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

**Edge Cases & Error Scenarios:** OCR assets present but altered after install → digest mismatch blocks v2 publication. Mixed page with an image region OCR skipped → that region's items `ORIGIN_UNAVAILABLE`, document falls back to v1. Docling upgrade → origin hook re-qualified before the switch stays on.

## Interaction Contract

No UI. Entry points: the publication boundary and the committed `config/local.yaml` switch.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Publication boundary with v2 writer | Publish a converted document | New bundle only | v2 bundle with per-item origins and OCR asset identity, or audited v1 fallback | Reload through the v2 verifier; check manifest version, origins and asset digests | ServicePrincipal `ingest`; switch flipped only after S0004 acceptance |

**Validation and audit:** the switch change is recorded with the activation decision; fallbacks are audited per document.

## Data Requirements

Per-item origin and producer, OCR engine name/version, OCR asset name/revision/SHA-256, fallback reason and rate, manifest contract version.

## Role-Based Visibility

Unchanged from F0004: origin metadata follows artifact access.

## Non-Functional Expectations

Origin projection adds no model call and no second conversion.

## Dependencies

F0004 v2 contracts, projection and fallback; S0001 live conversion; S0004 activation decision; ADR-0065 (Proposed; only its storage carry-in applies).

## Out of Scope

`TRANSCRIBED` and `DESCRIBED` producers, new OCR engines, rewriting legacy bundles, assertion admission behavior (F0006).

## Questions & Assumptions

The v2 switch flips only together with S0004 activation; on rejection it stays `false`.

## Definition of Done

- [ ] Every acceptance criterion has observed evidence on live conversions.
- [ ] Applicable runtime tests, authorization checks and contract validation pass.
- [ ] STATUS, compatibility evidence and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded in STATUS; planning checks are not runtime proof.

## Review Provenance

Implementation signoff belongs in [STATUS.md](STATUS.md). This planning update is not runtime completion or reviewer approval.
