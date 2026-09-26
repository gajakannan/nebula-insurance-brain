# ADR-0064: Time Interpretation and Valid-Time Precision

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0007](ADR-0007-full-bitemporality.md) (how valid time is obtained from text), [ADR-0008](ADR-0008-database-level-temporal-integrity.md) (the representation of unknown bounds inside the exclusion constraint), and [ADR-0039](ADR-0039-typed-insurance-values-and-completeness.md) (granularity is part of a typed temporal value)
**Source:** Master blueprint sections 14–16, 87, 109.2. Informed by Utopia decisions 0022, 0024, 0031, and 0045 (see References).

## Context

The blueprint defines two clocks (section 14), exclusion over both (section 15), and a mutation algorithm (section 109.2). Section 109.2 separates source receipt, artifact creation, assertion creation, and canonical acceptance. The blueprint does not say how valid time is read out of text. It has no concept of a time expression, a document's own date, a date's precision, or an end whose date is unknown.

Insurance sources depend on all of these:

- Policy periods run "from 12:01 a.m. standard time at the address of the named insured".
- Endorsements are "effective as of inception" or "effective the 15th of the month following".
- A retroactive date, a loss run "valued as of 06/30", and a fiscal-year exposure period are each different kinds of time.
- A broker email says "last renewal" or "next month".

Utopia recorded three failure modes before it redesigned time handling:

- The model computed dates inside the prompt, leaving no trace.
- Upload time stood in for an undated document's date, so "today" in a regulator's release resolved to the day of ingestion.
- Each chunk resolved relative expressions alone. Three chunks of one bulletin produced three different years for "compared with the end of last year".

## Proposed Decision

### 1. A time mention is evidence

Interpretation reports every time expression as a `time_mention`:

- the verbatim text, and the content block and offsets, located by the admission service (ADR-0065);
- the interpretation run that produced it;
- the assertions it dates. One mention can date many assertions: a column heading "Policy Period 01/01/2026–01/01/2027" dates every value in the column.

### 2. The model interprets; code computes

For each mention, the model returns an interpretation, never a computed date:

| Field | Values |
|---|---|
| `shape` | `POINT`, `INTERVAL`, `AS_OF`, `DURATION`, `ENDED_UNDATED` |
| `reference` | `ABSOLUTE` with the value as written; or `ANCHORED`, naming an anchor (another mention, the document date, or a named period the document defines, such as the policy period or a fiscal year) plus an offset (count, unit, direction); or `NONE` |
| `granularity` | `YEAR`, `QUARTER`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND` |

Code performs the calendar arithmetic, maps fiscal and policy periods to intervals, truncates to the stated granularity, and applies the time-of-day and time-zone conventions the document declares. It also derives the interval the shape implies. It records a resolution grade:

- `A`: absolute;
- `B`: resolved through an anchor;
- `C`: unanchored.

A wrong anchor or offset is visible and correctable. A wrong date written by a model is not.

### 3. A document carries a time context

Each interpreted document version carries a `document_time_context`. The context is seeded from the document's opening and extended block by block. It is stored with the interpretation run so that later re-resolution uses the same basis. It holds:

- **the document's own date, and its source:** `CONTENT`, `SOURCE_METADATA` (a filing, issue, or send date from a system of record or email header), or `HUMAN` (set by a reviewer);
- **the periods and calendars the document defines:** policy period, fiscal year, valuation date, retroactive date;
- **the anchors its narrative sets;**
- **the document's declared time-of-day and time-zone conventions.**

**Upload, sync, receipt, and extraction times are recorded-time facts** (section 109.2's `source_received_at` family). They never enter the context. An undated document has no document date.

### 4. What cannot be resolved waits

A grade-`C` mention keeps its words and interpretation and dates nothing. The assertions it would date carry no valid time. When an anchor arrives, resolution recomputes the dependent intervals: a later block, another document dating the same event, or a reviewer setting the document date. The result is new assertions under a new interpretation run or review decision, never an in-place rewrite (ADR-0037).

### 5. Valid time records its precision and the difference between unknown and open

- **Precision.** Each valid-time bound stores its granularity. A value is truncated to its granularity, so storage, display, and export cannot disagree.
- **Unknown start.** A missing start is not "since always". The lower evidence bound is `attested_from`, the earliest document date among the assertion's evidence.
- **Unknown end.** An ending without a date is `valid_to_state = UNKNOWN` with `attested_to`, the date of the document that says it ended. That is distinct from `OPEN` (still holds) and `BOUNDED`.
- **The exclusion constraint.** F0008 settles the physical representation inside the ADR-0008 constraint. The recommended option: an `UNKNOWN` end closes the range at `attested_to` for integrity purposes, and valid-time reads between the last positive evidence and `attested_to` return `UNKNOWN` rather than the value or absence (section 107.4).

### 6. Each property declares its temporal kind

Ontology properties declare `temporal_kind`, and writes normalize by it:

| Kind | Meaning | Examples |
|---|---|---|
| `STATE` | Holds over an interval | a limit, a named insured, a premium basis |
| `EVENT` | A point at its stated granularity; a span collapses to its start | a loss occurrence, a notice of claim, an issuance |
| `ETERNAL` | Has no valid time | a form's edition identifier, an organization's date of formation |

### 7. Succession uses how a start was obtained, not model confidence

A successor closes its predecessor in a single-valued FactSlot only when:

- its start is grade `A` or `B`;
- the source-authority and change semantics of section 54 allow it.

A grade-`C` successor closes nothing and opens a review item. Succession never reads model confidence. Confidence remains for review routing and display.

### 8. Three document-related times stay apart

1. **Valid time:** when the claim holds.
2. **Attestation:** when the document observed it (the document date).
3. **Recorded time:** when the Brain accepted it.

Section 109.2's receipt and acceptance timestamps belong to the recorded-time family. A retroactive endorsement received June 12 and accepted June 14 is valid from June 1, attested June 10 (its issue date), and recorded June 14.

## Consequences

- **F0004** stores the document date with its source. **F0016** stores the time context, time mentions, and their interpretations per run.
- **F0008** implements precision, `valid_to_state`, and attestation bounds inside the ADR-0008 integrity design.
- **F0012 and F0013** declare `temporal_kind` on every property.
- **F0019 and F0025** take effective dates from time mentions resolved against the policy period, and prove grade-`C` handling.
- **F0022** shows a mention's words beside its resolved interval, and lets a reviewer set a document date, which triggers re-resolution.
- **Retrieval and graph reads** take valid time explicitly (F0020, F0035). Full-text reads remain "now" unless versioned.

## Proof gates before acceptance

- **Normalization accuracy on the Golden Corpus**, reported per shape and grade. Proposed starting thresholds are ≥ 95% for absolute mentions and ≥ 85% for anchored mentions. F0026 sets the final numbers with named reviewers.
- **Endorsement acceptance** (section 87 and F0025): "effective as of inception", "effective the date shown above", and a policy-period time-of-day convention each resolve correctly, and the June 1 / June 12 / June 14 example produces the answers above.
- **Undated documents:** a document with only an upload time and the text "today" produces a grade-`C` mention and no valid time. Setting its document date re-resolves it without re-parsing.
- **Unknown ends:** reads distinguish `OPEN`, `BOUNDED`, and `UNKNOWN`, and never widen an unknown start to negative infinity.
- **Fiscal and 52/53-week periods, time zones, and date-only values** are covered by regression cases in section 98.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0045 — A time mention is resolved against its document](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0045-a-time-mention-is-resolved-against-its-document.md)
- [0022 — An unknown date is not an open one](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0022-an-unknown-date-is-not-an-open-one.md)
- [0024 — The world axis reaches the second](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0024-the-world-axis-reaches-the-second.md)
- [0031 — An event holds at the moment it names](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0031-an-event-holds-at-the-moment-it-names.md)
- [design/time](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/time.md)

Worked and boundary examples: [EX-SEM-003 and EX-SEM-004](../../examples/statements-time-and-governance.md#time-interpretation).
