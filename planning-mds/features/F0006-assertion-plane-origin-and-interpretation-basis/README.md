# F0006 — Assertion plane + origin + interpretation basis

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The assertion plane records what sources claim before anything becomes truth; origin and interpretation basis are first-class from the first extraction (section 11).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0005](../../architecture/decisions/ADR-0005-three-plane-knowledge-model.md), [ADR-0035](../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0006.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Persist both assertion kinds: `OPEN_STATEMENT` (subject, source relation phrase, object or literal, role-word qualifiers, time-mention references, mandatory quote, nullable predicate) and `TYPED_ASSERTION` (ontology property and release). v0.1 acceptance runs on the template route; open extraction and alignment ship in F0066 (ADR-0063).
- Define the admission service contract: quote-in-block, name-in-quote, time-words-in-quote, and name-claimed-by-another checks; server-computed selectors; drop reasons (ADR-0065).
- Add the `mood` qualifier. Mood-bearing statements are never eligible for canonical facts; an issued policy's operative provisions remain contract facts (ADR-0065, EX-SEM-007).
