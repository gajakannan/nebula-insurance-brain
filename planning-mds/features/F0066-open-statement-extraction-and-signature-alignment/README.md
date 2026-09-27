# F0066 — Open-statement extraction + signature alignment

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

Narrative sources (endorsement wording, broker correspondence, underwriting notes, inspection reports, conversation) are extracted as open statements in the source's own words, with no ontology in the prompt. A workbench-governed alignment step then turns those statements into typed assertions, deciding once per signature and never per document.

This feature was added by the 2026-09-25 amendment. [ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) is accepted as direction; its proof gates qualify this feature's implementation and per-profile activation. Related: [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) (admission and mood), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) (decision basis). Source: master blueprint sections 11, 29, and 99 (invariants 38–39). Examples: [EX-SEM-001/002 and EX-SEM-010](../../examples/statements-time-and-governance.md).

## Scope

- **Open extraction.** A compact contract per content block: entities with their kind words, named or described; statements that open with a verbatim quote and name both sides in words; the relation phrase as written; role-word qualifiers, including mood; time mentions; other names. Every output passes the ADR-0065 admission checks. Extraction uses temperature 0 and streams output, with truncation recorded.
- **Kind-word alignment.** Bind kind words to classes. Roles are not kinds.
- **Signature alignment.**
  - Candidates are admitted through the class hierarchy, with a shortlist when there are too many.
  - The aligner reads the source block.
  - Two votes, with candidates in opposite orders, must agree.
  - `NONE` and `UNDECIDED` are recorded, never skipped.
  - A person's binding is final.
  - Each decision stores its basis fingerprint.
- **Implication rules and phrase readings.** Rules are proposed by the aligner and approved by a person. Readings are cached per distinct phrase. Implied assertions are `INFERRED` and carry the rule version and evidence.
- **Materialization.** Idempotent set semantics through `typed_assertion_source`. A typed assertion retires when no source statement holds. Mood-bearing statements are never materialized.
- **Queue items.** `SIGNATURE_ALIGNMENT` and `IMPLICATION_RULE` items are delivered to F0043's queues.
- **Activation.** Per document profile section through `interpretation_route` (F0014), only after the parity gate passes for that profile.

## Out of scope

- Replacing template extraction for form-shaped sections.
- An ontology in any extraction prompt.
- Model-computed dates; ADR-0064 handles time.
- Automatic ontology changes; F0029/F0030 own ontology growth.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0066.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
