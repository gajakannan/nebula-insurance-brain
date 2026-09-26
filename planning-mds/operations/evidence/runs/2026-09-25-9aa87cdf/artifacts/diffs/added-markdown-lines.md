The runtime epic inventory is the master blueprint section 95 roadmap (original F0001 to F0063, plus F0065 and F0066), sequenced per sections 115.3 and 124. F0064 tracks repository tooling separately. The authoritative registry is `features/REGISTRY.md` and the sequencing view is `features/ROADMAP.md`, both generated from `kg-source/features/**`. The original 63 runtime features retain their identifiers and stages. F0065 adds a bounded neurosymbolic assessment in v0.1B under the user-authorized 2026-09-07 amendment; its draft architecture remains subject to proof and review. F0066 adds open-statement extraction and signature alignment in v0.2B under ADR-0063, accepted as direction on 2026-09-25. Story links are appended by the plan action as each feature is planned.
- [F0066 — Open-statement extraction + signature alignment](features/F0066-open-statement-extraction-and-signature-alignment/README.md) - Planned (added 2026-09-25, ADR-0063)
- `architecture/decisions/` — ADR-0001 to ADR-0069 (Accepted architecture and Proposed contracts; ADR-0060 proposes Docling-Graph, with pinned synthetic development proof complete and production acceptance pending; ADR-0063 is accepted as direction and ADR-0064 to ADR-0069 are Proposed, section 4.11)
### 4.11 Statements, time, and governance amendments (2026-09-25)

The operator reviewed Utopia's decisions made after this repository started (2026-09-05, Utopia commit `b3919ca`) and approved incorporating them.

- **[ADR-0063](architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), accepted as direction.** Open statements in the source's own words, beside typed assertions. Typed assertions come from template extraction (form-shaped sections) or from per-signature alignment (narrative sections, F0066, v0.2B).
- **[ADR-0064](architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) to [ADR-0069](architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md), Proposed.** They cover time interpretation and valid-time precision, assertion admission, text origin and mood, names as time-bounded claims, impact-gated automation with human precedent and a revert fuse, decision basis fingerprints, and external action attempts.

**v0.1 impact** is limited to storage and contracts, because they are expensive to retrofit after F0003, F0006, and F0008 ship:

- F0004 (document date source, text origin);
- F0006 (assertion kinds, admission, mood);
- F0007 and F0013 (name FactSlots, temporal kinds);
- F0008 (precision, unknown ends);
- F0014 (interpretation route);
- F0016 (time mentions, drops, basis);
- F0017 (identifier-first names);
- F0019, F0022, F0025, F0026.

v0.1 acceptance still runs on the template route. Later features carry the behavioural parts: F0027, F0032, F0043, F0050, F0052, F0056, F0059.

Scope amendments are recorded in each feature README. Master blueprint sections 3, 11, 14, 17, 29, 53, 56, 62, 64, 75, 76, 78, 95, and 99 were revised in place, and the glossary and [examples EX-SEM-001–011](examples/statements-time-and-governance.md) were added.

**Not changed:** F0002's approved plan. Utopia's same-knowledge-base provenance record (0048) matches F0002's composite ownership keys. Its extra safeguards are left as a follow-up for the F0002 implementation run, not an amendment to the approved plan:

- ownership columns made immutable by trigger;
- triggers for link tables that have no owner column;
- deferred self-references for restore.

5. v0.2A — F0033 to F0040 and F0044 to F0047; v0.2B — F0027 to F0032, F0066 (open-statement alignment, ADR-0063), and F0041 to F0043
| Statements, time, and governance amendments (2026-09-25) to sections 3, 11, 14, 17, 29, 53, 56, 62, 64, 75, 76, 78, 95, 99 | ADR-0063 to ADR-0069; `BLUEPRINT.md` section 4.11; F0066; feature scope amendments; `examples/statements-time-and-governance.md` |
assertion                       assertion_kind: OPEN_STATEMENT | TYPED_ASSERTION (ADR-0063)
assertion_qualifier             role-word qualifiers on open statements; includes mood (ADR-0065)
typed_assertion_source          open statements behind a materialized typed assertion (ADR-0063)
time_mention                    verbatim time expression, interpretation, computed interval, grade (ADR-0064)
document_time_context           per document version and run (ADR-0064)
interpretation_drop             refused / truncated / uninterpreted items with reason (ADR-0065)

kind_word_binding               (ADR-0063, F0066)
signature_binding               with decision basis (ADR-0063, ADR-0068)
implication_rule
implication_rule_version
phrase_reading
entity_alias                    search projection over name facts (ADR-0066)
automated_decision              action, confidence, precedents, trace, undo, status (ADR-0067)
automation_fuse                 per KB and automation type (ADR-0067)
action_definition               revisioned (ADR-0069)
action_attempt                  request identity, dispatch token, state (ADR-0069)


## Statements, time, and governance additions (ADR-0063 to ADR-0069)

These are proposed contract additions, not claims about the current schema. The feature named for each record settles its columns in Phase B.

| Record | Required information | Owner |
|---|---|---|
| Assertion (kind) | `assertion_kind`; for open statements: nullable `predicate_id`, source relation phrase, subject/object references or literal, mandatory quote with server-computed selector; typed assertions carry the ontology release | F0006 |
| Assertion qualifier | Role word as written, value or entity reference; `mood` holds the passage's own words | F0006 |
| Typed assertion source | Typed assertion ↔ open statement(s), with binding or implication-rule version; retirement when no source holds | F0066 |
| Time mention | Text, block, offsets, run, shape/reference/anchor/offset/granularity, computed interval, resolution grade, assertions dated | F0016 |
| Document time context | Document date and its source (`CONTENT`, `SOURCE_METADATA`, `HUMAN`), defined periods and calendars, anchors, time-of-day/time-zone convention | F0004/F0016 |
| Canonical fact version (time) | Per-bound granularity; `valid_to_state` (`OPEN`, `BOUNDED`, `UNKNOWN`); `attested_from`, `attested_to` | F0008 |
| Content block (origin) | `text_origin`, producing engine/model/version, origin-specific anchor; no mixed origins | F0004 |
| Interpretation drop | Run, block, reason code, model/prompt identity, raw-item hash, access-controlled excerpt | F0016 |
| Signature binding | Signature (phrase, subject classes, object classes or VALUE), property, direction or `NONE`/`UNDECIDED` with reason, ontology release, basis hash, decider, confidence | F0066 |
| Implication rule / phrase reading | Signature or kind-word key, concluded property, object source, version; reading cached per distinct phrase including "no answer" | F0066 |
| Name facts | `hasLegalName`, `hasTradeName`, `hasFormerName`, `knownAs` FactSlots; `entity_alias` becomes a projection | F0007/F0013/F0017 |
| Automated decision | Target, action, confidence, model sentence, precedents shown, trace, undo data, status; impact-hold reason | F0027/F0043 |
| Decision basis | `basis_hash` on interpretation runs, bindings, resolution verdicts, derived facts/assessments, impact analyses | F0016/F0027/F0032/F0056/F0065/F0066 |
| Action attempt | Execution request id (unique `NULLS NOT DISTINCT` with action and scope), definition revision, dispatch token, state, response capture, timestamps, safe request snapshot | F0050/F0059 |
# ADR-0063: Open Statements and Signature Alignment

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Deciders:** Operator (direction accepted 2026-09-25); Architect (record owner)
**Accepted as:** Direction. The proof gates below qualify the implementation and the activation of open extraction for a document profile. They do not reopen the direction.
**Refines:** [ADR-0005](ADR-0005-three-plane-knowledge-model.md) (the assertion plane gains two layers), [ADR-0014](ADR-0014-document-profiles-drive-interpretation.md), [ADR-0015](ADR-0015-extraction-profiles-are-composable.md), [ADR-0016](ADR-0016-semantic-reinterpretation-is-incremental.md) (reinterpretation recomputes per signature where alignment applies), and [ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md) (template extraction remains the route for form-shaped content, but is no longer the only route to a typed assertion)
**Source:** Master blueprint sections 5, 11, 28–30, 101. Informed by Utopia decision 0044 and its design notes (see References).

## Context

Every interpretation route planned before this record binds a claim to the ontology when the claim is extracted. F0015 compiles document and extraction profiles into Pydantic templates, and Docling-Graph fills those templates from persisted content (ADR-0060). That works well for form-shaped sources: declarations pages, ACORD applications, schedules of values, and loss-run tables. There, the template matches the page.

For narrative sources, binding at extraction time has a measured cost. Endorsement wording, broker correspondence, underwriting notes, inspection reports, and conversation are examples. Utopia compared the two approaches on public corpora on 2026-09-15:

- Statements written in the document's own words had 0 unstated out of 333 and 2% misworded.
- Facts bound to a property list at extraction time had 4–9% unstated and about 16% misworded.
- The property list itself induced facts, for example an award recorded as a genre, or a place given a notable work.

Binding at extraction time also ties each document to the ontology release it was read under. When that release changes, sections 28–29 re-run interpretation over candidate blocks, so cost grows with the number of documents.

Utopia's measurements also record the limit of the alternative. Aligning statements after extraction recovered fewer facts (6.5–12% against 15.5% of gold facts) until the aligner read the source text and gained implication rules. Implicit facts, such as a country implied by "a British film", are not stated as statements. The direction below keeps both routes for that reason.

## Decision

### 1. The assertion plane holds three layers

- **Open statement.** What a source says, in its own words. It is an `Assertion` with:
  - `assertion_kind = OPEN_STATEMENT`;
  - a subject reference, the source's relation phrase, and an object reference or literal;
  - qualifiers keyed by the passage's own role words;
  - time-mention references (ADR-0064);
  - a mandatory verbatim quote located by the admission service (ADR-0065);
  - `predicate_id` NULL.

  It needs no ontology and is retained whatever the ontology becomes. Entities referenced only by description, such as "the named insured's subsidiary", stay document-local until identity resolution attaches them.
- **Ontology.** Versioned modules, unchanged (ADR-0011). A property gains, as ontology data:
  - its temporal kind (ADR-0064);
  - its definition, examples, and regression cases.
- **Typed assertion.** A claim expressed in an ontology property, with the ontology release it was computed under. Only typed assertions reach entity resolution, conflict resolution, FactSlot selection, and canonical commit.

Fact mode, origin, and interpretation basis (ADR-0035) apply to both assertion kinds. Open statements are always `EXPLICIT`.

### 2. Two routes produce typed assertions

1. **Template extraction.** This is the existing ADR-0060/F0015 path. It applies where a document profile declares a section form-shaped. Each field it produces is a typed assertion and passes the same admission checks (ADR-0065).
2. **Signature alignment.** This applies where a profile declares a section narrative, or declares both routes.
   - **Signature:** the normalized relation phrase, the subject's class set, and the object's class set, or `VALUE` for a literal.
   - **Decided once per signature,** per knowledge base and ontology release, never per assertion.
   - **Binding:** records the property, the direction, the ontology release, the decision basis (ADR-0068), the decider, and the confidence.
   - **Materialization:** a set operation. Each supporting open statement adds a `typed_assertion_source` row. A typed assertion retires when no source statement still supports it under a current binding. Several statements that give the same claim yield one typed assertion.

Each document profile section declares `interpretation_route ∈ {TEMPLATE, OPEN, TEMPLATE_AND_OPEN}` (F0014). When both routes produce a claim for the same FactSlot, the claims are ordinary competing assertions for conflict resolution (section 54). Neither route overrides the other.

### 3. Alignment rules

- **Kind words bind to classes first.** "Named insured" and "additional insured" are roles, not kinds (see the boundary example). "Contractor" and "premises" are kind words.
- **Candidates are admitted structurally.** A property is a candidate when its declared domain and range admit the endpoint classes or an ancestor of them. A candidate that fits only by inheritance is shown to the aligner as such. When the structure admits more candidates than the configured limit, a shortlist uses ontology-description embeddings and label overlap. The shortlist is part of the decision basis.
- **The aligner reads the source.** Each decision sees example statements with their quotes and blocks. It does not see only the phrase.
- **Two votes must agree.** The candidates are presented in opposite orders, and both votes must pick the same property and direction. Disagreement, no admissible candidate, and overflow are recorded as `UNDECIDED`, `NONE`, and `UNDECIDED(too_many_candidates)`. None of them is skipped silently.
- **A person's binding is final.** The aligner never overwrites it. Human decisions are review decisions (section 75) and precedents (ADR-0067).
- **Implication rules.** An open statement of a given shape can imply a typed assertion of another property. Examples:
  - a "subsidiary of" phrase implies a parent-organization relationship;
  - an "LLC" designator implies the legal-entity form;
  - "a Texas corporation" implies the jurisdiction of incorporation.

  The rule is proposed by the aligner and approved by a person, and code executes it. A reading of the object phrase, such as the jurisdiction a demonym names, is requested once per distinct phrase and cached. Materialization never calls a model. Implied assertions carry `interpretation_basis = INFERRED`, the rule version, and the triggering statement's evidence.
- **Mood.** A statement that carries a mood qualifier (ADR-0065) is never materialized as a typed assertion eligible for canonical facts.

### 4. Reinterpretation follows the route

- **Alignment route.** An ontology or rule release recomputes only the signatures and rules whose basis changed (ADR-0068). A model is consulted only for signatures that must be decided again. Documents are not re-read.
- **Template route.** Targeted reinterpretation over candidate blocks, as in ADR-0016 and ADR-0060. Neither route re-parses content (ADR-0003).

### 5. What is excluded

- **No ontology in the open-extraction prompt.** It is the mechanism that induces unstated facts.
- **No dates computed by the model** (ADR-0064), and **no word lists in code** for names, relation shapes, or time expressions. Lexicons are governed data with provenance.
- **No typed assertion from alignment without either an open statement or an approved implication rule behind it.**

## Consequences

- **F0006** stores both assertion kinds from v0.1: nullable predicate, source phrase, role-word qualifiers, time-mention references, and a mandatory quote. v0.1 acceptance runs on the template route and does not depend on alignment.
- **F0066** delivers open extraction, kind-word and signature alignment, implication rules, and materialization in v0.2B. It follows the F0030 ontology release workflow, which it needs for definitions and regression cases.
- **Review** gains an alignment queue (F0043).
- **Cost** grows with the number of distinct phrasings, not the number of documents. Utopia saw kind-word decisions fall from 54 to 5 new words on a second pass over the same corpus.
- **Coverage** depends on how many kind words are bound and on the ontology's size. An unbound signature stays in the open layer, loses nothing, and feeds ontology suggestions (F0029/F0030).

## Proof gates

These gates qualify implementation and per-profile activation.

1. **Open-layer faithfulness.** On the Golden Corpus narrative slice (endorsement wording, broker correspondence, underwriting notes), open statements have ≤ 2% not stated, judged by a model calibrated against a hand-labelled set whose agreement is reported. Measure over two runs per configuration, and report the judge's own variance.
2. **Typed-layer parity.** For each narrative profile, alignment is activated only when its typed assertions reach at least the template route's judged precision and recall, on the same documents, over two clean runs. Until then that profile stays on `TEMPLATE`, and its open statements are retained without being materialized.
3. **Cost.** Report prompt and completion tokens per document, and the model calls spent deciding signatures as the corpus grows.
4. **Materialization is set-exact.** Idempotence and retirement are tested against a real PostgreSQL. A statement is invalidated, a binding changes, a property changes, and several statements back one assertion; the result is identical regardless of arrival order.
5. **Human precedence.** A binding decided by a person during an agent run is never overwritten.

## References

Utopia records at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a). Ideas are incorporated natively; no code is adopted.

- [0044 — The ontology is a view over what documents say](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0044-the-ontology-is-a-view-over-what-documents-say.md) (prototype measurements, three layers, alignment, implication rules)
- [0053 — A phrase decision records the inputs it considered](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0053-a-phrase-decision-records-the-inputs-it-considered.md)
- [design/ontology](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/ontology.md) and [design/extraction](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/extraction.md)
- [design/prior-work](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/prior-work.md) (open information extraction, canonicalization, and alignment pitfalls)

Worked and boundary examples: [EX-SEM-001 and EX-SEM-002](../../examples/statements-time-and-governance.md#open-statements-and-alignment).
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
# ADR-0066: Names Are Time-Bounded Claims

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0006](ADR-0006-factslot-defines-canonical-semantic-identity.md) (names become FactSlots) and [ADR-0025](ADR-0025-deterministic-er-ships-before-probabilistic-er.md) (the role names play in resolution)
**Source:** Master blueprint sections 53, 70, 78 (`entity_alias`). Informed by Utopia decision 0041 and its identity design (see References).

## Context

Section 78 plans `entity_alias` as a table beside `entity`. Insurance names change and are contested, and that change is information:

- a named insured is amended by endorsement;
- a company trades under a DBA;
- a policy lists "formerly known as";
- a broker writes an abbreviation;
- a loss run spells a name one way and the application another.

A plain alias table cannot tell you when a name was used, which document said so, or whether the claim was later corrected. It rebuilds, outside the ledger, what the ledger already does for everything else.

Utopia replaced its alias array with name facts for these reasons. It also found that identity keyed on the surface string fails two ways:

- **a namesake** is one string for several things;
- **an alias** is several strings for one thing.

Batch model verdicts on similar-looking names produced confident wrong merges.

## Proposed Decision

### 1. Names are assertions and facts

- **The name FactSlots.** A name is a typed assertion on one of the system name properties:
  - `hasLegalName`: single-valued per valid time;
  - `hasTradeName`: multi-valued, DBA;
  - `hasFormerName`;
  - `knownAs`: multi-valued; abbreviations and informal names.
- **What a name carries.** Its value, a qualifier for the name kind where needed, a verbatim quote (admitted under ADR-0065), both clocks, and the normal change semantics.
- **The display name.** An entity's display name is selected from its current accepted name facts. It is not a separate authority.
- **`entity_alias`.** A rebuildable search projection over name facts.

### 2. A rename keeps the entity

An endorsement that changes the named insured does not create a new entity. It asserts a new legal name valid from the endorsement's effective date (ADR-0064), and the prior legal name ends there. "What was the named insured on March 3?" is an ordinary valid-time query.

### 3. Names propose identity; they never decide it alone

- **v0.1 deterministic resolution (F0017)** keys on identifiers: policy number, FEIN, NAIC, and stable source identifiers. An exact name match with no identifier creates a review pair. It never merges.
- **Similarity is only a proposal.** Name-vector, abbreviation, containment ("Acme" inside "Acme Holdings"), and cross-script matches (F0027) only propose pairs. A pair proposed by similarity is never merged on a batch model verdict alone. It needs a tool-assisted second look that reads the evidence of both sides, or a person.
- **A name another entity of a compatible type already holds** creates a shared-name review pair, never a merge.
- **A role is not an entity.** "The named insured", "the first named insured", and "the additional insured" are roles that point at entities.

### 4. A merge moves name facts with everything else

Merges and reverts (section 53) move name facts with every other fact. A read at a recorded time before a merge shows both entities, each with its own names.

## Consequences

- **F0007** defines the name FactSlots. **F0013** declares the name properties and their kinds.
- **F0017** implements identifier-first resolution and shared-name review pairs.
- **F0027** adds similarity channels as proposals only, with the second-look requirement.
- **F0023** lists an entity's names with their sources and validity.
- **`entity_alias`** in section 78 is recast as a projection.

## Proof gates before acceptance

- **A named-insured change by endorsement** answers the legal name as of dates before and after the change, with evidence for each.
- **Two entities with the same legal name and different FEINs** stay apart. A DBA shared with another entity creates a review pair.
- **An abbreviation arriving before the full name,** and the reverse order, resolve to the same outcome. Measure pairwise precision and recall in both arrival orders and report the difference.
- **A name absent from its quote,** or claimed by another entity in the same document, is dropped with its reason (ADR-0065).

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0041 — A name is a claim about an entity](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0041-a-name-is-a-claim-about-an-entity.md)
- [design/identity](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/identity.md), including #889 (a similarity-proposed pair is never auto-merged on the batch verdict alone)

Worked and boundary examples: [EX-SEM-008](../../examples/statements-time-and-governance.md#names).
# ADR-0067: Automation Gated by Unrecallable Impact, Human Precedent, and a Fuse

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0044](ADR-0044-review-surface-and-approval-contract.md), [ADR-0047](ADR-0047-controlled-learning-and-reinterpretation.md), and [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md); gives the section 64 Execution Gate its first concrete check
**Source:** Master blueprint sections 53, 64, 75, 110.5, 111. Informed by Utopia decisions 0025, 0026, 0027, 0028, and 0043 (see References).

## Context

Section 64 lists what the Execution Gate should consult, and section 53 says merges are reversible. Neither addresses what Utopia found in production use.

**Undo restores the graph, not what the graph was read into.** Suppose an automated merge of "Acme" and "Acme Corp" is reverted on Monday. Meanwhile it had already:

- produced a derived assessment;
- opened a conflict someone looked at;
- been cited in a chat answer;
- entered an export.

None of that is recalled by the revert.

Confidence is the wrong axis for this. A 0.93-confident merge that touches nothing downstream is cheap to undo. A 0.99-confident merge that an F0065 assessment rests on is not.

Utopia also found two other failure modes:

- An agent that learns from its own past decisions cites itself and grows more confident each round.
- Nothing stops automation that keeps being wrong.

## Proposed Decision

### 1. Hold automated changes whose effects cannot be recalled

This applies to every automatic change made without a person's decision:

- entity merges (F0017, F0027);
- automated resolution of review queue items (F0043);
- automatic promotion (F0042);
- agent-proposed actions (F0059).

Before applying such a change, the service computes its impact. Any one of the following holds the change for a person, whatever the confidence:

| Impact kind | Hold when |
|---|---|
| `CONFLICT` | Two values of a single-valued FactSlot would hold at the same valid-time moment in current recorded time. A succession is not a conflict (ADR-0064). |
| `DERIVED` | A live derived fact, assessment (F0065), or derivation (F0055) rests on an affected row |
| `CITED` | An affected entity or fact was cited in a conversation answer (F0037) or a decision-ledger entry (F0057) |
| `EXPORTED` | An affected row has left the Brain through an export or an external projection; opt-in per knowledge base |

The hold reason is recorded as `IMPACT_HOLD:<kind> <detail>`, for example `IMPACT_HOLD:DERIVED 3 assessments`. The UI presents it as a reason, not as doubt about the verdict.

Decisions that only keep things apart (keep separate, keep both) are not gated, because the next decision undoes them and nothing outside the Brain is told.

### 2. Only human decisions are precedent

Automated deciders may read the knowledge base's review ledger as precedent: earlier decisions on these names, on either name, on this type pair, on reverted merges, and on this queue.

- **Only rows with a human actor count.** An agent's own decisions are never precedent.
- **Precedent contradicting a verdict blocks automatic application.** Agreeing precedent may lower the threshold by a configured amount.
- **Pairs already decided by a person** are applied as that person decided.
- **A precedent includes the reviewer's optional free-text `why`.** Reason codes remain for analytics. A free-text `why` is optional and never required, because a mandatory field teaches that people decide without reasons.
- **Verdict caches are keyed on the precedent set they were decided with** (ADR-0068).

### 3. Automated decisions act through the people's paths and can be reverted

- **Each automated decision is a row:** target, action, confidence, the model's sentence, the precedents shown, the tool trace, status, and the data needed to undo it.
- **It calls the same service function a person's decision calls,** so the graph ends up in the same shape.
- **A person can accept, override, or revert it.** An override becomes a precedent.

### 4. A fuse turns automation off

Per knowledge base and automation type, a configured number of reverts of automatic actions within a window turns that automation off. The default is two within seven days. Tripping the fuse:

- raises an alert;
- writes an audit event with a system actor;
- requires a person to re-enable it.

### 5. Defaults differ from Utopia

Every automation type is **off by default** per knowledge base. It is enabled only after its agreement rate has been measured against human decisions on the Golden Corpus (F0026 and the F0043 gate).

## Consequences

- **F0027 and F0043** implement the impact computation, the precedent reading, automated-decision rows, and the fuse.
- **F0059** reuses the impact check as its first concrete gate.
- **F0022 and F0043** capture the optional `why` beside reason codes.
- **F0037 and F0057** record which entities and facts an answer or decision cited, so `CITED` is computable.

## Proof gates before acceptance

- **A confident merge that an F0065 assessment rests on** is held with `IMPACT_HOLD:DERIVED`. The same merge with nothing downstream applies.
- **A merge that would put two legal names on one entity at the same moment** is held with `CONFLICT`. A dated rename succession is not held.
- **An agent's own decision** never appears as precedent. A person's contrary decision blocks the next automatic verdict on the same pair.
- **Two reverts within the window** disable the automation and produce the alert and audit event.
- **Measured on a labelled set:** agreement rate, share decided automatically, wrong-merge count, and revert rate. Report these before any automation is enabled.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0027 — An automatic merge is gated by what it can undo](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0027-an-automatic-merge-is-gated-by-what-it-can-undo.md)
- [0025 — Governance reads the ledger before it decides](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0025-governance-reads-the-ledger-before-it-decides.md)
- [0026 — A decision records why](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0026-a-decision-records-why.md)
- [0028 — The adjudicator looks before it asks](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0028-the-adjudicator-looks-before-it-asks.md)
- [0043 — Every review queue is governed](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0043-every-review-queue-is-governed.md)
- [design/governance](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/governance.md)

Worked and boundary examples: [EX-SEM-009](../../examples/statements-time-and-governance.md#automation-and-impact).
# ADR-0068: Decision Basis Fingerprints Define Staleness

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0016](ADR-0016-semantic-reinterpretation-is-incremental.md), [ADR-0017](ADR-0017-knowledge-evolution-is-first-class.md), [ADR-0026](ADR-0026-derived-facts-have-dependency-lineage.md), and [ADR-0045](ADR-0045-ontology-release-compatibility.md)
**Source:** Master blueprint sections 29, 30, 56, 112. Informed by Utopia decision 0053 (see References).

## Context

The Brain caches many decisions that depend on inputs that can change:

- interpretation runs;
- alignment bindings (ADR-0063);
- entity-resolution verdicts;
- derived facts and assessments;
- ontology impact analyses.

Knowledge evolution (sections 29–30) and derived invalidation (section 56) both need to know which cached decisions are no longer valid.

Utopia first compared timestamps ("was the input updated after the decision?") and found four failures:

1. **An inherited input.** A property declared on a parent class was never among the inputs considered, so no edit to it ever made the decision stale.
2. **A structural edge without a timestamp.** Adding or removing a subclass edge silently changed which candidates were admissible.
3. **An edit during the model call.** It committed before the decision, so the decision looked newer than the edit.
4. **Structural non-decisions were skipped rather than recorded.** Examples are "no candidate" and "too many candidates". So a lost support never retired its projection, and an overflow re-queued forever.

## Proposed Decision

### 1. A decision stores a fingerprint of what it considered

Every cached or automated decision that depends on mutable inputs stores a `basis_hash`. It is computed over the canonical serialization of every input the decider saw, and it is computed before any model is called.

| Decision | Basis includes |
|---|---|
| Interpretation run (F0016) | Artifact hash, selected blocks, profile/template/schema/prompt hashes, pipeline revision and configuration, model identity, document time context (ADR-0064) |
| Alignment binding (ADR-0063) | Ancestor closures of both endpoint classes, the value flag, and the admitted candidate properties with each property's version |
| Entity-resolution verdict (F0017, F0027) | Both entity profiles as read (name facts, identifiers, classes, neighbours), and the precedent set shown (ADR-0067) |
| Derived fact or assessment (F0055, F0065) | Exact input fact versions, rule version, ontology release, and evaluator version |
| Ontology/profile impact analysis (F0032) | The release diff and the dependency index version it was computed against |

### 2. Staleness is a changed fingerprint

A decision is stale when the fingerprint of its current inputs differs from the stored one. It is never judged against a clock. Workers recompute fingerprints for live decisions from data they already load.

- **A decision whose subject no longer exists** is orphaned. It is not consulted, and its projections retire through the normal materialization rules.
- **Unchanged inputs leave no queued work.**

### 3. Structural outcomes are decisions

"No admissible candidate", "too many candidates", and "input missing" are recorded as decisions with their reason and basis. They take part in staleness like any other decision: a candidate added later reopens a `NONE`.

### 4. A person's decision is never re-evaluated automatically

A human decision stores its basis for display and audit. When the basis changes, the decision is marked "inputs changed since decision". It may raise a review item. An agent never overwrites it.

## Consequences

- **F0016** and **F0066** (alignment) store bases.
- **F0032** uses fingerprints to schedule targeted reinterpretation.
- **F0056** uses fingerprints to find the derived facts to invalidate.
- **F0065** already pins exact input versions; its assessment records add the hash.
- **F0027** keys its verdict cache on the basis, including precedents.

## Proof gates before acceptance

Each gate runs against a real PostgreSQL, with a scripted model where one is needed.

- **Inheritance:** a property declared on an ancestor becomes admissible, and removing the parent edge retires the dependent projection without a model call.
- **Concurrent edits:** an edit committed while the model call is in flight leaves the decision stale on the next run.
- **Structural outcomes:** overflow is recorded as undecided, with no model call and no re-queue, and shrinking the candidate set makes it executable again.
- **Human decisions:** a person's decision is never overwritten, and it shows "inputs changed" after an input edit.
- **Derived facts:** changing one input fact version re-flags only the derived facts and assessments whose basis includes it.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0053 — A phrase decision records the inputs it considered](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0053-a-phrase-decision-records-the-inputs-it-considered.md)
- [0060 — A rule's definition has a history](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0060-a-rule-definition-has-a-history.md) (a conclusion names the definition version it was drawn under; F0065 already requires this)

Worked and boundary examples: [EX-SEM-010](../../examples/statements-time-and-governance.md#decision-basis).
# ADR-0069: Action Attempts Keep Their Identity and Uncertain Outcome

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0028](ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md) (a retry policy for external side effects) and [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md) (delegated action execution); complements [ADR-0041](ADR-0041-atomic-semantic-commit-and-projection-delivery.md), which covers internal commits
**Source:** Master blueprint sections 62, 64, 69, 91. Informed by Utopia decisions 0034 and 0050 (see References).

## Context

ADR-0041 makes internal semantic commits atomic and idempotent. External side effects are a different problem. Examples:

- an approved action calling a policy administration system;
- a notification;
- a webhook to a broker portal;
- a future MCP mutation tool.

Temporal (ADR-0028) retries activities by default. A synchronous "call, then record" shape cannot tell a request that was never sent from a remote effect whose response was lost. A retry can then repeat a non-idempotent effect, such as issuing an endorsement twice.

Utopia modelled this before building its action sender and found two tempting shortcuts that each produced duplicate dispatches:

- an ordinary nullable unique key;
- letting recovery take over a prepared attempt.

## Proposed Decision

### 1. An attempt has an identity before it has an effect

Each explicit user or approved-agent operation carries an `execution_request_id`, scoped to actor, action, and tenant/knowledge base.

- **Equal inputs under a new ID** are a new operation.
- **An existing ID with different inputs or a different definition revision** is a conflict.
- **A replay re-authorizes** before it reads back the attempt.
- **Uniqueness uses `NULLS NOT DISTINCT`,** which the PostgreSQL 18 build supports, and includes the action's identity.

### 2. A preview is bound to a revision

Every action definition edit and credential rotation increments the definition's revision in the same transaction.

- **Preview** returns the revision and a rendered request with no secrets, without dispatching.
- **Execution** renders from the same revision and validated arguments. It never uses a client-supplied URL, body, or header set.

### 3. Dispatch passes through explicit states

| State | Meaning |
|---|---|
| `PREPARED` | Intent persisted; no dispatch grant; replays only read it |
| `DISPATCHING` | A unique dispatch token and the authorization gate committed; only the original flow may send, and only after commit confirmation |
| `NOT_SENT` | Expiry or cancellation won atomically before dispatch |
| `RESPONSE_RECEIVED` | A response was observed (status, capture state, safe excerpt), independent of 2xx |
| `OUTCOME_UNKNOWN` | Dispatch may have happened and no durable observation establishes a response |

- **Recovery never turns `OUTCOME_UNKNOWN` into a sendable state.**
- **A late response** may update an unknown attempt using the original token. It never grants another send.
- **A lost commit acknowledgement means do not send.**
- **No database lock is held across the network.**
- **Revocation:** a revocation before the gate rejects the attempt; a revocation after it cannot recall the request.

### 4. No automatic retry of dispatch

- **Temporal activities that dispatch external effects** use a maximum of one attempt for the dispatch step, unless the remote contract honours an idempotency key that the attempt carries.
- **Internal, idempotent recomputation** may retry normally.
- **Redirects are not followed.**
- **HTTP 202 is a response, not proof of business completion.** A 500 may follow a remote effect.

### 5. A response is not a fact

A response is never written into canonical state directly. If it carries business information, that information enters as an observation through the normal assertion, review, and commit path, with `origin = SYSTEM_OBSERVATION`.

## Consequences

- **F0050** adopts the retry rule for external-effect activities.
- **F0059** executes approved actions through this state machine.
- **F0047's future mutation tools** and any webhook sender use it.
- **Retention** of attempts follows ADR-0043.
- **Audit** records the dispatch token, timestamps, and the immutable safe request snapshot.

## Proof gates before acceptance

- **Concurrent duplicate submissions** under one ID dispatch at most once.
- **Changing authorization or the definition revision** after preview rejects the attempt at the gate.
- **Process kills** after `PREPARED`, after `DISPATCHING`, and after the remote effect never produce a second dispatch, and leave the correct state.
- **Lost response bodies, timeouts, redirects, 202, and 500** are recorded as specified.
- **A Temporal activity replay** of an external-effect step does not re-send.

This supports **at-most-once application dispatch**. It does not provide exactly-once external business execution, which requires a remote contract the Brain cannot invent.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0050 — An action attempt keeps its identity and uncertain outcome](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0050-an-action-attempt-keeps-its-identity-and-uncertain-outcome.md)
- [0034 — An action is a declared call](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0034-an-action-is-a-declared-call.md)

Worked and boundary examples: [EX-SEM-011](../../examples/statements-time-and-governance.md#action-attempts).
**Statements, time, and governance update (2026-09-25):** Seven records incorporate what Utopia learned after this repository started (2026-09-05). [ADR-0063](decisions/ADR-0063-open-statements-and-signature-alignment.md) is accepted as direction: the assertion plane holds open statements in the source's own words beside typed assertions, and signature alignment joins template extraction as a route to typed assertions. [ADR-0064](decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) to [ADR-0069](decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) are Proposed. They cover:

- time interpretation and valid-time precision;
- assertion admission, text origin, and mood;
- names as time-bounded claims;
- impact-gated automation;
- decision basis fingerprints;
- external action attempts.

Sections 3, 11, 14, 17, 29, 53, 56, 62, 64, 75, 76, 78, 95, and 99 are revised in place. Examples: [statements, time, and governance](../examples/statements-time-and-governance.md).

Reviewed again on 2026-09-25 against Utopia's decisions since 2026-09-05 (its commit `b3919ca`). These later ideas are incorporated:

```text
open statements in the source's words; ontology as a view; per-signature alignment   ADR-0063 (accepted direction)
time mentions interpreted by the model and computed by code; precision; unknown ends  ADR-0064
structural admission checks, drop records, text origin, statement mood             ADR-0065
names as time-bounded claims; similarity only proposes identity                      ADR-0066
automation held on unrecallable impact; human-only precedent; revert fuse           ADR-0067
decision basis fingerprints instead of timestamps                                    ADR-0068
external action attempts with identity and uncertain outcome                         ADR-0069
```

Where Nebula is already stronger, it keeps its own design:

- **FactSlot identity with qualifiers** (section 13);
- **missingness states** (section 107.4);
- **conjunctive authorization** (sections 118–120);
- **declared evidence precision**, including `unresolved` (section 108.2).

Unlike Utopia, automation is off by default per knowledge base (ADR-0067).

## Open statements and typed assertions (ADR-0063, ADR-0065)

The assertion plane holds two kinds of assertion.

```text
OPEN_STATEMENT
    what the source says in its own words: subject, relation phrase, object or literal,
    role-word qualifiers, time-mention references, mandatory verbatim quote; no predicate

TYPED_ASSERTION
    the claim in an ontology property, marked with the ontology release;
    produced by template extraction (form-shaped profile sections) or by
    signature alignment of open statements (narrative sections)
```

Only typed assertions reach entity resolution, conflict resolution, FactSlot selection, and canonical commit.

- **Alignment** decides once per signature (relation phrase, subject classes, object classes) and materializes typed assertions as a set operation that retires them when their support goes. A person's binding is final.
- **Mood.** A statement that carries a mood (required, conditional, planned, quoted, offered) is never materialized as a fact. It routes to normative, subjectivity, quote, or scenario structures.
- **Admission.** Every interpretation output passes structural admission checks before persistence: the quote is in the block, names are in their quote, and time words are in their quote. Offsets are computed by the server, and every refused item is a drop record with a reason.

Valid time comes from time mentions (ADR-0064):

- **The model interprets and code computes.** The model returns each mention's shape, reference (absolute, or anchored with an offset), and granularity. Code computes the interval against the document's time context: its own date from content or source metadata, its declared periods, its anchors, and its time-of-day and time-zone conventions. Upload and receipt times never date a document.
- **Unanchored mentions wait.** A mention whose anchor is unknown dates nothing until an anchor arrives.
- **Each bound stores its precision.** An ended fact whose end date is unknown is `UNKNOWN`, not open. A missing start reaches back only to the earliest attesting document.
- **Temporal kind.** Properties declare `STATE`, `EVENT`, or `ETERNAL`.
- **Succession.** A successor closes a predecessor only when its start is anchored (grade `A` or `B`), never on model confidence.

In the example above, the endorsement is attested by its own issue date. It is received June 12 and recorded when it is canonically accepted (section 109.2). These are three distinct times.

Evidence also records how its words were obtained: the block's `text_origin` (`STATED`, `OCR`, `TRANSCRIBED`, `DESCRIBED`) and its producing engine. Evidence that is only a model's description of a figure cannot supersede a canonical fact; it routes to review (ADR-0065). Time mentions, with their interpretation and resolution grade, are evidence for valid time (ADR-0064).

For profile sections on the alignment route (ADR-0063), an ontology or rule release does not re-read documents at all. It recomputes only the signatures and implication rules whose decision basis changed (ADR-0068) and re-materializes their typed assertions. Cost grows with distinct phrasings, not documents. A model is consulted only for signatures that must be decided again.

Names are time-bounded, evidenced assertions on `hasLegalName`, `hasTradeName`, `hasFormerName`, and `knownAs` (ADR-0066). A named-insured change by endorsement keeps the entity and dates each name. Name similarity, abbreviation, containment, and cross-script matches only propose pairs. A pair proposed by similarity is never merged on a batch model verdict alone. Automated merges are further held when their effects would leave what a revert can recall (ADR-0067).

Which derived facts are affected is decided by decision basis fingerprints: exact input fact versions, rule version, ontology release, and evaluator version. A comparison of timestamps is not used (ADR-0068).

Activities that dispatch external side effects follow ADR-0069:

- a request identity persisted before dispatch;
- a revision-bound preview;
- one dispatch grant;
- `OUTCOME_UNKNOWN` when the effect's fate is unknown;
- no automatic retry of the dispatch step unless the remote honours the attempt's idempotency key.

Internal idempotent recomputation may retry normally.

The gate's first concrete check is impact (ADR-0067). An automated change is held for a person, whatever its confidence, when its effects would leave what a revert can recall:

- a single-valued FactSlot conflict at one moment;
- a live derivation or assessment resting on it;
- a cited answer or decision;
- an export.

Approved actions then execute as action attempts (ADR-0069).

Automated deciders on any queue follow ADR-0067:

- **Precedent** comes only from human-actor decisions, with the reviewer's optional free-text reason.
- **Impact holds** are shown as reasons, not doubts.
- **Automated decisions** act through the same service paths as people and record their undo.
- **A revert fuse** turns an automation type off for a knowledge base.

Every automation type starts disabled until its agreement with human decisions is measured. v0.2 adds `SIGNATURE_ALIGNMENT` and `IMPLICATION_RULE` queues (ADR-0063), plus a `TIME_ANCHOR` queue for unanchored or conflicting document dates (ADR-0064).

## ADR-0063 to ADR-0069 — Statements, time, and governance (2026-09-25)

| ADR | Decision | Status |
|---|---|---|
| [ADR-0063](decisions/ADR-0063-open-statements-and-signature-alignment.md) | Open statements in the source's words; typed assertions from template extraction or per-signature alignment; implication rules | Accepted (direction); implementation proof gates open |
| [ADR-0064](decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) | Time mentions interpreted by the model and computed by code; document time context; precision; unknown bounds; temporal kind | Proposed |
| [ADR-0065](decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) | Structural admission checks and drop records; text origin; statement mood | Proposed |
| [ADR-0066](decisions/ADR-0066-names-are-time-bounded-claims.md) | Names are time-bounded, evidenced claims; similarity only proposes | Proposed |
| [ADR-0067](decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) | Automation held on unrecallable impact; human-only precedent; revert fuse | Proposed |
| [ADR-0068](decisions/ADR-0068-decision-basis-fingerprints.md) | Decision basis fingerprints define staleness | Proposed |
| [ADR-0069](decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) | External action attempts keep identity and uncertain outcome | Proposed |

assertion                       assertion_kind: OPEN_STATEMENT | TYPED_ASSERTION (ADR-0063)
assertion_qualifier             role-word qualifiers on open statements; includes mood (ADR-0065)
typed_assertion_source          open statements behind a materialized typed assertion (ADR-0063)
time_mention                    verbatim time expression, interpretation, computed interval, grade (ADR-0064)
document_time_context           per document version and run (ADR-0064)
interpretation_drop             refused / truncated / uninterpreted items with reason (ADR-0065)

kind_word_binding               (ADR-0063, F0066)
signature_binding               with decision basis (ADR-0063, ADR-0068)
implication_rule
implication_rule_version
phrase_reading
entity_alias                    search projection over name facts (ADR-0066)
automated_decision              action, confidence, precedents, trace, undo, status (ADR-0067)
automation_fuse                 per KB and automation type (ADR-0067)
action_definition               revisioned (ADR-0069)
action_attempt                  request identity, dispatch token, state (ADR-0069)

F0066 Open-statement extraction + signature alignment (ADR-0063)
38. Only typed assertions reach canonical resolution; open statements are kept whatever the ontology becomes, and alignment never writes a typed assertion without an open statement or approved rule behind it.
39. A statement that carries a mood is never materialized as a fact.
40. A model never computes a date; upload, sync, and receipt times never date a document.
41. An unknown end is not an open end, and a missing start is not "since always".
42. Every quote and name is located in its source by the server before admission; every refused item is a drop record.
43. Evidence that is only a model's description of a figure cannot supersede a canonical fact.
44. A rename does not create an entity; name similarity never merges on its own.
45. Automated changes whose effects would leave what a revert can recall are held for a person; only human decisions are precedent.
46. Cached decisions are stale when the fingerprint of their inputs changes, never by comparing timestamps; a person's decision is never overwritten by automation.
47. An external action whose outcome is unknown is never re-sent automatically.

## Statements, time, and automated governance (ADR-0063 to ADR-0069)

These definitions come from the 2026-09-25 architecture amendments, which were informed by Utopia's decisions since 2026-09-05. ADR-0063 is accepted as direction. ADR-0064 to ADR-0069 are Proposed. Worked and boundary examples: [statements, time, and governance](../examples/statements-time-and-governance.md).

| Term | Meaning in the Brain | Concrete example / boundary | Owning feature |
|---|---|---|---|
| Open statement | An assertion of kind `OPEN_STATEMENT` holding what a source says in its own words: a relation phrase, role-word qualifiers, time-mention references, a mandatory quote, and no predicate | EX-SEM-001: "subcontracts all tear-off work to"; never bound to a generic "related to" | F0006 (storage), F0066 (extraction) |
| Typed assertion | An assertion expressed in an ontology property, produced by template extraction or signature alignment and marked with its ontology release; only typed assertions reach canonical resolution | EX-SEM-001: `usesSubcontractor` materialized from the open statement | F0006/F0015/F0066 |
| Signature | The normalized relation phrase with the subject's class set and the object's class set (or `VALUE`); alignment decides each signature once per knowledge base and ontology release | EX-SEM-001; EX-SEM-010 when the class hierarchy changes | F0066 |
| Signature binding | The decision that a signature is a property in a direction, or `NONE`, or `UNDECIDED`, with its decision basis and decider; a person's binding is final | Two votes with candidates in opposite orders must agree | F0066 |
| Implication rule | An approved rule that a statement shape implies a typed assertion of another property, with the object read from a cached per-phrase reading; its results are `INFERRED` | EX-SEM-002: "a Texas limited liability company" implies the jurisdiction of formation | F0066 |
| Interpretation route | A document profile section's declared route to typed assertions: `TEMPLATE`, `OPEN`, or `TEMPLATE_AND_OPEN` | Declarations pages use `TEMPLATE`; broker correspondence uses `OPEN` | F0014 |
| Time mention | A verbatim time expression located in a block, with a model interpretation (shape, reference, granularity) and a code-computed interval and resolution grade | EX-SEM-003: "Effective as of 12:01 a.m. on July 1, 2026" | F0016 |
| Document time context | A document's own date and its source, the periods and calendars it defines, its narrative anchors, and its time-of-day/time-zone conventions; never upload or receipt time | EX-SEM-003b: "as of inception" waits without the policy period | F0004/F0016 |
| Resolution grade | `A` absolute, `B` anchored, `C` unanchored; only `A`/`B` starts may close a predecessor in a single-valued FactSlot | A grade-C successor opens review instead of closing | F0008/F0019 |
| Valid-time precision | The granularity stored on each valid-time bound, with values truncated to it | "July 2026" is month precision, not July 1 | F0008 |
| Unknown end | `valid_to_state = UNKNOWN` with `attested_to`: the fact ended, but the source gives no date; distinct from an open end | EX-SEM-004: "no longer on the account" | F0008 |
| Temporal kind | A property's declared `STATE`, `EVENT`, or `ETERNAL`, which normalizes writes and reads | A loss occurrence is an `EVENT`; a limit is a `STATE` | F0012/F0013 |
| Admission check | A server-side structural check on interpretation output before persistence: the quote is in the block, names are in their quote, time words are in their quote; offsets are computed by the server | EX-SEM-005b: a fabricated quote is dropped | F0006/F0016 |
| Interpretation drop | A persisted record of a rejected, malformed, truncated, or uninterpreted item with its reason code; drops make a run `PARTIAL` and feed `NOT_PROCESSED` | `QUOTE_NOT_IN_SOURCE`, `BLOCK_UNINTERPRETED` | F0016/F0022 |
| Text origin | How a block's words were obtained: `STATED`, `OCR`, `TRANSCRIBED`, or `DESCRIBED`; described-only evidence cannot supersede a fact | EX-SEM-006: a chart description versus the SOV table | F0004 |
| Statement mood | A qualifier holding the passage's own words when a statement is required, conditional, planned, quoted, or offered; mood-bearing statements are never materialized as facts | EX-SEM-007: "subject to receipt of a signed application" | F0006, F0052 |
| Name fact | A name held as a time-bounded, evidenced assertion on `hasLegalName`, `hasTradeName`, `hasFormerName`, or `knownAs`; a rename keeps the entity | EX-SEM-008: named-insured change by endorsement | F0007/F0017 |
| Impact hold | Holding an automated change for a person because its effects would leave what a revert can recall (`CONFLICT`, `DERIVED`, `CITED`, `EXPORTED`) | EX-SEM-009: a merge an assessment rests on | F0027/F0043/F0059 |
| Precedent | A human-actor review decision, with its optional free-text reason, that automated deciders may read; an agent's own decisions are never precedent | A person's "keep apart" blocks an automatic merge of the same pair | F0043 |
| Automation fuse | The per-knowledge-base automatic disabling of an automation type after a configured number of reverts within a window | Default: two reverts in seven days | F0043 |
| Decision basis | A fingerprint of every input a cached decision considered; the decision is stale when the fingerprint of current inputs differs | EX-SEM-010: a changed ancestor closure reopens a binding | F0016/F0032/F0056/F0066 |
| Action attempt | A persisted external side-effect attempt with a request identity and the states `PREPARED`, `DISPATCHING`, `NOT_SENT`, `RESPONSE_RECEIVED`, or `OUTCOME_UNKNOWN`; never retried blindly | EX-SEM-011: a worker dies after sending | F0050/F0059 |
| Open statements, typed assertions, signature alignment, implication rules | [EX-SEM-001/002](statements-time-and-governance.md#open-statements-and-alignment) | F0006 storage, v0.1A; F0066 alignment, v0.2B; ADR-0063 |
| Time mentions, document time context, resolution grade, precision, unknown ends, temporal kind | [EX-SEM-003/004](statements-time-and-governance.md#time-interpretation) | F0004/F0008/F0016/F0019/F0025, v0.1; ADR-0064 |
| Admission checks, drops, text origin, statement mood | [EX-SEM-005–007](statements-time-and-governance.md#admission-origin-and-mood) | F0004/F0006/F0016/F0022, v0.1; F0052 routing, v0.3; ADR-0065 |
| Names as time-bounded claims; similarity only proposes | [EX-SEM-008](statements-time-and-governance.md#names) | F0007/F0017, v0.1A; F0027, v0.2B; ADR-0066 |
| Impact holds, human precedent, automation fuse | [EX-SEM-009](statements-time-and-governance.md#automation-and-impact) | F0027/F0043, v0.2B; F0059, v0.4+; ADR-0067 |
| Decision basis fingerprints and staleness | [EX-SEM-010](statements-time-and-governance.md#decision-basis) | F0016/F0066/F0032, v0.1–v0.2B; F0056, v0.4+; ADR-0068 |
| External action attempts and uncertain outcomes | [EX-SEM-011](statements-time-and-governance.md#action-attempts) | F0050, v0.3; F0059, v0.4+; ADR-0069 |
# Statements, time, and automated governance: semantic examples

**Status:** Every example below is synthetic and illustrative. No runtime execution, model output, or measured rate is claimed. The examples explain [ADR-0063](../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) to [ADR-0069](../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md). Where they fit, they reuse the continuing [EX-GL-001](neurosymbolic-gl/README.md) case.

The glossary has the definitions. The owning feature and delivery phase are shown on each example and in the [coverage map](README.md). These are development and documentation examples; they stay outside the frozen holdout.

## Open statements and alignment

**EX-SEM-001 — F0006 storage (v0.1A); F0066 alignment (v0.2B); ADR-0063.**

A broker email in the EX-GL-001 package says: *"Acme Roofing subcontracts all tear-off work to Dalton Crews LLC."*

Open interpretation stores one open statement:

- subject: Acme Roofing;
- phrase: "subcontracts all tear-off work to";
- object: Dalton Crews LLC;
- the verbatim quote, located by the admission service;
- no predicate.

Later, the ontology release defines `usesSubcontractor` with domain `Contractor` and range `Organization`. The kind words "roofing" and "LLC" are already bound to classes. Alignment then decides the signature ("subcontracts … to", `Contractor`, `Organization`) once:

- two votes, with candidates in opposite orders, both choose `usesSubcontractor`, forward;
- materialization writes one typed assertion with `typed_assertion_source` pointing at the statement;
- a second email with the same phrasing adds a source row, not a second assertion;
- no document is re-read.

**Boundary (EX-SEM-001b).** An underwriter's note says *"Acme may subcontract tear-off work next season."* That statement carries `mood = "may … next season"` and is never materialized.

A different boundary: if the ontology has no admissible property, the signature is recorded as `NONE`. The statement stays in the open layer and counts toward ontology suggestions. It is not bound to a generic "related to" property.

**EX-SEM-002 — F0066, v0.2B; ADR-0063 implication rules.**

A statement says *"Dalton Crews LLC, a Texas limited liability company …"*. An approved implication rule concludes `jurisdictionOfFormation`, taking the object from a cached reading of "Texas". The implied assertion carries `interpretation_basis = INFERRED`, the rule version, and the statement's evidence.

**Boundary.** "A Texas-based roofer" names a location, not a jurisdiction of formation. The reading must not be reused across different phrases. It is cached per distinct phrase, and "Texas-based" has its own reading, which says nothing about formation.

## Time interpretation

**EX-SEM-003 — F0016/F0019/F0025, v0.1; ADR-0064.**

The EX-GL-001 endorsement reads *"Effective as of 12:01 a.m. on July 1, 2026, the Each Occurrence limit is amended to $2,000,000."* The policy's time context holds:

- the policy period from 01/01/2026 to 01/01/2027;
- the policy's convention: 12:01 a.m. standard time at the address of the named insured.

The mention is interpreted as a `POINT`, reference `ABSOLUTE` "July 1, 2026", granularity `MINUTE`. Code applies the time-zone convention and computes the start. The resolution grade is `A`.

The document is attested by its issue date, taken from its content. Recorded time is canonical acceptance on July 10. Receipt on July 9 is a recorded-time-family fact, not the document date. The EX-GL-001 temporal walkthrough answers follow unchanged.

**Boundary (EX-SEM-003b).** A second endorsement says *"effective as of inception"*. Its reference is `ANCHORED` to the policy period's start. If that policy's declarations are not in the package, the anchor is unknown: the mention is grade `C`, the assertion carries no valid time, and a review item asks for the anchor. It must not take the upload date, or January 1 of the current year.

**EX-SEM-004 — F0008, v0.1A; ADR-0064 unknown bounds.**

A loss run *"valued as of 06/30/2026"* is an `AS_OF` attestation of the listed losses. It is not the validity interval of each loss. Each loss occurrence is an `EVENT` at its stated date and granularity.

A broker note dated 2026-08-02 says *"the prior carrier is no longer on the account"*. This ends the prior-carrier state with `valid_to_state = UNKNOWN` and `attested_to = 2026-08-02`.

**Boundary.** A query at 2026-07-15 must answer `UNKNOWN`, not "still held" and not "ended". A missing start date on the prior-carrier fact reaches back only to the earliest attesting document, never to negative infinity.

## Admission, origin, and mood

**EX-SEM-005 — F0006/F0016, v0.1A; ADR-0065 admission.**

The model returns the quote *"Each Occurrence Limit $500,000"*, but the declarations block reads *"EACH OCCURRENCE LIMIT $ 500,000"*. Normalization handles the case and whitespace difference. The server locates the quote, computes the offsets itself, and admits the assertion.

**Boundary (EX-SEM-005b).** Two failures look alike but are handled differently.

- **A fabricated quote.** The model returns the quote *"Each Occurrence Limit $5,000,000"*, which appears nowhere in the block. The item is dropped as `QUOTE_NOT_IN_SOURCE`, the drop row is written, and the run reports it.
- **A misread value (CASE-05 of EX-GL-001).** The model quotes the genuine $500,000 wording but emits the value 5,000,000. Admission checks that the quote is present, not that the value was read correctly, so the assertion is admitted and reaches review, where the reviewer corrects it.

Admission refuses evidence that does not exist. It does not replace review.

**EX-SEM-006 — F0004/F0022, v0.1; ADR-0065 text origin.**

An SOV attachment includes a bar chart of building values. Docling produces a `DESCRIBED` block, and the model reads the tallest bar as $5.2M for Building 3. The SOV table, a `STATED` source, says $2.5M.

The described assertion opens a review item with reason `DESCRIBED_EVIDENCE`. It cannot supersede the stated value.

**Boundary.** An OCR block from a scanned declarations page is admissible evidence at its declared precision. OCR is not treated like a description.

**EX-SEM-007 — F0006 (v0.1A); routing to F0052 (v0.3); ADR-0065 mood.**

A binder says *"Binding is subject to receipt of a signed and dated application within 10 days."* The statement carries `mood = "subject to"` and becomes a subjectivity candidate. The Brain does not assert that the application was received.

**Boundary.** An issued policy's condition *"This insurance does not apply unless the insured maintains automatic sprinklers"* is an operative provision. It is asserted as a fact about the policy: the policy has that condition. The embedded content, that the insured maintains sprinklers, is not asserted as a fact about the insured's premises.

## Names

**EX-SEM-008 — F0007/F0017, v0.1A; F0027, v0.2B; ADR-0066.**

The declarations name *"Acme Roofing Inc."* with FEIN 12-3456789. An endorsement effective 2026-09-01 amends the named insured to *"Acme Roofing & Restoration Inc."*, with the same FEIN.

- `hasLegalName` records the first name valid until September 1 and the second from September 1.
- The entity is unchanged.
- "Who was the named insured on August 15?" returns the first name, with its evidence.

**Boundary.** A loss run lists *"Acme Roofing"* with no FEIN, and another account in the tenant is *"Acme Roofing Supply LLC"*.

- Name similarity proposes pairs and merges nothing.
- A batch model verdict of "same" is not applied without a second look that reads both entities' evidence.
- "The named insured" in a letter is a role pointing at an entity. It is not a name fact.

## Automation and impact

**EX-SEM-009 — F0027/F0043, v0.2B; F0059, v0.4+; ADR-0067.**

With automated merging enabled, the resolver is 0.97 confident that two coverage-holder entities are one. The F0065 assessment EX-ASSESS-001 rests on one of them. The merge is held for a person as `IMPACT_HOLD:DERIVED 1 assessment`, and the card says why. A different merge with nothing downstream applies automatically, and can be reverted from the queue.

**Boundary.** A person earlier kept "Acme Roofing" and "Acme Roofing Supply" apart and wrote a reason: "different FEINs on the ACORD". That decision is precedent and blocks an automatic merge verdict on the same pair. The resolver's own earlier verdicts are never precedent.

When two automatic merges are reverted within seven days, automated merging turns itself off for that knowledge base and raises an alert.

## Decision basis

**EX-SEM-010 — F0066/F0032, v0.2B; F0056, v0.4+; ADR-0068.**

The signature ("subcontracts … to", `Contractor`, `Organization`) was bound when `usesSubcontractor` was declared on `Organization`. A later release moves the property's domain to a new parent class `LegalEntity`, and `Contractor` is made a subclass of it. The ancestor closure changes, so the stored basis no longer matches and the signature is reconsidered. Nothing compares timestamps.

**Boundary.** Relabelling the property's display name does not change the basis, so no work is queued. A person's binding on another signature shows "inputs changed since decision" after a relevant edit, and is never overwritten by the aligner.

## Action attempts

**EX-SEM-011 — F0050, v0.3; F0059, v0.4+; ADR-0069.**

An approved agent action requests an endorsement in the policy administration system. The attempt is `PREPARED` with `execution_request_id` R-17, then `DISPATCHING`. The worker dies after sending, and before the response is stored. Recovery finds `DISPATCHING`, marks it `OUTCOME_UNKNOWN`, and does not send again. A person checks the remote system.

**Boundary.** A Temporal activity replay of the same step must not re-send R-17. A later 200 response carrying R-17's dispatch token updates the attempt to `RESPONSE_RECEIVED`. Any new endorsement data it carries enters as a `SYSTEM_OBSERVATION` assertion; it is never written into canonical state directly.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Store the document's own date with its source (`CONTENT`, `SOURCE_METADATA`, `HUMAN`). Upload, sync, and receipt times are recorded-time facts and never a document date (ADR-0064).
- Content blocks carry `text_origin` (`STATED`, `OCR`, `TRANSCRIBED`, `DESCRIBED`), the producing engine/model/version, and an origin-specific anchor. A block never mixes origins (ADR-0065).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Persist both assertion kinds: `OPEN_STATEMENT` (subject, source relation phrase, object or literal, role-word qualifiers, time-mention references, mandatory quote, nullable predicate) and `TYPED_ASSERTION` (ontology property and release). v0.1 acceptance runs on the template route; open extraction and alignment ship in F0066 (ADR-0063).
- Define the admission service contract: quote-in-block, name-in-quote, time-words-in-quote, and name-claimed-by-another checks; server-computed selectors; drop reasons (ADR-0065).
- Add the `mood` qualifier. Mood-bearing statements are never eligible for canonical facts; an issued policy's operative provisions remain contract facts (ADR-0065, EX-SEM-007).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Define the name FactSlots: `hasLegalName` (single-valued per valid time), `hasTradeName`, `hasFormerName`, and `knownAs` (multi-valued). An entity's display name is selected from its current name facts (ADR-0066, EX-SEM-008).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Store per-bound granularity, `valid_to_state` (`OPEN`, `BOUNDED`, `UNKNOWN`), and `attested_from`/`attested_to`. Settle how `UNKNOWN` ends are represented inside the ADR-0008 exclusion constraint; the recommended option is in ADR-0064. Reads distinguish unknown from open and never widen a missing start to negative infinity.
- A successor closes a predecessor in a single-valued slot only when its start is grade `A` or `B`, never on model confidence.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Every ontology property declares `temporal_kind` (`STATE`, `EVENT`, `ETERNAL`) (ADR-0064).
- Properties and classes carry a definition, examples, and regression cases, which alignment and the workbench rely on (ADR-0063).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Declare `temporal_kind` on every GL property, and declare the name properties and name kinds (ADR-0064, ADR-0066).
- Model policy-period time-of-day and time-zone conventions so that documents can declare them in their time context.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Each document profile section declares `interpretation_route` (`TEMPLATE`, `OPEN`, `TEMPLATE_AND_OPEN`). v0.1 GL profiles use `TEMPLATE`; `OPEN` is activated per profile only after F0066's parity gate (ADR-0063).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Template fields remain typed assertions on the template route. Every field that claims span precision passes the admission checks; a field that cannot be located declares coarser precision or `unresolved` (ADR-0065).
- Never place the ontology in an open-extraction prompt. The compiler serves only the template route (ADR-0063).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record time mentions with their model interpretation, the code-computed interval, and the resolution grade, plus the document time context used by the run. Unanchored mentions date nothing and are re-resolved when an anchor arrives (ADR-0064).
- Persist interpretation drops by reason. A run with `BLOCK_UNINTERPRETED` or `TRUNCATED_OUTPUT` is `PARTIAL`; affected fields answer `NOT_PROCESSED` (ADR-0065).
- Store a `basis_hash` over everything the run considered (ADR-0068).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Resolve on identifiers first. An exact name match without an identifier creates a review pair and never merges. A name held by another compatible entity creates a shared-name pair. Roles such as "the named insured" point at entities and are not names (ADR-0066).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Take endorsement effective dates from time mentions resolved against the policy period and its time-of-day convention. "Effective as of inception" without a known policy period is grade `C` and opens review (EX-SEM-003b).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Show a time mention's words beside its resolved interval and grade, and let an authorized reviewer set a document's date, which triggers re-resolution without re-parsing (ADR-0064).
- Show interpretation drops per document, separately from review items, and show text origin beside evidence. `DESCRIBED`-only evidence arrives as a `DESCRIBED_EVIDENCE` review item (ADR-0065).
- Capture an optional free-text `why` beside reason codes on every decision; it becomes precedent for automation (ADR-0067).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- List an entity's names with their kind, sources, and validity; answer the legal name as of a valid time (ADR-0066).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Prove the endorsement timeline with valid time taken from resolved time mentions, attestation from the endorsement's own date, and recorded time from canonical acceptance. Receipt time never dates the document (ADR-0064, EX-SEM-003).
- Include a grade-C "as of inception" case and an unknown-end case.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md), [ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Report the open-statement not-stated and misworded rates with a calibrated judge, the judge's own variance, and run-to-run spread over at least two runs per configuration (ADR-0063).
- Report time normalization accuracy per shape and grade against thresholds set with named reviewers; proposed starting points are 95% for absolute and 85% for anchored mentions (ADR-0064).
- Report drop rates by reason and the described-evidence review count (ADR-0065). Report name-resolution precision and recall in both arrival orders (ADR-0066).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Name-vector, abbreviation, containment, and cross-script matches only propose pairs. A pair proposed by similarity is never merged on a batch model verdict alone (ADR-0066).
- Automated merges pass the impact hold, read only human precedent, record their undo, and respect the revert fuse. Automation is off by default (ADR-0067).
- Key verdict caches on a basis that includes both profiles and the precedent set (ADR-0068).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Frequent unbound signatures and kind words in use from the open layer are inputs to ontology discovery (ADR-0063).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Approved ontology elements carry a definition, examples, and regression cases drawn from open statements. A definition change reruns its cases, and releases record the structure alignment depends on: hierarchy, equivalences, domains, ranges (ADR-0063).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- On the alignment route, recompute only signatures and implication rules whose basis changed; re-read no documents. On the template route, keep targeted block reinterpretation (ADR-0063, ADR-0068).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record which entities and canonical facts each answer turn cited, so that the impact hold's `CITED` check is computable (ADR-0067).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Add `SIGNATURE_ALIGNMENT`, `IMPLICATION_RULE`, and `TIME_ANCHOR` queues (ADR-0063, ADR-0064).
- Automated deciders on any queue follow ADR-0067: human-only precedent, impact holds shown as reasons, the people's service paths with a recorded undo, and a revert fuse. Every automation type starts disabled until its agreement with human decisions is measured.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Future mutation tools execute through action attempts; read-only tools are unaffected (ADR-0069).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Activities that dispatch external side effects use the action-attempt state machine and do not automatically retry the dispatch step, unless the remote honours the attempt's idempotency key (ADR-0069).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Receive mood-routed statements (obligations, requirements, subjectivities) as normative-constraint candidates (ADR-0065, EX-SEM-007).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Find the derived facts and assessments to invalidate by decision-basis fingerprint, never by timestamp comparison (ADR-0068).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record which entities and facts a decision cited, so that the impact hold's `CITED` check is computable (ADR-0067).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md), [ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- The impact hold is the gate's first concrete check; approved actions execute as action attempts (ADR-0067, ADR-0069).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Assessment records add a `basis_hash` over their exact inputs, rule version, ontology release, and evaluator version. This refines existing lineage and does not change the approved outcomes (ADR-0068).
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
**Next Available Feature Number:** F0067
| F0066 | Open-statement extraction + signature alignment | Planned | v0.2B | `F0066-open-statement-extraction-and-signature-alignment/` |
**Last Reviewed:** 2026-09-25 (F0066 added under ADR-0063; statements, time, and governance scope amendments recorded in feature READMEs); previously 2026-09-07 (v0.1 bounded assessment scope amendment)
| [F0066 — Open-statement extraction + signature alignment](./F0066-open-statement-extraction-and-signature-alignment/README.md) | Planned | ADR-0063 (accepted direction): extract narrative sources as open statements in their own words, then bind them to the ontology once per signature, with implication rules and set-exact materialization of typed assertions. Placed after the F0030/F0031 workbenches and before the F0032 evolution engine, which recomputes per signature. |

## Statements, time, and governance measurements (ADR-0063 to ADR-0069)

- **Measure noise before claiming an improvement.** Any extraction or alignment comparison reports at least two runs per configuration and the judge model's own variance on repeated judgement. The judge is calibrated against a hand-labelled set, and its agreement is stated. A difference smaller than the combined spread is not an improvement.
- **Do not use F1 against a gold set known to omit true facts.** Report judged precision and gold recall separately (ADR-0063).
- **Open statements (ADR-0063):** not-stated rate (target ≤ 2%) and misworded rate on the narrative slice; tokens per document. **Typed assertions per profile:** judged precision and recall against the template route on the same documents before `OPEN` activation.
- **Time (ADR-0064):** normalization accuracy per shape and resolution grade (proposed starting thresholds 95% absolute, 85% anchored); valid-time correctness on the endorsement timeline; grade-C and unknown-end handling.
- **Admission (ADR-0065):** drop rates by reason, `BLOCK_UNINTERPRETED` and truncation counts, and described-evidence review items. Fabricated-quote fixtures are refused and misread-value fixtures reach review (EX-SEM-005b).
- **Names and identity (ADR-0066, ADR-0067):** pairwise precision and recall of same-entity decisions in both arrival orders, with the difference reported; wrong merges and missed merges separately. Before enabling any automation: agreement with human decisions, share decided automatically, revert rate.
- **Regression cases (section 98):** fiscal and 52/53-week periods; time-zone and time-of-day conventions; "as of inception"; subjectivities and quote-versus-bound; chart-description contradictions; named-insured change by endorsement; basis changes through the class hierarchy; external-action crash windows.

