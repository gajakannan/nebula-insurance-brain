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
