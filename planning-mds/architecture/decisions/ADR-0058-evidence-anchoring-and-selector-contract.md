# ADR-0058: Evidence Anchoring and Selector Contract

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-08
**Deciders:** Pending; becomes Accepted only when the stated proofs, owners, and release gates are satisfied (master blueprint section 106 decision posture)
**Settled by:** F0001-S0003 (evidence resolves) and F0001-S0004 (native review round trip); results recorded by F0001-S0007
**Source:** Master blueprint sections 108.2, 111, 125; prototype `planning-mds/examples/nebula-review-panel-live-files.html`

## Context

[ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md) moves the review surface into Nebula. That surface only works if an assertion's evidence can be re-anchored in the original bytes at review time, and if the system is honest when it cannot be. Section 108.2 already requires explicit evidence precision and a single character-offset convention; it does not yet say what an evidence locator looks like per format, or who resolves it.

Two different things were previously conflated as "the bounding box": what the extractor recorded, and what the reviewer's screen highlights. Interpretation runs happen once against Docling's normalized document; review happens later in a browser against the source file, possibly after a renderer upgrade. A locator that only holds coordinates cannot survive that gap, and a locator that silently resolves to the wrong region is worse than one that fails.

The prototype resolved this against real files in four formats. Its findings are the substance of this record: anchoring by quote works, multi-item unions handle simple PDF fragmentation, OOXML paths index real runs and real cell references, and the failures are visible rather than approximated.

## Proposed decision

**1. Locators are W3C Web Annotation selectors, with one local extension.** An evidence locator is a target with a `source` (the immutable Nebula artifact identity), an optional `part` (the OOXML part path), and a list of selectors that are redundant by design — a positional selector for speed and a textual selector for recovery.

| Content | Selectors |
|---|---|
| PDF | `FragmentSelector` conforming to `http://www.w3.org/TR/media-frags/` (page plus region as percent of the page box) and `TextQuoteSelector` (exact, prefix, suffix) |
| WordprocessingML | `RangeSelector` over `XPathSelector` start and end with character offsets, plus `TextQuoteSelector` and `TextPositionSelector` |
| SpreadsheetML | `nebula:TableCellSelector` (sheet, header row, column, row key, resolved cell reference) plus `XPathSelector` into the sheet part |
| Delimited and plain text | `TextPositionSelector` and `TextQuoteSelector` |

`nebula:TableCellSelector` is a declared local extension: the W3C model has no cell selector, and resolving a spreadsheet cell by position alone is not durable. The column resolves by header text and the row by a business key, so an inserted column or a reordered sheet does not silently move the anchor.

**2. Positions are Unicode code points.** Section 108.2 requires choosing one convention; this is the choice. JavaScript's UTF-16 code units are converted at the panel boundary, never stored.

**3. The spreadsheet header row is stored, never assumed.** Real statements of value carry banner rows, merged title cells, and second header blocks for another location group. The header row is resolved during ingestion and carried in the locator. A locator that assumed row 1 is a defect, not a fallback.

**4. Precision is declared, and `unresolved` is a first-class value.** Precision is one of `exact-span`, `table-cell`, `block`, `page`, `document`, or `unresolved`, extending section 108.2's list with the panel's behavior for each. The panel renders what the precision claims: a page-level ground shows a page-level mark and says so, and never a tight box the evidence does not support.

**5. Unresolved evidence blocks the decision instead of degrading it.** When a locator cannot be re-anchored, the reviewer cannot accept or correct the field on evidence they were not shown. The submitted record carries action `BLOCKED` with reason code `EVIDENCE_UNRESOLVED` and the resolver's explanation. `BLOCKED` is an operational outcome, not an adjudication: it produces no assertion, and the review item stays open. It is distinct from `REJECT`, which is a reviewer's judgment that the source does not support the value.

**6. Anchoring authority is server-side; the browser renders.** The stored locator is resolved against Docling's normalized text during interpretation. The panel's parsers exist to display the original bytes and to bind the highlight, not to define where the evidence is. Where the two disagree — PDF producers that emit text items out of reading order are the known case — Docling's normalized text is authoritative and the panel reports a resolution failure rather than moving the anchor.

**7. Corrections carry the locator forward.** A `CORRECT` decision creates an assertion with origin `HUMAN_REVIEW`, `corrected_from_assertion_id`, the evidence target the reviewer actually saw, and the precision at which they saw it (ADR-0037).

## Alternatives and consequences

- **Coordinates only.** Smaller records, and the standard approach. It breaks on re-render, cannot recover from a renderer upgrade, and gives nothing to verify an anchor against. Rejected: the quote selector is what makes failure detectable.
- **Quote selectors only.** Durable but ambiguous on repeated values and slow over large documents; no region to draw. Rejected as the sole selector, retained as the recovery path.
- **A Nebula-proprietary locator format.** Fewer constraints, no interoperability. Rejected: the W3C model already covers three of the four formats, and a local extension for the fourth is a smaller commitment than a bespoke model.
- Redundant selectors make evidence records larger and require every writer to populate all of them. The alternative is a locator that cannot be validated.
- Declaring `unresolved` will surface real anchoring failures as blocked review items rather than as silent misplacement. That is the intended trade; it will make the first corpus look worse and the system trustworthy.

## Proofs required

| Proof | Owner | Release gate | Recorded result |
|---|---|---|---|
| A locator round-trips through interpretation, storage, and the panel for each of the four formats | Document intelligence engineer | F0001-S0003 | Not executed |
| Quote recovery after a deliberate coordinate drift; the panel re-anchors from the quote | Frontend + QA | F0001-S0004 | Not executed |
| A page-level ground renders as page-level and never as a tight box | Frontend + QA | F0001-S0004 | Not executed |
| An unresolvable locator produces `BLOCKED` / `EVIDENCE_UNRESOLVED` and no assertion | Backend + QA | F0001-S0004 | Not executed |
| A statement of values with banner rows above the header resolves through the stored header row | Document intelligence engineer | F0001-S0003 | Not executed |
| Code-point offsets survive the UTF-16 boundary in both directions | Frontend + backend | F0001-S0004 | Not executed |
| A rotated or scanned page with no text layer declares its precision honestly | Document intelligence engineer | F0001-S0003 | Not executed |

## Consequences

- Until accepted, implementation treats master blueprint sections 108.2 and 125 as requirements to prove, not as settled contracts.
- Acceptance requires recording the executed proofs, the owner, and the release gate in this record (F0001-S0007).
- The `ReviewDecision` schema and the evidence portion of `InterpretationResult` are bound by this record; changing a selector shape is an ADR change, not a schema tweak.

## References

- Master blueprint sections 108.2 (evidence precision), 111, 125
- [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md), [ADR-0037](ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0040](ADR-0040-lossless-content-and-evidence-contract.md)
- Prototype: [`planning-mds/examples/nebula-review-panel-live-files.html`](../../examples/nebula-review-panel-live-files.html)
- W3C Web Annotation Data Model, Selectors and States: https://www.w3.org/TR/annotation-model/#selectors
- W3C Media Fragments URI 1.0: https://www.w3.org/TR/media-frags/
