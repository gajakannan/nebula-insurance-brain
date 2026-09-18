# F0005 — One-time document ingestion — PRD

## Feature Header

**Feature ID:** F0005
**Feature Name:** One-time document ingestion
**Priority:** High
**Phase:** v0.1A
**Status:** Draft — direction authorized; no completed plan gates, implementation, or proof acceptance claimed.

## Feature Statement

**As a** document intelligence engineer
**I want** durable ingestion and repeatable interpretation of saved native content
**So that** model failures and profile changes do not repeat published parsing or lose source evidence.

## Business Objective

Evaluate and integrate Docling-Graph without weakening parse reuse, evidence fidelity, tenant boundaries, or canonical authority. The current measured baseline uses Docling and a direct full-document vLLM request. The proposed replacement delegates extraction coordination while retaining Nebula contracts.

## Scope & Boundaries

**In scope:** exact-version proof, native/scanned processing, source and artifact persistence, durable job recovery/idempotency, two saved-JSON profile runs, evidence translation, local model configuration, operational limits, comparative evaluation, and activation only after proof acceptance.

**Out of scope:** full F0015 profile compiler, F0016 production run service, F0032 evolution scheduler, F0017 enterprise resolution, canonical acceptance, AGE loading, review UX implementation, and Temporal. Fixed templates and the existing result contract support this feature's proof; downstream features reuse it.

## Acceptance Criteria Overview

- [ ] S0001 identifies the exact upstream code and exposes native conversion plus quality before extraction can fail.
- [ ] S0002 publishes the original source and six-file bundle durably; retries after publication never reconvert; partial and incomplete results remain distinguishable.
- [ ] S0003 proves saved-JSON reuse after restart and maps insurer-critical property/relationship evidence without fabricated precision.
- [ ] S0004 measures schema validity, accuracy, abstention, calls/tokens, latency, and review burden against the direct-client baseline on agreed expected cases.
- [ ] Timeouts, invalid output, partial conversion, duplicate/competing jobs, cancellation, tenant denial, bounded concurrency, secret handling, and provenance retention pass.
- [ ] Exact dependencies, runtime wiring, version metadata, and the lockfile change only with the proven candidate; ADR-0060 remains Proposed until its mandatory proof gates pass.

## UX / Screens

No new user interface. Existing job status and evidence consumers must distinguish pending, partial, failed, and completed work without treating a failed extraction as missing source evidence. Native review remains F0022.

## Data Requirements

Keep separate source, content artifact, and interpretation identities (ADR-0004). Docling parser/configuration identifies conversion; Graph revision/template/chunking/model configuration identifies interpretation. Graph chunks and provenance belong to the run. Use ContentArtifactStore and strict versioned manifests; preserve old bundles. The [assembly plan](feature-assembly-plan.md) specifies the adapter-to-bundle handoff.

## Dependencies

F0004 artifact contract; F0001 fixtures and historical results; F0002/F0003 production authorization and persistence; ADR-0003/0004/0040/0055/0058/0059 and proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Production compilation and evolution depend on this proof, not vice versa. Temporal remains v0.3.

## Risks and Open Decisions

The exact upstream build, supported pre-extraction checkpoint seam, quality/cost thresholds, licensed comparison corpus, and named reviewers remain unsettled. They are implementation/proof prerequisites owned in the assembly plan, not implied approvals. A version string or successful graph export alone proves neither reuse nor source grounding.

## Success and Evidence

Actual package/model runs, failure injection, comparison results, and reviewer verdicts are required. Structural documentation checks validate this planning package only. See [STATUS](STATUS.md) for the recommendation-by-recommendation audit and remaining work.
