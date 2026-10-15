# Graph Observatory: Design Note

**Date:** 2026-10-13 (revised the same day after operator review)
**Status:** Design note. Decisions it needs are in proposed [ADR-0071](decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) and [ADR-0072](decisions/ADR-0072-observatory-is-a-read-only-projection.md); the scoped feature is [F0067](../features/F0067-graph-observatory/README.md) (v0.2B). This note is not itself a repository decision.
**Audience:** Product management, architecture, AI/semantic engineering, frontend engineering, information governance, and QA

## Review outcome (2026-10-13)

The operator reviewed the first draft and set the delivery shape:

1. **A design feature, delivered in two moves.** The trace contract and its recording obligations are carried into the features that execute answers and learning now, as PRD inputs. A fully scoped Observatory feature, F0067, lands in v0.2B once those features exist. The draft's Slice 0 to 3 plan is replaced by section 10.
2. **Trace contract.** Proposed [ADR-0071](decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) with a draft [schema](../schemas/semantic-execution-trace.schema.json).
3. **Read-only boundary.** Proposed [ADR-0072](decisions/ADR-0072-observatory-is-a-read-only-projection.md). Learning traces are projected from the records the Brain already keeps (interpretation runs, alignment decisions, resolution verdicts, candidates, review items, commits, audit events), not emitted as a parallel stream. Only read-path traces (answers, queries) are recorded directly.
4. **3D is wanted where it earns its place, decided after reviewing 2D alternatives.** The [rendering options page](../examples/graph-observatory-2d-options.html) draws the same two synthetic traces five ways: A nebula 2D, B layer lanes, C basis path, D 2.5D depth reference, and E true 3D (WebGL), where height is the knowledge layer. F0067 records the choice.

Corrections from the review, applied below:

- The answer basis comes from the grounded answer itself (ADR-0046), so there is no separate answer-basis table.
- Trace replay is a historical read: it shows what the viewer may see now, intersected with what the execution saw (ADR-0053).
- App-wide frontend libraries (state, query cache, styling) are F0021's decision. F0067 adds only rendering dependencies.
- 2D inspection reuses F0045's Cytoscape explorer.
- Conversation hypotheses (ADR-0019, F0040) are their own layer in the visual vocabulary.
- Rule-evaluation events wait for F0055 (v0.4+). Until then, v0.2 traces show ontology terms and temporal selection, not rule firing.

> **Design thesis:** Make the Brain's recorded retrieval, knowledge-graph traversal, ontology application, evidence evaluation, and learning outcomes inspectable. The animation is a replayable rendering of facts about an execution, never a fictional reconstruction of invisible model thought.

## Executive summary

**Graph Observatory** is an integrated visualization capability for two related Insurance Brain experiences:

1. **Chat with Document — Answer Trace:** A knowledge worker asks a question about a document (or an associated entity). The answer remains the primary result. A collapsible **How the Brain answered** panel opens a recorded, step-by-step graph trace showing what evidence and semantic relationships were actually used, which operations ran, where the answer came from, and what could not be established.
2. **Learning Observatory — Administrator view:** An authorized administrator observes how newly provided information passes through existing extraction, assertion, alignment, entity resolution, conflict detection, ontology checks, and governed knowledge-change mechanisms. It is **read-only**: it does not approve, reject, edit, or publish ontology or graph changes.

These share an event vocabulary, projection API, timeline/replay infrastructure, and visual language. The implementation is **incremental**, with bounded General Liability (GL) document and endorsement scenarios before broader learning observability. **Replay is on demand**, rather than automatic, continuous theatrical playback. The design is instrumentation-first: **only real recorded backend operations** may be displayed as execution facts.

A 21-second reference video (a third-party prompt-builder demo, kept locally and not committed) informs the presentation: point-cloud clusters, a "crawler" focus with tentacles reaching recorded nodes, boxed labels, stage tabs, camera pan and zoom, and a HUD of logs, progress bars and gauges. Frame review shows the scene is essentially a 2D field with camera motion, not a 3D graph. Those effects become meaningful only when mapped to evidenced operations. There is no claim that the visual depicts transformer attention or an LLM's unobservable internal reasoning.

### Product decisions fixed for this proposal

| Decision | Chosen direction | Consequence |
|---|---|---|
| Dashboard prominence | Integrated dashboard | Chat/answer primary; graph secondary and expandable |
| Rendering | 3D where it adds meaning, always alongside an accessible 2D view; pending the options review | Decided in F0067 from the [options page](../examples/graph-observatory-2d-options.html) |
| Truthfulness | Actual recorded operations only | No synthetic graph traversal or invented causal steps in production |
| Administration | Read-only observability | Governance and approvals remain in existing/future dedicated workbenches |
| Playback | Replay on demand | Execution finishes independently; open trace and replay afterwards |
| Delivery | Contract carried into existing features now and binding on them; early answer panel with F0038; F0067 in v0.2B | See section 10 |
| Trace access | Follows answer access; knowledge workers can see colleagues' answers and traces | ADR-0072 section 3 |
| Retention | Read-path traces 90 days by default, configurable per tenant; kept with a decision that cites the answer | ADR-0071 section 5 |

### Explicit non-goals

- An autonomous ontology editor or approval console.
- A replacement for semantic APIs, the canonical store, the assertion plane, or an agent orchestration engine.
- An always-running live telemetry wall, unrelated to a specific user-visible investigation.
- A second record of learning outcomes alongside the authoritative records (ADR-0072).
- A claim to display neural attention weights, private chain-of-thought, or undocumented model reasoning.
- A 3D renderer for the whole enterprise graph, or a requirement that all graph exploration occur in 3D.
- Expensive re-extraction of source documents to generate visualization frames.

## 1. Fit within Insurance Brain

The repository's `planning-mds/BLUEPRINT.md` is the process/scope authority; `planning-mds/architecture/master-blueprint.md` is the architecture baseline until resolved by ADR. This proposal must enter through the repository's **PM / Architect / Implementation** process and tracking checks rather than being committed as a new ungoverned top-level application.

Verified repository directions at drafting time include:

- `engine/`: Python backend, FastAPI APIs, semantic kernel packages, PostgreSQL persistence and workers.
- `neuron/`: AI interpretation, document extraction candidate, conversation, learning, agent/MCP components.
- `experience/`: React/TypeScript web UI, presently with a bounded Review Panel; full application shell remains separately planned.
- `ontology/`, `profiles/`, `schemas/`, `knowledge-packs/`: authored semantic assets.
- `planning-mds/kg-source/**`: authored planning knowledge; compiled knowledge-graph outputs are **not hand-edited**.
- Semantic layers: evidence; open/typed source assertions; governed canonical world model; versioned ontology; learning candidates; conversations and derived knowledge artifacts.

In particular, accepted direction **ADR-0063** distinguishes **open statements** (claims preserved in source language), **typed assertions** (statements aligned to ontology), and governed canonical knowledge. A visual graph must *not* collapse these layers or promote evidence merely because it was traversed.

### Boundary architecture

```text
USER / ADMIN
     |
     +--> Chat with Document ----------------------> Answer + evidence refs
     |                                                     |
     |                                         'How the Brain answered'
     |
     +--> Learning activity / job details ------> Learning status + outcomes
                                                           |
                                                  'Inspect learning trace'
                                                           |
                                          +----------------v----------------+
                                          | Graph Observatory (experience/) |
                                          | playback + 3D + 2D + inspector  |
                                          +----------------+----------------+
                                                           |
                                           authorized trace/snapshot APIs
                                                           |
                                          +----------------v----------------+
                                          | Observatory projection layer   |
                                          | engine/: trace contracts,      |
                                          | auth filter, replay, summaries |
                                          +----------------+----------------+
                                                           ^
                                               typed observability events
                                                           |
                      +------------------------------------+----------------+
                      |                                    |                |
          graph/semantic retrieval                 neuron/learning    operation state
          ontology resolution                      assertion pipeline workflows
          evidence resolution                      conflict checks    and workers
                      |                                    |                |
                      +------------------------------------+----------------+
                                                           |
                               Existing Brain's governed semantic authority
                               PostgreSQL / graph / vectors / source evidence
```

**One-way authority rule:** semantic operations may emit trace facts; the Observatory may read and render them; the Observatory may **not** alter the source-of-truth based on presentation state. Observability events do not themselves change canonical truth.

## 2. Experience A — Chat with Document answer trace

### Primary journey

1. The user opens a document and asks a question in its chat interface.
2. The Brain responds with an answer, source references, applicable caveats, and an `execution_id` / `trace_id` when an instrumented execution exists.
3. A small **How the Brain answered** summary appears next to the answer: sources consulted, number of recorded graph hops, evidence references, reasoning operations (if any), and warnings.
4. The user expands the trace panel. It defaults to a **static summary** at the end of execution, not an animation already playing.
5. The user chooses **Replay**. Actual events advance through the recorded execution sequence, highlighting nodes, relations, evidence, inference outputs, uncertainties, and skipped/failed steps.
6. Selecting a node/edge opens a contextual inspector: ontology meaning, asserted relationship, evidence locator, timestamps, canonical/candidate status, and role-permitted raw document citation.
7. The user can pause, step, scrub, switch to 2D, inspect the answer's cited evidence, or leave the replay without losing the answer.

### Suggested desktop layout

```text
+-----------------------------------------------------------------------+
| Document title / account context                           [History] |
+----------------------------------+------------------------------------+
| Document + evidence              | Chat with Document                 |
| [PDF / table / source excerpt]   | User: Does this endorsement ...?  |
|                                  | Brain: Answer and caveats          |
| Highlight sourced paragraph <---+ [Citation A] [Citation B]          |
|                                  |                                    |
|                                  | [How the Brain answered  v]        |
+----------------------------------+------------------------------------+
| GRAPH OBSERVATORY (collapsible, optionally full-screen)                |
| [Summary] [Replay] [2D] [3D] [Evidence]  As-of time [ ... ]            |
|                                                                       |
|  ambient graph     illuminated actual path      node inspector        |
|  o..o..o    -----> O ===> O ===> O              Relationship: ...    |
|  .  . .            (focused neighborhood)       Source: ...          |
|                                                                       |
|  playback:  |<  <  [play]  >  >|       trace event / duration         |
+-----------------------------------------------------------------------+
```

On smaller screens, make the trace a drawer/full-screen view rather than compressing an unreadable 3D graph. The evidence pane and answer text remain accessible without WebGL.

### Show the **actual answer basis**, not the full retrieval universe

Attribution must distinguish:

- **Observed:** executed query; retrieved candidate result; node/edge actually visited; evidence opened; rule evaluated; recorded conclusion.
- **Used in answer:** an evidence reference or canonical fact explicitly linked to a supported answer span/structured conclusion.
- **Considered but not used:** retrieved candidate, rejected path, conflict, or unselected source.
- **Unknown or not instrumented:** internal tool/model behavior for which no trusted trace event exists.

A traversal graph is **not** automatically a causal proof of the answer. `used_in_answer` links must derive from the answer's grounded evidence/derivation references, not from proximity or animation. If an operation was not recorded, show an instrumentation gap rather than make up intermediate hops.

### Example: GL endorsement question

*User:* “Does endorsement X change the general aggregate limit effective on the renewal date?”

An example recorded path **if and only if the corresponding operations occurred**:

```text
Document context
   -> resolved Policy P
   -> visited policy --hasCoverage--> GL Coverage C
   -> visited endorsement --amendsCoverage--> C
   -> compared endorsed effective time to user's as-of date
   -> resolved source evidence from endorsement and declarations
   -> assessed contradictory/older policy wording if discovered
   -> returned conclusion with evidence and uncertainty
```

The graph overlays should separate the policy/coverage relationship, source assertions, temporal selection, and any derived inference. Showing a contradiction is a success of transparency, not a rendering error. The evidence panel should deep-link to its source page/block/row.

## 3. Experience B — Learning Observatory (read-only)

### Primary journey

1. Administrator opens a document ingestion run, conversation-derived learning artifact, corrected extraction, or candidate semantic update.
2. The page shows **observed run history**, current status, versions, counts, errors, and policy-controlled visibility.
3. The administrator opens **Inspect learning trace** to explore what changed—or was only proposed—with a static state summary.
4. On request, a replay shows recorded transitions: content reuse, open statement extraction, ontology alignment, typed assertion materialization, entity resolution, conflict checks, proposed learning candidates, canonical change commits (when and only when committed), and versioned ontology effects.
5. The admin filters by `candidate`, `committed`, `rejected`, `conflicted`, `unresolved`, `not_applicable`, and by knowledge layer. The view links to an authoritative governance artifact, if available, without implementing approval actions itself.

### Key question the screen must answer

> **What new information arrived, what did the Brain already know, what was proposed, what was accepted, and why?**

A critical case is **zero canonical change**. The Brain might read a document and correctly retain a statement as source evidence, reject ontology alignment, detect a duplicate, or log an unresolved conflict. The visualization must show all these outcomes without implying successful learning.

### Learning lane / layered model

```text
SOURCE / EVENT       "Endorsement language ..."  (persisted source)
      |
OPEN STATEMENT       Verbatim supported claim, predicate not bound
      |
ONTOLOGY ALIGNMENT   Matched to existing property? undecided? no fit?
      |
TYPED ASSERTION      Ontology-bound assertion + version + source origin
      |
ENTITY RESOLUTION    References bound, uncertain or unresolved
      |
CONFLICT / TEMPORAL  Compare against existing claims and accepted versions
      |
LEARNING CANDIDATE   Proposed relationship/concept/rule (not canonical)
      |
GOVERNED COMMIT      Only on independently verified commit event
      |
VIEW / PROJECTION    New current graph snapshot or version
```

Not every run follows every lane. Some steps may execute in parallel, be absent, retry, or fail. The animation derives phases from recorded operations; it does not fabricate an eight-step sequence.

### Learning event classifications

| Event in backend | Display meaning | Must **not** imply |
|---|---|---|
| `SOURCE_CONTENT_REUSED` | Prior parsed artifact was reused | Source was parsed again |
| `OPEN_STATEMENT_RECORDED` | Source statement captured verbatim | Statement is true or ontology-bound |
| `ASSERTION_ALIGNED` | Typed mapping associated with a schema release | Canonical acceptance |
| `ENTITY_LINK_RESOLVED` | Identity link selected or validated | All ambiguity eliminated |
| `CONFLICT_DETECTED` | Incompatible candidates/effective facts found | One claim is necessarily false |
| `LEARNING_CANDIDATE_CREATED` | Proposed new semantic knowledge | Promotion completed |
| `ONTOLOGY_CHANGE_PROPOSED` | Suggested class/predicate/rule update | Released ontology changed |
| `CANONICAL_CHANGE_COMMITTED` | Authorized canonical write confirmed | Every downstream projection already caught up |
| `ONTOLOGY_RELEASE_PUBLISHED` | New ontology version published | All earlier assertions were reinterpreted |
| `PROJECTION_UPDATED` | Read model advanced | Underlying evidence was created now |

*These event names are proposed observability contract names, not verified existing implementation endpoints.*

## 4. Visual design translated from the reference video

The original video establishes the **visual vocabulary**, not the operational data model. Reproduce its atmospheric qualities while rendering actual events only.

| Reference-video behavior | Observatory interpretation | Integrity rule |
|---|---|---|
| Large star-like graph field | Aggregated or known surrounding semantic neighborhoods | Do not represent unqueried entities as visited |
| Stable colored clusters | Ontology domains, entity families, or knowledge layers | Legend makes category and granularity explicit |
| Ring / moving attention focal point | Active *recorded* operation focus | Call it traversal focus, not transformer attention |
| Luminous connecting arc | Recorded traversed predicate/path | Edge and direction resolved from the trace |
| Dimmed background | Known but currently inactive context | Not a claim that unseen data was eliminated |
| Camera sweep | Move between recorded neighborhoods on replay | Preserve spatial orientation and allow reduced motion |
| HUD counters | Measured execution/event counts and latency | No invented token throughput or coherence gauges |
| Scrolling terminal | Human-readable semantic event log | No raw secrets, unredacted prompts, or DB credentials |

### Visual semantics

Color is redundant with line pattern, icon, tooltip, and textual legend:

- **Source/evidence:** source-document or citation-marked shape.
- **Open statement:** source-language assertion shape distinct from canonical facts.
- **Typed assertion:** ontology-bound predicate edge; label displays ontology version.
- **Canonical fact/relationship:** solid line with verified committed status.
- **Inferred/derived:** derivation shape with rule reference; never indistinguishable from direct evidence.
- **Proposed learning:** dashed outline and candidate label.
- **Conflict/unknown:** warning marker and explicit unresolved reason.
- **Active focus:** halo following one or more *recorded* replay events.

Labels remain accessible in a separate inspector, keyboard-navigable event list, and 2D mode. Animations are supplementary rather than the only way to understand conclusions.

### 3D layout rules

Use stable, deterministic cluster anchors and cache layouts by graph projection/view/version. Do not let a force layout rearrange the full scene on every replay event. Assign no semantic meaning to arbitrary X/Y/Z positions. If importance drives node size, disclose the computed measure and scope. The renderer should show semantic aggregates at distance, expand details only for the authorized subgraph, and maintain a stable camera target.

The visualizer is deliberately **not** an entire knowledge graph browser; it is a bounded observability canvas with expansion links into ordinary graph/entity inspection.

## 5. Trace and replay architecture

### Three distinct datasets

1. **Execution trace:** immutable or append-controlled ordered facts about one run; includes event type, provenance, identifiers, status, versions, timestamps, safe metadata.
2. **Graph projection snapshot:** authorized, bounded nodes/edges selected for this trace and knowledge-time context, with stable semantic identifiers and relationship types.
3. **View presentation state:** user-controlled camera position, replay cursor, selection, layout, filters, and 2D/3D mode; never authoritative.

Do not overload a single “telemetry payload” with all three.

### Trace lifecycle

```text
Chat request / learning run
       |
       v
Existing engine/neuron operation  --instrumented--> event emitter
       |                                         |
       v                                         v
Answer / learning result                 durable trace sink
       |                                         |
       +------------------execution_id-----------+
                                                 |
                                  trace summary + event pagination
                                                 |
                                          snapshot/projection
                                                 |
                                      policy-filtered API
                                                 |
                              static view -> replay on demand
```

Record event sequences at operation boundaries, not every frame. A complete trace should carry terminal status; unfinished/failed traces must remain inspectable with explicit completeness metadata. A trace is not a substitute for the existing audit trail and may retain narrower, redacted data.

### Recommended persistence

Read-path and learning traces are stored differently (ADR-0071 section 5, ADR-0072 section 2).

**Read-path traces (answers, queries).** Nothing else records their internal steps, so they are stored directly: PostgreSQL, a dedicated schema, bounded retention, no new event platform. Suggested logical tables:

- `semantic_trace`: trace ID, execution ID, operation type, principal scope (server-side only), status, semantic context, start/end, completeness.
- `semantic_trace_event`: trace ID, monotonic sequence, event ID, event type, attribution, timestamp, span IDs, typed sanitized payload.
- `semantic_trace_projection`: trace ID, projection version, as-of context, reference to the bounded authorized projection.

The answer basis is not a separate table. It is the grounded answer's own references (ADR-0046), copied into the `ANSWER_BASIS_LINKED` event when the answer is emitted.

**Learning traces.** These are a read model rebuilt from authoritative records, each event citing its record. They can be cached, but the cache is disposable.

For learning traces, never represent a commit that the commit record does not show. For purely read-side spans, instrument execution boundaries and persist structured trace events; avoid inventing a distributed exactly-once guarantee. Never claim a commit on a planned or attempted event. Store only necessary IDs, hashes and summaries, with guarded lookups for sensitive content.

### Sequence, replay and version semantics

- `sequence` establishes ordering **within one trace**; timestamps are not an ordering guarantee.
- Support parent/child spans and causal links for parallel operations. A flattened timeline is a chosen view, not proof of serial execution.
- Store the ontology release, graph/canonical snapshot identifier, as-of valid time, as-known/recorded time, and projection version needed to explain an event.
- When replaying a historical trace, default to the **recorded snapshot/meaning at execution**, not silently current graph data.
- If a historical version is unavailable, explicitly label the projection as reconstructed or incomplete and suppress unsupported claims.
- Replays must be deterministic in their **semantic state**; cosmetic particle timing may vary.
- Record completion, failure, timeout and instrumentation-gap markers.

### Sample contract (illustrative)

```json
{
  "schema_version": "1.0",
  "trace_id": "trace_gl_001",
  "event_id": "evt_014",
  "sequence": 14,
  "occurred_at": "2026-10-13T11:22:13Z",
  "operation": "DOCUMENT_CHAT",
  "event_type": "EDGE_TRAVERSED",
  "span_id": "span_traverse_02",
  "parent_span_id": "span_retrieve_01",
  "semantic_context": {
    "ontology_release_id": "ontology-release-example",
    "graph_projection_id": "projection-example",
    "valid_as_of": "2026-07-01",
    "known_as_of": "2026-10-13T11:22:00Z"
  },
  "payload": {
    "source_node_id": "policy-example",
    "predicate_id": "hasCoverage",
    "target_node_id": "coverage-example",
    "layer": "CANONICAL",
    "evidence_ref_ids": ["evidence-example"]
  }
}
```

The contract is now drafted as [`semantic-execution-trace.schema.json`](../schemas/semantic-execution-trace.schema.json); the options page's fixtures pass it. `trace_id` should be opaque and authorized on each access. Tenant and principal IDs may be captured in trusted server metadata but **must not be accepted from client-submitted trace identifiers**. Store typed, schema-validated events and generate frontend types from a shared JSON Schema/OpenAPI definition where practical. The identifiers and predicates above are illustrative only.

### Query API (proposed; subject to API convention review)

```text
GET /api/observatory/traces/{trace_id}
GET /api/observatory/traces/{trace_id}/events?after=...&limit=...
GET /api/observatory/traces/{trace_id}/graph?view=answer-basis
GET /api/observatory/traces/{trace_id}/evidence/{evidence_ref}
GET /api/observatory/learning-runs/{run_id}/traces
```

Return trace completeness/status, permission-safe counts, version context and next-page cursors. Authorization must occur on every resource expansion, not only the trace summary. **No live WebSocket is required for the agreed replay-first v1**; paginated HTTP can deliver accurate event playback. SSE/WebSocket is a future transport option if live observability is later requested.

## 6. Backend instrumentation boundaries

### Chat / graph reasoning

Instrument at observable boundaries such as:

- request accepted and document/knowledge scope established;
- entity/document context resolved;
- vector/text/graph retrieval operation performed and candidates returned;
- actual graph predicates traversed or neighborhoods expanded;
- ontology class/property/rule applied;
- evidence verified or unavailable;
- conflict, failed constraint or temporal mismatch identified;
- grounded answer basis assembled and response emitted.

A retrieval hit is not a committed relationship and not necessarily an answer source. A generated answer token stream is not a graph traversal trace. Where the LLM cannot expose validated intermediate steps, report only tool calls, structured outputs, verified derivations and final grounding. **Do not capture or reveal hidden chain-of-thought.**

### Learning / ontology changes

Project these from the authoritative records that already exist (ADR-0072), instead of emitting a parallel learning event stream. Each projected event cites its record:

- content artifact reused or initial parse completed;
- statement/typed assertion admitted or rejected;
- signature/property alignment and decision basis recorded;
- entity resolution and conflict checks performed;
- learning candidate proposed, superseded or retained;
- human/governance action **observed** from authoritative record;
- canonical commit and ontology publication acknowledged by their own committed events;
- downstream projection catch-up recorded separately.

Respect ADR-0063's source-language assertion versus typed assertion separation. An ontology change proposal is never rendered as a released schema change; similarly, an inferred assertion must carry a derivation/rule reference rather than masquerade as source evidence.

### OpenTelemetry and semantic tracing

Use OpenTelemetry-style trace/span correlation for operational timing and distributed causality if compatible with the existing platform. Add a **domain semantic event contract** alongside it, since generic spans cannot express provenance, ontology release, time dimensions, or canonical status. Do not put entire source documents, PII, prompts, embeddings, or evidence excerpts into generic telemetry exporters.

## 7. Frontend integration and rendering stack

### Place inside the existing app

Suggested logical paths, subject to the repository's actual feature conventions:

```text
experience/src/features/graph-observatory/
    api/                  trace and projection fetching
    contracts/            generated domain event types
    store/                replay cursor and UI state (Zustand)
    components/           AnswerTracePanel, LearningTracePanel,
                          GraphCanvas3D, GraphCanvas2D,
                          TraversalFocus, SemanticInspector,
                          ReplayControls, EventTimeline, HUD
    render/               GPU buffers, shaders, instanced nodes/edges
    layout/               deterministic anchors, worker calculations
    accessibility/        semantic event list, keyboard/reduced-motion
    tests/
```

Use React/TypeScript already in `experience`. The current `experience/package.json` is React 18 + Vite + TypeScript with four runtime dependencies. State management, query caching and styling are app-wide choices for F0021, not this feature. F0067 adds only rendering dependencies, pinned through the dependency policy. 2D inspection reuses F0045's Cytoscape explorer.

Candidate roles (the 3D rows apply only if F0067 chooses 3D; GSAP's licence is free of charge but proprietary and needs review):

| Tool | Why |
|---|---|
| Three.js + React Three Fiber | 3D space, controlled camera, instanced rendering |
| GSAP or R3F-native animation | Replay-controlled camera/focus interpolation; cancellable seeks |
| Zustand | Cursor, selection, filters, display state (not canonical graph truth) |
| TanStack Query (if adopted) | Snapshot/event pagination, evidence fetch/cache |
| Cytoscape.js | Legible 2D semantic inspection |
| Tailwind + shadcn/ui (if adopted) | HUD, accessible controls, inspector and responsive layout |
| Web Worker | Larger layouts and projection preprocessing away from UI thread |

### Rendering and replay mechanics

```text
HTTP trace summary + paginated events + graph projection
                     |
          normalized trace cache
                     |
      replay cursor / seek / step
                     |
         deterministic view reducer
            /       |         \
     3D scene    timeline     inspector
       /             |           |
  halo/paths       event text  evidence / ontology
```

The reducer must support seek directly (via snapshots/checkpoints or deterministic recomputation), not just forward-playing mutable animation state. Camera travel and luminous arcs depend on events already recorded; they are **presentation animations** and may never introduce extra semantic hops.

For performance, batch points and edges on GPU; use instancing/BufferGeometry, bounded labels, viewport culling, aggregated far-field graph structure, and detail-on-demand. Treat 10,000 visible lightweight nodes / ~1,000 focused edges as **initial benchmark candidates**, not guaranteed capacities. Do not spawn thousands of React DOM objects. Use device-aware reduced effects and a static fallback when WebGL is unavailable.

## 8. Security, governance and privacy

Security is integral: a connected graph can expose private relationships even if each node label looks innocuous.

- **Historical replay:** Replay shows what the viewer may see now, intersected with what the execution saw. It never reinstates revoked access (ADR-0053, ADR-0072).
- **Server-side resource scope:** Apply Brain AuthX, tenancy, document/resource permissions, and delegated-agent constraints to every trace query and evidence expansion.
- **Existence leakage:** Filter node IDs, edge existence, counts, cluster labels and topology. Do not reveal forbidden neighbors as anonymous ghost nodes unless that disclosure is explicitly allowed.
- **Read-only:** The Observatory issues GET/query operations and controls only local view state. Editing, promoting, approving and publishing remain in authoritative workbenches and services.
- **No hidden reasoning:** Show verifiable structured traces, not model chain-of-thought, unseen attention, or inferred private deliberation.
- **Data minimization:** Persist sanitized metadata and references; retrieve evidence through existing authorized document APIs. Avoid raw prompt/claim payloads in operational logs.
- **Version/retention:** Record semantic release/snapshot identifiers, retention class, redaction requirements, and access/audit events. Align trace retention with organizational security policy; do not default to indefinite retention.
- **Governance accuracy:** Distinguish attempt vs commit vs projection availability; proposed vs accepted; source statement vs typed claim vs canonical fact.
- **Observability of observability:** Capture trace instrumentation failure, truncation, missing evidence, and export failures as explicit completeness states.

### Data lineage assertion

The graph renderer must **not** derive “used in final answer” from all visited nodes. Explicit answer-basis links are required. Evidence hashes/locators, derivation IDs and canonical fact version references should be resolvable at the retained temporal snapshot, subject to permissions.

## 9. UX specification and states

### Chat panel compact summary

```text
How the Brain answered                 [Inspect]
2 cited evidence items | 4 recorded graph hops | 1 time check
Trace status: Complete                [Replay]
```

The numbers above are illustrative. If no graph traversal occurred, show **“No recorded graph traversal; answer grounded in document excerpts”** instead of showing a decorative path. If no trace was captured, say **“Detailed trace unavailable”**; this must not block the answer.

### Admin run summary

```text
Learning run: example-123            Status: Completed
Source statements: 8 | Typed assertions: 5 | Candidates: 2
Canonical changes: 0 | Unresolved conflicts: 1
[Inspect events] [Replay] [Open authoritative record]
```

Again, the example values are not claims about an actual run. “Canonical changes: 0” is an informative and expected outcome.

### Essential states

- no operation trace / instrumentation disabled;
- trace recording in progress (not automatically animated);
- complete, partial/truncated, failed, or timed-out trace;
- evidence redacted or no longer accessible;
- historical ontology/projection missing;
- disputed relationship or multiple competing claims;
- 3D unavailable / prefers-reduced-motion / 2D selected;
- replay paused, seeking, finished, and reset.

Provide a legend and accessible event list in every mode. Avoid overloaded HUD gauges that can't be defined operationally. Suggested real measurements: node/edge visits, retrieval candidates, verified evidence references, conflicting assertions, rule checks, elapsed per-stage duration, and event completeness.

## 10. Delivery approach: carry the contract in now, land the Observatory in v0.2B

The draft's four slices are replaced by two moves.

### Move 1: carry-in requirements (now, as PRD inputs)

Each feature below carries a short "Graph Observatory carry-in" section in its README. The plan action folds it into the PRD. Feature status does not change.

| Feature | Phase | What it carries |
|---|---|---|
| F0016 Semantic interpretation runs | v0.1A | Run and per-stage outcome records queryable by run, with terminal status, including "nothing changed" outcomes. No Observatory-only events. |
| F0021 Native React shell | v0.1B | A route, feature-flag and lazy-load seam, so a heavy view can load without growing the base bundle. No Observatory dependencies in v0.1. |
| F0034 AGE graph projection | v0.2A | A stable projection version identifier that a trace can cite. |
| F0036 Grounded generation | v0.2A | The answer-basis event built from the ADR-0046 answer object; retrieval, traversal, temporal, evidence and conflict boundary events; disclosed gaps. |
| F0037 Conversation engine | v0.2A | Call-boundary and gap events for model and tool calls; no chain-of-thought capture; non-blocking recording. |
| F0038 Chat with Document | v0.2A | `trace_id` on each answer; the read-path trace store; the early "How the Brain answered" panel (static summary plus basis path, no replay); the answer never depends on the trace. |
| F0040 Conversation graph | v0.2A | Conversation hypotheses as their own layer in traces, never shown as canonical. |
| F0041 Learning plane | v0.2B | Candidate lifecycle records with terminal states, citable by learning traces. |
| F0042 Promotion and governance | v0.2B | Commit and publication records distinguishable from attempts (ADR-0069); review decisions citable; deep-link targets. |
| F0045 Cytoscape explorer | v0.2A | The shared layer and attribution vocabulary, reusable as the Observatory's 2D view. |
| F0058 Historical decision replay | v0.4+ | The same replay coordinates and the same permission rule. |

### Move 2: F0067 Graph Observatory (v0.2B)

F0067 builds the projection layer, read APIs, the full answer trace view (extending F0038's early panel with replay) and the read-only Learning Observatory on top of Move 1. It records the renderer decision (whether and where 3D is used) from the options review. Its first golden cases are one real GL endorsement answer and three real learning runs: zero canonical change, an unresolved conflict, and a governed commit.

### Guardrails

Feature flags and graceful fallback throughout. The answer and the ingestion run never depend on the Observatory. No mock production traces fill missing backend capability.

## 11. Test strategy and acceptance criteria

| Dimension | Required verification |
|---|---|
| Semantic fidelity | Every visual visited node/edge maps to an authorized recorded operation; no invented hops |
| Answer attribution | “Used in answer” edges/evidence supported by explicit output-basis refs |
| Learning correctness | Candidate, conflict, commit, release and projection states remain distinct |
| Historical reproducibility | Deterministic semantic replay using stored version/as-of context |
| Trace gaps | Partial, truncated, missing and failed traces disclosed accurately |
| Security | Tenant isolation; no unauthorized topology/count/evidence inference |
| Read-only | No Graph Observatory API or UI action can approve/commit/publish |
| Accessibility | 2D/list fallback, keyboard controls, accessible labels, reduced-motion setting |
| Rendering | Benchmarked bounded graph with stable frame time and no unbounded memory growth |
| Reliability | Repeatable cursor seeking; cursor/page reconstruction across refresh |
| Graceful failure | Chat answers and existing ingestion/review run when visualization is unavailable |
| Privacy | No raw secrets/prompts/PII leaked to generic telemetry exporters |

### Measurable initial targets (proposed, to validate)

- p95 trace summary retrieval below 1 second on target test hardware for a bounded trace.
- p95 seek-to-settled semantic state below 250 ms for the initial bounded fixture; camera easing may continue afterward.
- 60 FPS desktop goal for bounded active neighborhoods, with a 30 FPS reduced-effects fallback; benchmark rather than assume.
- 30-minute replay/inspection stress test without unbounded growth.
- All semantic event sequences deterministic under repeated seek/step/refresh tests.
- Zero intentionally fabricated production semantic events; backend instrumentation gaps visibly disclosed.

## 12. ADRs and work products

The draft proposed five ADRs. Two carry decisions; the rest are design detail for F0067's Phase B:

- [ADR-0071](decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed): trace contract, attribution classes, gap disclosure, ordering and time, recording rules, validator invariants.
- [ADR-0072](decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed): read-only boundary, learning traces as projections over authoritative records, authorization on every expansion, replay never reinstates access, synthetic labelling, replaceable renderers.
- Persistence and replay detail falls under ADR-0071 with ADR-0032 and ADR-0053. Visual vocabulary and rendering strategy belong in F0067's Phase B architecture, informed by the options page.

Work products in the repository:

- [Draft schema](../schemas/semantic-execution-trace.schema.json)
- [Rendering options page](../examples/graph-observatory-2d-options.html) with fixtures EX-OBS-001 (answer trace) and EX-OBS-002 (learning run)
- [F0067 feature shard and README](../features/F0067-graph-observatory/README.md)
- Carry-in sections in the feature READMEs listed in section 10

Stories are authored by F0067's plan action; the draft's O-01 to O-09 partition is an input to it, not a commitment.

## 13. Risks, alternatives and decisions deferred

| Risk | Mitigation / selected posture |
|---|---|
| Pretty graph creates false sense of certainty | Layer/status legend, explicit evidence and unknowns, verified event-only view |
| Traces expose sensitive topology | Backend-sanitized graph projections and fine-grained checks on every expansion |
| Visual sequence hides parallel execution | Preserve causal span parentage; timeline indicates parallel branches |
| Renderer bogs down on enterprise-scale graph | Bounded subgraph, LOD, batching, stable layout, adaptive effects |
| Trace volume grows without bound | Configurable retention, sampling of low-value metrics, bounded event payloads, partitioning where needed; never sample mandatory audit facts incorrectly |
| Instrumentation changes app semantics | Nonblocking emit path, failure isolation, independent success/failure monitoring |
| Historical replay silently uses current ontology | Persist version context; disclose unavailable snapshots; fail closed on claims of historical correctness |
| Feature appears before host experience exists | Feature flags; defer runtime integration until chat/learning pathway real |

**Deferred decisions:** renderer choice (whether and where 3D is used; F0067), finalized event taxonomy, replay graph projection representation, concrete valid-time precision encoding, 3D/2D library pins, thresholds for aggregation, deployment telemetry backend. (Retention, trace access and the golden cases were decided on 2026-10-13; see the product decisions table and F0067.) These require the actual code path and repository standards review rather than assumptions in this document.

## 14. Recommended first implementation target

Build **one faithful, bounded, replayable demonstration backed by a real GL policy-and-endorsement execution**. In its collapsed state, the user receives a normal answer with precise citations; expanding **How the Brain answered** reveals a static trace summary; pressing **Replay** animates the recorded path with the same visual polish as the reference video. The admin counterpart starts with **one real incremental learning run** that displays proposed and committed outcomes without any editing action.

This creates the critical product proof: the visualizer is beautiful, but every illuminated node, arc, warning and transition has a traceable semantic reason to exist.

---

## Appendix A. References

- [BLUEPRINT](../BLUEPRINT.md) and [master blueprint](master-blueprint.md)
- [ADR-0046](decisions/ADR-0046-grounded-answer-and-analytic-query-contract.md), [ADR-0063](decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0053](decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md), [ADR-0032](decisions/ADR-0032-decision-replay-uses-recorded-time-state.md), [ADR-0071](decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md), [ADR-0072](decisions/ADR-0072-observatory-is-a-read-only-projection.md)
- `experience/package.json` (frontend dependency baseline)
- The reference video is visual direction only. It is not evidence of attention mechanisms or of real semantic events, and it is not stored in the repository.

## Appendix B. Vocabulary

**Answer basis:** explicit, verifiable references linking an answer statement/conclusion to evidence or derivation. **Trace:** ordered observable facts from one execution. **Projection:** an authorized view of graph entities/relationships for a trace and temporal context. **Source statement:** evidence-backed claim in source language. **Typed assertion:** source claim aligned to an ontology predicate. **Canonical fact:** governed accepted semantic state. **Learning candidate:** new proposed knowledge not yet accepted. **Replay:** rebuilding visual state from stored operations rather than replaying the model computation. **Bitemporal context:** effective/valid time plus the time knowledge was recorded. **Read-only:** no mutation of semantic knowledge or governance state from the Observatory.
