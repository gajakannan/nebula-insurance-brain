# F0001 — Repository and Engineering Foundation — PRD

## Feature Header

**Feature ID:** F0001
**Feature Name:** Repository and engineering foundation
**Priority:** Critical
**Phase:** Infrastructure
**Status:** Draft

## Feature Statement

**As a** platform engineer standing up Nebula Insurance Brain
**I want** the runtime roots, local dependency stack, and the four pre-build contract proofs delivered and recorded
**So that** every v0.1 feature builds on a repository whose gates already run and on contracts that were proven against the real Docling, PostgreSQL, and authentik dependencies before they froze.

## Business Objective

- **Goal:** Convert master blueprint section 115.4 from "proofs required before the respective contracts are frozen" into recorded results, and section 106.2 P0 items into settled contracts, before F0002 starts.
- **Metric:** Four proofs executed with measured outcomes recorded in ADR-0040, ADR-0041, ADR-0044, ADR-0049, and ADR-0050; each moves from Proposed to Accepted or amended.
- **Baseline:** Zero runtime code; all five ADRs Proposed; dependency matrix unspecified (section 114.3).
- **Target:** Repository gates green in CI on every PR; dependency matrix pinned; proof results recorded; open decisions 3 and 4 of section 117.1 answered.

## Problem Statement

- **Current State:** The architecture is documented but unproven. Docling-Graph reuse, the native review round trip and its evidence anchoring, the two-range bitemporal commit, and the authentik plus Casbin access path are assumptions on paper. There is no toolchain, no containers, no CI for runtime code.
- **Desired State:** A fresh clone installs, starts its dependencies, runs its gates, and carries four small proof harnesses whose measured results are recorded where later features can rely on them.
- **Impact:** Without the proofs, F0004 to F0009 and F0018 to F0022 would freeze contracts on unverified behavior; section 106.2 marks these as P0 because rework there invalidates persisted artifacts and audit history.

## Scope & Boundaries

**In Scope:**
- `engine/` and `neuron/` runtime roots with a uv workspace, a FastAPI application skeleton with a health endpoint, Alembic, lint, type-check, and test configuration, and CI wiring (S0001)
- Local containers for PostgreSQL with pgvector and Apache AGE and authentik, plus the committed local filesystem content-artifact store configuration and pinned dependency matrix (S0002)
- Proof 1: parse once with Docling, reinterpret with two profiles through Docling-Graph, evidence resolves (S0003)
- Proof 2: native review round trip with duplicate and stale submissions rejected, unresolved evidence blocked, and lineage preserved (S0004)
- Proof 3: bitemporal commit under retroactive and concurrent change (S0005)
- Proof 4: access boundaries across two security scopes, revocation, the exact extension build, and a timed restore (S0006)
- Recording proof outcomes into the governing ADRs and the dependency matrix (S0007)

**Out of Scope:**
- The React semantic shell and session transport (F0021)
- The production canonical commit service and permission catalog (F0002, F0018)
- Entity resolution, projections, chat, learning (F0017, F0033 onward)
- Temporal, Qdrant, Kubernetes, any production hosting decision beyond what the proofs require (sections 89, 94)
- The Golden Corpus beyond the single GL package the proofs need (F0026)

## Acceptance Criteria Overview

- [ ] A fresh clone installs both Python workspaces, starts all containers, and passes the product gates and the runtime test suites in CI.
- [ ] Proof 1 shows a second interpretation with zero conversion or OCR calls and citations resolving to immutable blocks with declared precision.
- [ ] Proof 2 corrects a deliberately wrong limit exactly once; replayed and stale callbacks are rejected; the original assertion remains readable.
- [ ] Proof 3 answers the section 87 questions at every valid-time and recorded-time coordinate; concurrent commits cannot create ambiguous accepted state.
- [ ] Proof 4 verifies credentials before storage access, denies cross-scope object and review access, propagates revocation, installs the pinned extension build, and restores from backup with citations intact.
- [ ] Every proof's results and limitations are recorded in its governing ADR and the dependency matrix is complete.

## UX / Screens

Minimal UI. This feature delivers engineering infrastructure and proof harnesses exercised through tests and CLI commands, plus the proof-scope Nebula Review Panel that S0004 needs (ADR-0057). The full application shell and Document 360 arrive with F0021 to F0023.

## Screen Layouts (ASCII)

Limited to the proof-scope Review Panel in S0004: an artifact rail, a rendered viewport with anchored regions, a field list with per-field actions, and batch submission. No other Nebula screen, zone, or flow is introduced.

## Data Requirements

**Core Entities:**
- Content Artifact: the parse-once bundle including the native DoclingDocument JSON, normalized projections, and manifest with parser identity and hashes (sections 80, 81, 108.1)
- Semantic Interpretation Run and Interpretation Result: versioned run configuration, candidate assertions, evidence bindings with declared precision (section 108.3)
- Review Item, Review Batch, Evidence Locator, Review Decision: the native review round trip records (sections 75, 125)
- Fact Slot, Canonical Fact Version, Canonical Fact Change, Outbox Event: the bitemporal commit proof records (sections 13, 14, 16, 109)
- Principal, Membership, Audit Event: the access proof records (sections 65, 66)

**Validation Rules:**
- Every artifact file carries a sha256 and the manifest records parser package version and configuration hash.
- Valid-time and recorded-time ranges are non-empty and non-null; overlapping ranges on the same slot are rejected at the database.
- Webhook payloads are persisted with their hash before translation; duplicate hashes are rejected.

**Data Relationships:**
- Document Version → Content Artifact (one accepted artifact per source version and parser recipe)
- Content Artifact → Interpretation Run (many) → Assertion (many) → Review Item (optional) → Review Decision
- Fact Slot → Canonical Fact Version (many, bitemporal) → Canonical Fact Change (reason)

## Role-Based Access

| Role | Access Level | Notes |
|------|-------------|-------|
| Platform engineer (developer) | Run containers, tests, and proof harnesses locally and in CI | No production data |
| Document intelligence engineer | Run ingestion and interpretation proofs; read artifacts in the dev object store | Same tenant scope as the proof fixture |
| Persistence engineer | Run commit proof against the dev database | Service principal for the worker |
| Business reviewer | Review a batch in the Nebula Review Panel as their verified session principal | Adjudication only; no canonical approval authority (section 111.2) |
| CI runner | Execute gates and suites read-only against ephemeral services | No secrets beyond ephemeral service credentials |

## Success Criteria

- CI product-gates job passes on the F0001 closeout commit with runtime suites included.
- Each of the four proofs has a pass record with measured values in its ADR.
- The dependency matrix pins Python, PostgreSQL major and minor, AGE build, pgvector, Docling, Docling-Graph, and the `pdf.js` and `fflate` versions the Review Panel renders with.
- Section 117.1 decisions 3 and 4 are answered in BLUEPRINT section 2 and section 4.8.

## Risks & Assumptions

- Risk: the Brain now owns document rendering fidelity, and real submission packages bring scanned pages with no text layer, rotated pages, fragmented PDF text items, and spreadsheet headers that are not row 1; mitigation is that unresolved anchors block the decision rather than misplacing it (ADR-0058), and S0004 proves that path deliberately.
- Risk: the PostgreSQL major version and the AGE build are incompatible on the intended host; mitigation is to pin and test one exact combination in S0002 and S0006 (section 114.3).
- Risk: Docling-Graph's grounding precision differs across extraction modes; mitigation is to record precision per binding rather than assume span level (section 108.2).
- Risk: Phi-4-mini-instruct's 4,096-token context was validated by the CRM for short structured calls, not for document chunks; mitigation is client-side context enforcement and a recorded adequacy result in ADR-0040, with an alternative backend proposed at Phase B if needed.
- Decided at the clarification gate (2026-09-06), amended 2026-09-08 by ADR-0057 (native Review Panel replaces Label Studio): PostgreSQL 18 with fallback to 17 only on AGE build failure; the extraction model is `microsoft/Phi-4-mini-instruct` served by vLLM on the host GPU, the profile the CRM validated in its ADR-035 (verified: the CRM runs Phi, not Mistral; Ollama is an unwired seam there); proofs run in local Docker Compose with the inference service on the host.
- Settled at Phase B by ADR-0059: the provider-neutral artifact-storage ports are implemented initially by `LocalFilesystemObjectStore`; cloud adapters remain future work. Docling-Graph pin, authentik version, and webhook trust mechanism remain open.
- Assumption: a licensed GL policy package is supplied by the operator before S0003; otherwise the Architect selects a synthetic package (section 117.1 item 5).

## Dependencies

- Master blueprint sections 106.2, 108, 109.2, 109.3, 111.1, 114.1, 114.3, 115.4, 117.1, 120.1, 121.2
- ADR-0001, ADR-0003, ADR-0007, ADR-0008, ADR-0010, ADR-0034, ADR-0037, ADR-0059 (Accepted); ADR-0040, ADR-0041, ADR-0044, ADR-0049, ADR-0050 (Proposed, settled by S0007)
- Open decisions from section 117.1: target host and extension build, model-provider data policy, Docling-Graph pin, sample package availability

## Related Stories

Stories are colocated in this feature folder as `F0001-S000N-{slug}.md`.

- [F0001-S0001] - Runtime roots and toolchain skeleton
- [F0001-S0002] - Local runtime containers and dependency matrix
- [F0001-S0003] - Proof: parse once, reinterpret twice, evidence resolves
- [F0001-S0004] - Proof: native review round trip with lineage
- [F0001-S0005] - Proof: bitemporal commit under retroactive and concurrent change
- [F0001-S0006] - Proof: access boundaries, extension build, and restore
- [F0001-S0007] - Record proof outcomes and settle the pre-build contracts

## Architecture Traceability (Phase B)

| Story | Capabilities | Governing ADRs | Contracts |
|-------|--------------|----------------|-----------|
| S0001 | runtime-roots-and-toolchain | ADR-0054 | `api/brain-api.yaml` (`/health`), `schemas/problem-details` |
| S0002 | local-dependency-stack, local-inference-service | ADR-0054, ADR-0055 | `docker/DEPENDENCY-MATRIX.md`, `docker/local-inference-runbook.md` |
| S0003 | parse-once-content-artifact, semantic-interpretation-run | ADR-0003, 0004, 0016, 0035, 0040, 0055 | `schemas/content-artifact-manifest`, `schemas/interpretation-result` |
| S0004 | evidence-review-round-trip | ADR-0034, 0037, 0044 | `schemas/review-decision`, webhook and review-item endpoints |
| S0005 | bitemporal-canonical-commit | ADR-0007, 0008, 0009, 0041 | `schemas/canonical-commit-request` and `-response`, fact endpoints |
| S0006 | credential-verification-and-principal-resolution, authorization-enforcement, backup-and-restore | ADR-0049, 0050 | `security/policies/{model.conf,policy.csv}` |
| S0007 | (documentation) | ADR-0040, 0041, 0044, 0049, 0050 | ADR result tables |

## Solution Design Summary (Phase B)

The assembly plan (`feature-assembly-plan.md`) orders eight build steps: toolchain, stack, identity and authorization core, parse-once proof, bitemporal commit proof, review round trip, restore drill, and outcome recording. Architecture decisions new to this feature are ADR-0054 (layout and topology) and ADR-0055 (local inference profile); patterns are seeded in `architecture/SOLUTION-PATTERNS.md`.

## Rollout & Enablement

- Developer onboarding is `GETTING-STARTED.md` in this folder; the root README links to it.
- No feature flag; the feature is infrastructure.
