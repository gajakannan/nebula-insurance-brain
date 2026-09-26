# ADR-0065: Assertion Admission, Text Origin, and Statement Mood

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0010](ADR-0010-provenance-is-mandatory.md), [ADR-0040](ADR-0040-lossless-content-and-evidence-contract.md), [ADR-0058](ADR-0058-evidence-anchoring-and-selector-contract.md) (anchoring is checked when an assertion is admitted, as well as when it is rendered), and [ADR-0027](ADR-0027-normative-and-hypothetical-semantics-are-not-fact-modes.md) (mood routes extracted conditions to normative structures)
**Source:** Master blueprint sections 11, 17, 57, 107.4, 108.2, 110.4. Informed by Utopia decisions 0001, 0040, and 0041, #745, and the extraction design (see References).

## Context

ADR-0058 defines how evidence resolves for rendering, and section 108.2 requires declared precision. Neither says what the Brain refuses when a model returns a claim. Three gaps remain.

1. **Nothing verifies model evidence.** A model can return a quote that is not in the block, a name that is not in its quote, or offsets that point elsewhere. If the pipeline trusts the offsets, the review panel highlights the wrong region. If it drops the item without a record, a run reported as complete hides a gap. That conflicts with section 107.4's `NOT_PROCESSED` versus `NOT_FOUND`.
2. **Nothing records how a block's words were obtained.** A block's words may come from a native text layer, OCR, audio transcription, or a model's description of a figure. Docling produces all four. A chart description that misreads a figure should not be able to supersede a correct limit read from the declarations page.
3. **Nothing marks mood.** Insurance text is full of claims that are not claims about how things are:
   - "Binding is subject to receipt of a signed application."
   - "The insured must maintain automatic sprinklers."
   - "Quoted limit: $2,000,000."
   - "Coverage will be extended upon inspection."

   Recorded as plain assertions, these become false facts: that the application was received, that sprinklers are maintained, that the limit is $2M.

## Proposed Decision

### 1. The server checks structure, never vocabulary

An admission service runs on every interpretation output (both routes of ADR-0063) before any assertion is persisted.

| Check | Failure reason |
|---|---|
| The quote occurs in the claimed block's text, after documented normalization (Unicode NFC, collapsed whitespace, hyphenation joins) | `QUOTE_NOT_IN_SOURCE` |
| Each entity name occurs in the quote that introduces it | `NAME_NOT_IN_QUOTE` |
| A name another entity already claims in the same document is not admitted as this entity's name | `NAME_CLAIMED_BY_ANOTHER` |
| Time-mention words occur in the quote of the assertion they date | `TIME_NOT_IN_QUOTE` |
| The subject is a listed entity reference | `UNKNOWN_REFERENCE` |
| An object that names no listed entity is admitted as a literal and a signal is recorded | `OBJECT_UNDECLARED` (signal, not a drop) |
| The item is malformed | `MALFORMED_ITEM` |
| The model output was truncated (`finish_reason = length` or an incomplete stream) | `TRUNCATED_OUTPUT` (complete items are kept) |
| A block produced no parsable output | `BLOCK_UNINTERPRETED` |

Offsets and selectors are computed by the server, by locating the quote. Model-reported offsets are never trusted. Template fields that claim span precision pass the same check. When a field cannot be located as a span, its precision is declared coarser (table cell, block, page, document) or `unresolved` under ADR-0058. It is never fabricated.

The checks look only at structure. No word list decides what is a name, a clause, or a date.

### 2. Every drop is a row

Rejected and signalled items are written to `interpretation_drop`:

- run, block, reason code, and model/prompt identity;
- a hash of the raw item, and an access-controlled excerpt of it.

An interpretation run reports its drop counts. A run with any `BLOCK_UNINTERPRETED` or `TRUNCATED_OUTPUT` is `PARTIAL`, not `COMPLETE` (F0016). Missingness answers read drops: a field in a block that was not interpreted is `NOT_PROCESSED`, never `NOT_FOUND`.

### 3. Each block records how its words were obtained

Content blocks carry `text_origin`:

- `STATED`: a native text layer;
- `OCR`;
- `TRANSCRIBED`;
- `DESCRIBED`: a model-generated description of an image, chart, or figure.

They also carry the producing engine, model, and version, and an origin-specific anchor (page and region for OCR, time span and speaker for transcripts, page and figure for descriptions). A block never mixes origins. Evidence inherits the origin of its block.

- **Evidence that is only `DESCRIBED`** cannot close or supersede a canonical fact, and cannot be auto-accepted. It opens a review item with the reason `DESCRIBED_EVIDENCE`.
- **`OCR` and `TRANSCRIBED` evidence** is admissible. It keeps the engine's confidence where one exists, and the evidence precision declares the region.

### 4. Statements carry their mood

When a passage requires, obliges, plans, expects, forecasts, quotes, offers, or makes a statement conditional, the statement carries a `mood` qualifier holding the passage's own words: "subject to", "must", "shall", "will", "quoted", "proposed", "if". A reporting verb ("the broker advised", "the insured stated") is attribution, not mood.

- **A mood-bearing statement is never materialized** as a typed assertion eligible for canonical facts (ADR-0063).
- **It is routed as a candidate** to the structure that fits it:
  - obligations and requirements go to normative constraints (F0052);
  - underwriting conditions go to subjectivities;
  - offered terms go to quote-stage records;
  - hypotheticals go to scenarios (F0053).
- **Operative contract provisions are different.** Once issued, a policy's provisions are facts about the contract: "this policy provides coverage subject to condition X" is an assertion about the policy. The mood marker keeps the condition's content (for example, "the insured maintains sprinklers") from being asserted as a fact about the world.

## Consequences

- **F0004** gains `text_origin` and its anchors on blocks.
- **F0006** gains the `mood` qualifier and the admission service contract.
- **F0016** records drops, drop counts, and run outcomes. **F0022** shows drops per document, separately from review, and shows origin beside evidence.
- **F0026** measures the not-stated rate and drop rates by reason.
- **F0052** receives mood-routed candidates when it ships. Until then they remain open statements that are not materialized.

## Proof gates before acceptance

- **Admission check tests:** a quote absent from its block, a repeated value in two cells, a name claimed by another entity, a time word outside the quote, Unicode and hyphenation normalization, and truncated output. Each produces the specified reason and never a silent loss.
- **Server-computed offsets** match ADR-0058 selectors for PDF, DOCX, XLSX, and CSV fixtures.
- **A chart description** that contradicts a declarations-page limit opens review and does not change the canonical fact.
- **Subjectivity, quote-versus-bound, warranty, and conditional-coverage fixtures** are marked with mood and are not materialized. Operative provisions of an issued policy are asserted as contract facts.
- **A run with an uninterpretable block** reports `PARTIAL`, and the affected fields answer `NOT_PROCESSED`.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [design/extraction](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/extraction.md) (server checks, drop reasons, truncation handling, mood #745)
- [0040 — A chunk says where its words came from](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0040-a-chunk-says-where-its-words-came-from.md)
- [0041 — A name is a claim about an entity](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0041-a-name-is-a-claim-about-an-entity.md) (names checked against the text)
- [0001 — Ontology import and governance](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0001-ontology-import-and-governance.md) (every drop is a row)

Worked and boundary examples: [EX-SEM-005 to EX-SEM-007](../../examples/statements-time-and-governance.md#admission-origin-and-mood).
