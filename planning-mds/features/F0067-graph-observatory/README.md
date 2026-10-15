# F0067 — Graph Observatory

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

The Graph Observatory makes the Brain's recorded work inspectable. A knowledge worker opens **How the Brain answered** under an answer and sees what evidence, relationships, fact versions and conflicts it rests on. An administrator opens a learning run and sees what arrived, what the Brain already knew, what was proposed, what was committed, and why. Both are read-only and replay on demand.

This feature was added by the 2026-10-13 amendment. It is governed by proposed [ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (trace and answer-basis contract) and proposed [ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (read-only projection boundary). Design: [Graph Observatory design note](../../architecture/graph-observatory-design.md). Rendering options and fixtures EX-OBS-001/002: [options page](../../examples/graph-observatory-2d-options.html). Draft contract: [semantic-execution-trace.schema.json](../../schemas/semantic-execution-trace.schema.json).

The contract is carried into its predecessors first (design note section 10). This feature builds on what they record and cannot start before them.

## Scope

- **Answer trace.** Extends the early **How the Brain answered** panel that [F0038](../F0038-chat-with-document/README.md) ships (static summary and basis path) with the chosen renderer and replay with pause, step and scrub. Attribution follows ADR-0071: observed, used in answer, considered not used, not instrumented.
- **Learning Observatory.** A run summary and trace for interpretation and learning runs, projected from authoritative records (ADR-0072). Zero canonical change, unresolved conflicts, proposals and governed commits each read correctly. Read-only deep links to review queues, the ontology workbench and commit history.
- **Projection layer and read APIs.** Trace summary, paged events, bounded authorized projection and evidence expansion, each authorized server side. Replay never reinstates revoked access.
- **Rendering.** An accessible 2D view and event list in every mode, reusing F0045's vocabulary. Whether and where 3D is used is decided at Phase A from the options review. Reduced-motion and no-WebGL fallbacks.
- **Synthetic labelling.** Fixtures and demos are visibly marked.

## Out of scope

- Approving, rejecting, editing, promoting, committing or publishing anything.
- Live streaming of in-flight executions (replay-first; a later transport if asked).
- Showing model internals, attention or chain-of-thought.
- A whole-graph browser (F0045 and F0044 cover exploration).
- Re-extracting documents to produce visual frames.

## Open decisions for Phase A

- Renderer: which of the options page's renderings (A nebula 2D, B layer lanes, C basis path, D 2.5D depth reference, E true 3D with height as knowledge layer) are used where.

## Decided (operator, 2026-10-13)

- ADR-0071 and ADR-0072 are binding on the carry-in features now; acceptance still waits for their proof gates.
- Trace access follows answer access. Knowledge workers can see colleagues' answers, decisions and their traces; there is no separate trace permission (ADR-0072 section 3).
- Read-path trace retention defaults to 90 days, configurable per tenant; traces cited by a recorded decision are kept with it (ADR-0071 section 5).
- Golden cases: one real GL endorsement answer; three real learning runs (zero canonical change, unresolved conflict, governed commit).
- The first **How the Brain answered** panel (static summary plus basis path) ships early with F0038; this feature extends it.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0067.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
