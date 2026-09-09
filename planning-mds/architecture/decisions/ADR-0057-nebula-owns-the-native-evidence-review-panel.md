# ADR-0057: Nebula Owns the Native Evidence Review Panel

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-08
**Deciders:** Operator and Architect (product decision, 2026-09-08)
**Supersedes:** [ADR-0034](ADR-0034-label-studio-is-the-human-evidence-adjudication-engine.md)
**Amends:** [ADR-0001](ADR-0001-the-brain-owns-semantics.md) engine list; [ADR-0054](ADR-0054-repository-layout-runtime-roots-and-local-topology.md) local topology and asset trees
**Source:** Master blueprint sections 75, 111, 125; working prototype `planning-mds/examples/nebula-review-panel-live-files.html`

## Context

ADR-0034 selected Label Studio as the human evidence-adjudication engine on the direct-dependency rule: use a mature specialist product rather than rebuild its UX. That decision assumed the reviewer-facing capability the Brain needs — presenting a source region beside a predicted value, assigning it to a named reviewer, and returning a governed decision — was available in the edition the Brain would deploy.

Reviewing the official edition comparison against the governed loop this architecture requires shows the assumption does not hold. Project roles and access control, task assignment, and reviewer workflows are differentiated across Community, Starter Cloud, and Enterprise. The Community edition supplies task presentation, an API, webhooks, and pre-annotations; it does not supply the reviewer-authority model, assignment, or review workflow that sections 75 and 111.2 depend on. Section 111.1 already carried this as the risk to prove before estimating effort. The honest outcome of that investigation is that the Brain would pay Label Studio's full integration cost — a second identity system, a second copy of evidence outside the semantic boundary, webhook trust, task/assertion version reconciliation, per-document-type labeling configurations — and still have to build reviewer authority itself.

What the Brain actually needs from a review surface is narrower and more specific than a general annotation tool:

- render the original bytes of a submission package that mixes PDF, DOCX, XLSX, and CSV;
- put a predicted value next to the exact region the assertion claims it came from;
- accept, correct, or reject that value and return a governed `ReviewDecision`;
- say so plainly when the evidence cannot be anchored, rather than pointing at the wrong place.

A working prototype ([`examples/nebula-review-panel-live-files.html`](../../examples/nebula-review-panel-live-files.html)) demonstrates all four against real byte streams in the browser, with no server round trip and no external service: pdf.js (Apache-2.0) renders the PDF and exposes its text-item transforms, fflate (MIT) unzips the OOXML parts, and `TextDecoder` handles delimited text. Every coordinate, paragraph path, cell reference, and character offset in it is derived from the file at runtime, including the anchoring failures.

## Decision

**Decision:** Nebula owns the human evidence review surface. The Nebula Review Panel is a native part of `experience/`, rendered from the immutable content artifact and its evidence selectors, and it is the only surface on which a `ReviewDecision` is produced. Label Studio is removed from the architecture: it is not a runtime dependency, not a deployed container, not a Golden Corpus labeling environment, and not a documented alternate surface.

**Boundary:** Unchanged in substance from ADR-0034 and now entirely inside Nebula. The panel owns presentation, anchor resolution, and the reviewer interaction. The Brain owns `ReviewItem`, `ReviewDecision`, provenance, audit, semantic commits, and canonical truth. Annotation is still not approval (section 111.2): submitting a decision and committing canonical truth remain separate permissions, and the panel cannot commit.

**Composition:** The panel is a data-driven renderer keyed by content type, not a per-document-type labeling configuration. Adding a reviewable format means adding a renderer and its selector resolver behind the same review contract, defined in [ADR-0058](ADR-0058-evidence-anchoring-and-selector-contract.md). The first four are PDF (pdf.js), WordprocessingML and SpreadsheetML (fflate over the OOXML parts), and delimited text (`TextDecoder`).

**Use case (carried from ADR-0034, now native):** A casualty loss-run entity was extracted from page 7 with 0.61 confidence. The reviewer opens the review batch in Nebula, sees the exact source region and the predicted entity rendered from the immutable artifact, corrects it, and Nebula records the correction without mutating the original content artifact or the original machine assertion.

**Golden Corpus:** Ground-truth labeling and production correction use the same panel and produce the same records, which is what section 96 wanted from a shared review mechanism in the first place. Fixtures are exported from Nebula review decisions, not from an external project.

## Consequences

**Removed by this decision**

- The Label Studio container, its API client, webhook receiver, shared-secret trust, project templates, task mappers, and the `integrations/label-studio/` tree.
- The `engine/packages/brain-review-labelstudio/` package and `LabelStudioExternalTaskRef`.
- Reviewer identity mapping between two systems. The reviewer is the authenticated session principal (ADR-0049), so callback-origin verification, email-based user matching, and "annotation completion is not approval authority" enforcement at a webhook boundary all disappear as a class of problem.
- The external task-versus-assertion version reconciliation window. Staleness is still real, but it is now a check inside one transaction rather than an out-of-band callback arriving against a superseded version.
- Dependency on an edition's licensing terms for a governed capability, and reference R3 with it.

**Added by this decision**

- The Brain owns document rendering fidelity. pdf.js and fflate become pinned `experience/` dependencies in the section 114.3 matrix, with their own upgrade and security surface.
- Formats the panel cannot yet render cannot be reviewed. The renderer set is a delivery constraint that Label Studio's generality previously hid.
- Scanned pages with no text layer, rotated or cropped pages, aggressively fragmented PDF text items, tables continuing across page breaks, merged cells, and multi-row spreadsheet headers are now the Brain's problem to solve or to declare unresolved. The prototype exercises none of the OCR path; see ADR-0058 for how precision and failure are represented.
- Evidence never leaves the Brain's trust boundary for review. Retention, revocation, and deletion (ADR-0043) no longer have an external copy to chase, and task payload minimization (section 120.4) becomes a rendering-scope question rather than an export question.

**Governance**

- ADR-0034 is superseded, not deleted; its text stays readable as the decision that was replaced.
- ADR-0001's list of engines around the semantic core no longer includes Label Studio. Docling, Docling-Graph, AGE, pgvector, Temporal, and the remaining engines are unaffected.
- ADR-0054's local topology drops the Label Studio service and the `integrations/label-studio/` asset tree; `experience/` gains the review panel earlier than F0021's general shell, because F0022 depends on it.
- Features that cited `adr:0034` cite `adr:0057` in their kg-source shards.

## What still has to be proven

Accepting this decision settles the surface, not the implementation. The prototype is evidence that the design is sound, not that the loop works end to end.

| Proof | Owner | Release gate | Recorded result |
|---|---|---|---|
| Review round trip in the native panel: wrong limit corrected once, original assertion preserved, one audit event, decision survives restart | Backend + business reviewer | F0001-S0004 | Not executed |
| Duplicate submission and a decision against a superseded assertion version | Backend + QA | F0001-S0004 | Not executed |
| Reviewer authority: annotate permission cannot commit canonical truth; a reviewer outside scope cannot open the batch | Security reviewer | F0001-S0004, F0001-S0006 | Not executed |
| Anchor resolution and honest precision across the four renderers | Frontend + QA | F0001-S0004, ADR-0058 | Not executed |
| Golden Corpus export from native review decisions | Quality engineer | F0026 | Not executed |

## References

- Master blueprint sections 75 (human review), 111 (review surface and human governance), 125 (native review panel)
- Prototype: [`planning-mds/examples/nebula-review-panel-live-files.html`](../../examples/nebula-review-panel-live-files.html)
- Superseded: [ADR-0034](ADR-0034-label-studio-is-the-human-evidence-adjudication-engine.md)
- Related: [ADR-0037](ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0044](ADR-0044-review-surface-and-approval-contract.md), [ADR-0049](ADR-0049-shared-identity-and-verified-principal-boundary.md), [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md), [ADR-0058](ADR-0058-evidence-anchoring-and-selector-contract.md)
- pdf.js (Apache-2.0): https://github.com/mozilla/pdf.js
- fflate (MIT): https://github.com/101arrowz/fflate
