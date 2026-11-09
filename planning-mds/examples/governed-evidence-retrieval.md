# Governed evidence retrieval — worked and boundary examples

**Provenance:** Synthetic teaching cases; all outcomes below are illustrative expectations, not observed runtime results or legal/coverage advice. No production data or measured retrieval benefit is claimed. These development examples must stay outside the frozen evaluation holdout.

**Delivery:** F0033–F0036, v0.2A; F0067 visualization, v0.2B; conditional F0068 spectral experiments, v0.4+. The owners have no retrieval stories yet; their Phase A plans must bind these stable example IDs to stories and runtime reproduction commands. Definitions: [retrieval glossary](../domain/glossary.md#governed-evidence-retrieval). Contract direction: [ADR-0076](../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) and [design](../architecture/governed-evidence-retrieval-design.md). Also see [EX-FUTURE-001](future-semantics.md#retrieval-projection) for similarity versus accepted facts.

## EX-RET-001 — Bridge evidence under a budget

Priya asks which endorsement changed a synthetic policy's products-completed operations wording as of March 1. The fixture contains the original form, an amending endorsement, its effective clause and near-duplicate form passages. The authored gold evidence set includes the original wording, the modifying wording and the effective clause. Whether those words establish a coverage result is determined by the applicable source/canonical contract, never by a retrieval score.

**Worked:** A budget-aware selector keeps the required anchor and bridge evidence together, preserves the effective clause, groups by source, resolves the original locators and counts the complete serialized payload with the pinned tokenizer. The answer cites the evidence that supports its claims.

**Boundary:** Near duplicates must not crowd out the endorsement. If the full required set cannot fit, disclose the missing support or abstain. Do not truncate a clause/table row in a way that changes meaning, invent an effective date, or label an unresolved locator exact. Reauthorization removal triggers recount and coverage/gap recomputation.

**Owner:** [F0036](../features/F0036-evidence-aware-retrieval-and-grounded-generation/README.md), RET-36-01–06; ADR-0046/0058/0076.

## EX-RET-002 — Authorized expansion and hidden influence

**Worked:** Starting from an authorized policy, a typed link reaches its authorized location schedule. Both vertices, the relationship and the evidence dependencies pass current authorization at the pinned mode and time; the trace records the actual admissible path.

**Boundary:** A second path passes through a restricted intermediary. Even if both outer endpoints are visible, the path cannot contribute candidates, scores or counts. Modify/revoke that intermediary while leaving the admissible corpus unchanged: returned IDs, paths, score components, visible counts and selected context must remain unchanged. Assess timing and cache inference separately. A cross-tenant entity-name collision cannot create a link.

For F0068 the same case rejects a global eigenbasis built with the restricted intermediary; hiding its row later does not remove its influence. Use a compatible authorized basis or a safe baseline. Any bounded local computation needs separate experiment approval.

**Owners:** [F0034](../features/F0034-age-graph-projection/README.md), RET-34-01/03; [F0035](../features/F0035-hybrid-search-and-authorized-scope/README.md), RET-35-01/03/06; [F0068](../features/F0068-spectral-graph-retrieval-experiments/README.md), RET-68-02; ADR-0053/0076.

## EX-RET-003 — Source wording and canonical state

**Worked:** At a snapshot where the original form and later endorsement are both known, source mode can return the original wording as source evidence. Canonical mode at the same valid/known coordinates resolves the accepted amended binding. Each result declares its mode and precise version references. One immutable block can support several assertions; its content does not acquire a single universal acceptance status or canonical interval.

**Boundary:** At a `known_as_of` before the endorsement arrived, neither mode uses it in ranking or context. A source-only unaccepted assertion never becomes an accepted fact because retrieval found it. Supersession does not erase source wording; historical coordinates do not restore revoked access. Unknown temporal bounds remain explicit.

**Owners:** [F0035](../features/F0035-hybrid-search-and-authorized-scope/README.md), RET-35-04; [F0036](../features/F0036-evidence-aware-retrieval-and-grounded-generation/README.md), RET-36-03/04; ADR-0064/0073/0075/0076.

## EX-RET-004 — Requested root narrows broader grants

**Worked:** A user can read accounts A and B but asks a question rooted at A. Seeds, expansion, counts, context and replay use the requested A scope.

**Boundary:** A highly similar document from B cannot enter ranking or backfill. Broadening permission while keeping the requested A root and admissible A inputs unchanged must not add B evidence. Narrowing scope is a separate check from tenant isolation.

**Owner:** [F0035](../features/F0035-hybrid-search-and-authorized-scope/README.md), RET-35-02/03; ADR-0062/0076.

## EX-RET-005 — Selected does not mean used

**Worked:** The selected context contains five items; the grounded answer cites two. `ANSWER_BASIS_LINKED` marks those two as used. The other three are considered, not used. F0067 renders the recorded classifications and reauthorizes the trace/evidence reads.

**Boundary:** Neither rank, spectral proximity nor traversal makes an item used. A trace-write failure leaves an explicit partial/not-instrumented state without failing the answer or fabricating paths. No source excerpts or hidden model reasoning are stored as trace diagnostics.

**Owners:** [F0036](../features/F0036-evidence-aware-retrieval-and-grounded-generation/README.md), RET-36-07/08; [F0067](../features/F0067-graph-observatory/README.md), RET-67-01; ADR-0046/0071/0072.

## EX-RET-006 — Projection compatibility and fallback

**Worked:** A supported retrieval mode finds its optional projection incompatible with the pinned snapshot or current grant revision. It records the effective compatible authorized lexical/hybrid path and actual projection IDs, or an explicit unavailable/gap result if no compatible path exists.

**Boundary:** Do not silently read today's AGE topology for a historical query, retain old authority through a cache hit, or invent a spectral projection ID. An unimplemented/disabled mode is rejected rather than treated as an artifact-failure fallback. F0068 cannot reuse a current or broader-scope spectrum by selecting visible rows. A partial artifact build never publishes mixed node-map/adjacency/eigenpair revisions.

**Owners:** [F0033](../features/F0033-pgvector-retrieval/README.md), RET-33-03; [F0034](../features/F0034-age-graph-projection/README.md), RET-34-02/04; [F0035](../features/F0035-hybrid-search-and-authorized-scope/README.md), RET-35-04/05/08; [F0068](../features/F0068-spectral-graph-retrieval-experiments/README.md), RET-68-01/02/04; ADR-0076.
