# ADR-0072: The Observatory Is a Read-Only Projection

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-10-13
**Direction authorized by:** Operator, 2026-10-13, in the Graph Observatory design review (read-only administration, replay on demand, real recorded operations only). On 2026-10-13 the operator also made the direction binding on the carry-in features now: their PRDs take the carry-in requirements as acceptance criteria rather than guidance. Formal acceptance still waits for the proof gates below.
**Would refine:** [ADR-0053](ADR-0053-permission-safe-retrieval-and-historical-access.md) (trace replay is a historical read and follows its rule), [ADR-0020](ADR-0020-learning-plane-is-separate-from-canonical-truth.md) (learning outcomes are observable without becoming canonical).
**Related:** [ADR-0071](ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (the trace contract), [ADR-0062](ADR-0062-current-authorization-and-durable-decisions.md), [ADR-0032](ADR-0032-decision-replay-uses-recorded-time-state.md), [ADR-0036](ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md), [ADR-0022](ADR-0022-apache-age-is-the-graph-projection.md), [ADR-0069](ADR-0069-action-attempts-and-uncertain-outcomes.md).
**Source:** [Graph Observatory design note](../graph-observatory-design.md) sections 1, 3 and 8.

## Context

The Graph Observatory (F0067) shows answer traces to knowledge workers and learning traces to administrators. Two risks shape its boundary.

**A second source of truth.** The Brain already keeps durable records of what interpretation and learning did: interpretation runs (F0016, ADR-0060), open statements and alignment decisions (ADR-0063), entity-resolution verdicts (F0017), conflict and supersession records (F0019, F0028), learning candidates (F0041), review items and decisions (F0042, F0043), canonical commits (F0018), ontology releases (ADR-0045) and audit events (ADR-0062). If the Observatory emitted its own parallel event stream for these, the two would drift, and the picture could show a commit that never happened or miss one that did.

**Leaking through the picture.** A graph can disclose what a list never would: that a neighbour exists, how many there are, how two parties connect. Trace replay is also a historical read, so it could show something the viewer was allowed to see then but not now.

## Proposed Decision

### 1. Read-only

The Observatory issues only reads. It cannot approve, reject, edit, promote, commit or publish anything, and it holds no state beyond local view state. It deep-links to the authoritative workbench (review queues, ontology workbench, commit history) for any action.

### 2. Learning traces are projections over authoritative records

- A learning, governance or commit event in a trace is **derived from the durable record that already exists**, and cites it (`authoritative_record_ref`). There is no separate learning-event emitter.
- A commit appears only if the commit record exists. A proposal appears as a proposal. A run that changed nothing canonical shows zero canonical changes as an outcome, not an error.
- Projection catch-up is shown separately from commit (a projection can lag a commit).
- The projection is rebuilt from records, so it can be regenerated, and a missing record shows as a gap, never as an invented step.

Read-path traces (answers and queries) have no other durable record of their internal steps, so they are recorded directly under ADR-0071.

### 3. Authorization on every expansion

- **Trace access follows answer access** (operator, 2026-10-13). Anyone who may read an answer may read its trace, including a knowledge worker viewing a colleague's answers and decisions. There is no separate trace permission. The rules below still apply inside the trace.
- Every trace read, page of events, projection fetch and evidence expansion is authorized server side under ADR-0062. Authorizing the trace summary does not authorize what it names.
- **Existence is filtered, not hidden.** Nodes, edges, cluster labels and counts outside the viewer's scope are removed before the response, not drawn as anonymous or ghost nodes. Aggregate counts are computed within the viewer's scope.
- **Replay never reinstates access.** A replayed trace shows what the viewer may see now, intersected with what the execution saw then (ADR-0053). Content the viewer has since lost access to is withheld and the replay says that something was withheld only where disclosure of that fact is itself permitted.
- `trace_id` is opaque. Tenant and principal come from the server's authenticated context, never from client-supplied identifiers.

### 4. Synthetic content is always labelled

Fixtures, demos and design prototypes carry `synthetic: true` and are visibly marked wherever rendered. Missing backend capability is never filled with mock production traces.

### 5. Rendering is replaceable

Renderers consume the same trace contract and keep no semantics of their own. The baseline is a 2D rendering plus an accessible event list. Whether a 3D renderer is added is a product decision recorded in F0067. If one is added, depth must encode something recorded (for example knowledge layer or time) or be declared decorative, and it must not be the only way to read a trace.

## Consequences

- **F0016, F0017, F0019, F0028, F0041, F0042, F0043** keep the records named above queryable by run, with terminal status. No feature emits Observatory-only events for these.
- **F0067** builds the projection layer and read APIs under this boundary, and depends on those features.
- **F0045** (Cytoscape Graph Explorer) and F0067 share the visual vocabulary for layers and attribution.
- **F0021** provides the route, feature flag and lazy-loading seam; F0067 adds its rendering dependencies through the normal dependency policy.
- The [options page](../../examples/graph-observatory-2d-options.html) compares three 2D renderings, a 2.5D depth reference and a true 3D (WebGL) rendering whose height encodes the knowledge layer, against the same synthetic traces. The 3D decision is taken from that review.

## Proof gates

Before acceptance:

1. F0067 Phase B shows a learning trace built only from authoritative records, and a test where deleting the projection and rebuilding it yields the same trace.
2. A security test shows no unauthorized node, edge, label or count in any projection or expansion, including after a grant is revoked between execution and replay.
3. A test shows no Observatory endpoint accepts a write or a governance action.
4. A run with zero canonical changes, one with an unresolved conflict and one with a governed commit are each explained correctly from records alone.

## References

- [Graph Observatory design note](../graph-observatory-design.md)
- [Rendering options page](../../examples/graph-observatory-2d-options.html)
- [ADR-0071](ADR-0071-semantic-execution-trace-and-answer-basis-contract.md)
