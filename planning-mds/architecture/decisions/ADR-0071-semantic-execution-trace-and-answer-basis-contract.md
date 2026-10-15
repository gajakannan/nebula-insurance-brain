# ADR-0071: Semantic Execution Trace and Answer-Basis Contract

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-10-13
**Direction authorized by:** Operator, 2026-10-13, in the Graph Observatory design review: the trace contract is carried into the features that execute answers and learning, and a scoped Observatory feature (F0067) lands later. On 2026-10-13 the operator also made the direction binding on the carry-in features now: their PRDs take the carry-in requirements as acceptance criteria rather than guidance. Formal acceptance still waits for the proof gates below.
**Would refine:** [ADR-0046](ADR-0046-grounded-answer-and-analytic-query-contract.md) (the grounded answer's references become the only source of "used in answer"), [ADR-0010](ADR-0010-provenance-is-mandatory.md) (provenance of an answer, not only of a fact).
**Related:** [ADR-0072](ADR-0072-observatory-is-a-read-only-projection.md) (who may read traces and how learning traces are built), [ADR-0032](ADR-0032-decision-replay-uses-recorded-time-state.md), [ADR-0053](ADR-0053-permission-safe-retrieval-and-historical-access.md), [ADR-0063](ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0019](ADR-0019-conversation-knowledge-is-not-canonical-by-default.md), [ADR-0020](ADR-0020-learning-plane-is-separate-from-canonical-truth.md).
**Source:** [Graph Observatory design note](../graph-observatory-design.md) sections 2, 5 and 6; master blueprint sections 44, 113 and line "Explanations should expose stored evidence, rules, calculations, and decision reasons, without relying on private model reasoning traces".

## Context

Users will ask the Brain questions about documents and entities (F0036, F0038, F0039), and administrators will watch the Brain interpret and learn (F0016, F0041, F0042). Both groups need to see what the Brain actually did: which evidence it retrieved, which graph relationships it followed, which fact version it selected for a valid time, which conflicts it found, and what the answer rests on.

Three failure modes recur in systems that try this:

1. **Visited becomes used.** Everything the retriever or traversal touched is shown as support for the answer. A superseded limit that was read and rejected looks like evidence.
2. **Gaps get filled in.** Where a model step was not recorded, the display draws plausible intermediate hops. The picture then shows reasoning that never happened.
3. **Instrumentation is retrofitted.** If answer and learning features ship first and are instrumented later, the trace reflects whatever was easy to hook, not the operations that matter.

ADR-0046 already requires every grounded answer to carry scope, time basis, evidence references and abstention. This ADR defines the execution record around that answer, so that the record and the answer cannot disagree.

## Proposed Decision

### 1. A trace is ordered facts about one execution

A **semantic execution trace** records one execution: a conversation turn, a semantic query, an interpretation run or a learning run. It has three parts, kept separate:

- the **trace summary**: identity, operation, status, completeness and the semantic context used (ontology release, graph projection, valid-as-of and known-as-of coordinates);
- the **graph projection** it refers to: the bounded, authorized nodes and clusters the events name, with permission-safe aggregate counts;
- the **events**: ordered, typed, sanitized facts at operation boundaries.

Presentation state (camera, replay cursor, layout, colours, stage grouping) is never part of the trace. The draft shape is [`semantic-execution-trace.schema.json`](../../schemas/semantic-execution-trace.schema.json).

### 2. Four attribution classes, and only the answer decides "used"

| Class | Meaning | Where it comes from |
|---|---|---|
| **Observed** | The operation ran and was recorded. | Any event at an instrumented boundary. |
| **Used in answer** | A node or edge is part of the answer's basis. | Only the `ANSWER_BASIS_LINKED` event, built from the grounded answer's own evidence and derivation references (ADR-0046). |
| **Considered, not used** | Retrieved, traversed or evaluated, then not part of the basis. | Listed explicitly in the same basis event. Never inferred by subtraction in the client. |
| **Not instrumented** | An operation ran but its inside was not recorded. | An `INSTRUMENTATION_GAP` event with a reason code. |

Proximity, traversal, retrieval rank and animation never make a node "used". Until the basis event exists, nothing is "used".

### 3. Gaps are disclosed, never reconstructed

- Model internals are not recorded and are not drawn. Where a language model composes an answer, the trace records the call boundary, its structured output and its citations, and an explicit gap for the rest. **Hidden chain-of-thought is never captured or displayed.**
- A trace that ends early, is truncated, or loses events records that in `completeness`. A consumer must show partial and failed traces as such.
- A trace never claims a commit, release or projection update that the authoritative record does not show (see ADR-0072 for learning traces).

### 4. Ordering, spans and time

- `sequence` orders events within one trace. Timestamps are not an ordering guarantee.
- `span_id` and `parent_span_id` record parallel and nested operations. A flat timeline is a view, not evidence of serial execution.
- The trace summary records the ontology release, graph projection, valid-as-of and known-as-of coordinates the execution used (ADR-0007, ADR-0064). Replay of an old trace uses those coordinates, never the current graph silently. If a historical projection is unavailable, the replay says so (ADR-0032).

### 5. Recording rules

- Events are recorded at operation boundaries, not per token or frame.
- Recording is non-blocking: a failure to record never fails the answer or the run. It becomes a completeness state.
- Events carry identifiers, version references and sanitized summaries. They never carry prompts, model responses, evidence excerpts, credentials or personal data. Evidence is fetched through the existing authorized evidence APIs (ADR-0058).
- Operational telemetry (OpenTelemetry-compatible `trace_id` in logs, per SOLUTION-PATTERNS) and the semantic trace share correlation identifiers but are separate records. Generic telemetry exporters never receive semantic payloads.
- Read-path traces (answers and queries) are stored in a bounded-retention trace store in PostgreSQL. Retention defaults to **90 days** and is configurable per tenant (operator, 2026-10-13). A trace whose answer is cited by a recorded decision is kept with that decision instead of expiring (F0058). Learning traces are projected from authoritative records, not stored as a second copy (ADR-0072).

### 6. Invariants a validator checks

JSON Schema enforces the event shape, the attribution and event-type pairings, and the authoritative-record requirement for learning events. A contract validator additionally checks:

1. `sequence` is strictly increasing and every event's `trace_id` matches the summary.
2. Every node or edge an event names exists in the trace's projection.
3. `used_node_ids` and `considered_not_used_node_ids` do not overlap, every answer span's basis is in `used_node_ids`, and every classified node was observed by an earlier event.
4. `completeness.gap_count` equals the number of gap events and `recorded_events` equals the event count.
5. A synthetic trace is labelled as synthetic wherever it is rendered.

## Consequences

- **F0036 / F0038 / F0039** emit the answer-basis event from the grounded answer and record retrieval, traversal, temporal selection, evidence and conflict boundaries. Their PRDs carry this as acceptance criteria.
- **F0038** stands up the read-path trace store and ships the first **How the Brain answered** panel early (operator, 2026-10-13); F0067 extends it.
- **F0037** owns the call-boundary and gap events for model and tool calls.
- **F0016 / F0041 / F0042** keep the records that learning traces are projected from (ADR-0072).
- **F0034 / F0020** expose a projection identifier, so a trace can name the projection it used.
- **F0058** reuses the same replay coordinates for historical decision replay.
- **F0067** (Graph Observatory) renders traces. It cannot exist without the records above, so it is sequenced after them.
- The [options page](../../examples/graph-observatory-2d-options.html) holds two synthetic fixtures (EX-OBS-001 answer trace, EX-OBS-002 learning run) that pass the draft schema and the invariants in section 6.

## Proof gates

Before acceptance:

1. F0036 or F0038 Phase B binds the schema (or a successor) to a real endpoint and story, with the answer-basis event produced from the ADR-0046 answer object, not from the trace.
2. A test shows a traversed but superseded fact classified as "considered, not used", and a retrieval candidate never promoted to "used" by rank or proximity.
3. A test injects a recording failure and shows the answer still returned, with the trace marked partial.
4. The section 6 validator runs in CI over the example fixtures and over at least one recorded trace from a real execution.
5. Security review confirms no prompt, response, excerpt or personal data reaches the trace store or telemetry exporters.

## References

- [Graph Observatory design note](../graph-observatory-design.md)
- [Rendering options page and fixtures EX-OBS-001/002](../../examples/graph-observatory-2d-options.html)
- [Draft schema](../../schemas/semantic-execution-trace.schema.json)
- Master blueprint sections 44 and 113 (grounded answers)
