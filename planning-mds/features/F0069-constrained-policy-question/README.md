# F0069 — Constrained policy question (chat with this policy)

**Status:** Planned
**Phase:** v0.1C
**Roadmap:** Later
**Scope:** v0.1C; after F0024/F0025, before F0026 release qualification

## Overview

Give the v0.1 acceptance question a narrow conversational surface: a user on a policy asks a question about it and gets a trustworthy answer built from deterministic fact lookup and structured citations. This is the "chat with this policy" demonstration from master blueprint section 113.3. Section 115.3 places it in v0.1C; before this amendment its only owners were the v0.2 features F0036 to F0039.

Reserved by the 2026-11-08 blueprint requirement-ownership amendment (operator decision). Governing records: proposed [ADR-0046](../../architecture/decisions/ADR-0046-grounded-answer-and-analytic-query-contract.md) (v0.1 subset), [ADR-0039](../../architecture/decisions/ADR-0039-typed-insurance-values-and-completeness.md), [ADR-0042](../../architecture/decisions/ADR-0042-resource-and-derivation-authorization.md), [ADR-0053](../../architecture/decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md).

## Scope and acceptance inputs

- **CPQ-01 — Rooted and scoped.** The conversation is rooted on one policy the user is entitled to. Context expands only to that policy's accepted facts and their evidence; there is no broad retrieval.
- **CPQ-02 — Deterministic answers.** Answers come from F0020 typed queries over canonical facts, with explicit valid and recorded time. Counts and amounts are computed by queries, never by the model reading passages.
- **CPQ-03 — Answer contract.** Every answer states its scope, time basis, the ADR-0039 information state (for example `NOT_STATED` or an incomplete package), and structured citations to evidence. When the facts do not support an answer it abstains.
- **CPQ-04 — Document versus accepted.** The answer distinguishes what a document says from what the Brain has accepted (requested versus issued terms under ADR-0038).
- **CPQ-05 — Access.** Rules from ADR-0053: if the user loses access mid-conversation, later turns, history, cached answers and evidence links follow the new policy.
- **CPQ-06 — Hooks.** Persist the master blueprint section 88 `ConversationContext` hook. Display knowledge-gap objects read-only; assigning them as work belongs to F0043.

## Exclusions

No conversation tree, branching, attachments, free-form retrieval, conversation graph, learning or promotion (F0037 to F0042). No agent actions or writes.

## Documents

The PRD, STATUS, GETTING-STARTED, stories and assembly plan are authored by this feature's Phase A/B plan actions. This folder reserves the identifier and carries requirements; no plan approval or runtime delivery is claimed. Authored shard: `planning-mds/kg-source/features/F0069.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
