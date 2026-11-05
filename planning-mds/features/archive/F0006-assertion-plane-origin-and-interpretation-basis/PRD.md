# F0006 — Assertion plane + origin + interpretation basis

**Feature ID:** F0006
**Feature Name:** Assertion plane + origin + interpretation basis
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Phase A+B approved by operator on 2026-11-01; implementation not started
**Plan Run:** `2026-11-01-7d6d19ce` (A+B, new); Phase B rework `2026-11-01-512e9303` (requirements unchanged)

## Feature Statement

**As a** document intelligence engineer and business reviewer
**I want** source claims to retain their meaning, evidence, origin, and interpretation basis before acceptance
**So that** competing claims remain inspectable and unsupported or conditional claims cannot silently become accepted facts.

## Business Objective

- Goal: establish the assertion contract between persisted content and governed canonical acceptance.
- Baseline: F0001–F0005 supply a working typed-candidate importer, assertion/evidence persistence, and additive review corrections. They do not deliver the complete section 11 model or the statement/admission amendment.
- Target: all 35 story acceptance criteria pass, every negative fixture has an explicit outcome, and legacy compatibility fixtures retain their identities and evidence. No canonical write is caused by assertion admission alone.
- Evidence: PostgreSQL round trips and ownership failures; versioned payload validation; server-location fixtures; existing importer/review/commit regression cases. Planning checks do not establish runtime delivery.

## Problem Statement

A source claim is distinct from accepted knowledge. Two declarations can disagree without either disappearing. An extraction's confidence cannot replace its evidence, the origin of the claim, or how directly the evidence supports it. Conditional wording and a model's description of a chart need explicit safeguards before downstream acceptance.

## Scope & Boundaries

**In Scope (Must, MVP):**

1. Typed assertion records preserving subject candidate, ontology property/release, value or object, qualifiers, claimed valid time, evidence, run/source identity, creation actor/time, fact mode, assertion origin, interpretation basis, and supplied confidence.
2. Storage and contract support for `OPEN_STATEMENT`: source relation phrase, subject, object or literal, role-word qualifiers, time-mention references, mandatory quote, no predicate, and `EXPLICIT` basis. Open extraction and signature alignment remain later work.
3. Structural admission service contract and executable checks: quote-in-block, name-in-quote, time-words-in-quote, duplicate name ownership within the document, subject references, literal-object signal, malformed/truncated/uninterpreted output, and server-computed selectors at honest precision.
4. Storage/contract safeguards and review hooks for mood and evidence origin. Mood-bearing claims are ineligible for canonical facts. Described-only evidence cannot auto-accept, close, or supersede a fact; it requires `DESCRIBED_EVIDENCE` review. Operative provisions of an issued policy remain facts about that contract.
5. A versioned addition alongside the existing strict interpretation-result schema, compatible readers, and regression protection for existing import, review, and commit paths.

**Out of Scope:**

- Open extraction, signature decisions/bindings, implication rules, and typed materialization (F0066).
- Full interpretation-run orchestration, durable `interpretation_drop` records/counts, PARTIAL transitions, and time-mention production/resolution (F0016). F0006 supplies outcomes these consumers must persist; it does not claim these behaviours delivered.
- New FactSlots, canonical bitemporal storage/resolution, supersession algorithms, and full commit orchestration (F0007–F0010/F0017–F0019).
- Review screens and drop/origin display (F0022), production qualification (F0026), normative/subjectivity/scenario execution (F0052/F0053), automated deciders, fingerprint scheduling, or action dispatch.
- Pipeline selection, provider controls, v2 content publication, activation of Docling-Graph, or new permission grants. F0005 closed on the rejection branch: `direct-baseline` and the v1 writer remain default.

## Personas

See [personas.md](personas.md): Mateo owns claim/evidence fidelity; Ingrid owns durable scoped records; Rosa needs retained source and correction history. These are existing personas, not new access roles.

## Acceptance Criteria Overview

- Both assertion kinds round-trip without conflating mode, origin, basis, text origin, or confidence.
- Competing assertions coexist; creating either kind never creates canonical truth.
- Admission checks expose every rejected or signalled item with its specified reason and evidence scope.
- Mood, described-only evidence, and open statements cannot bypass canonical eligibility checks through a legacy consumer.
- Existing valid payloads and correction chains remain readable; no fabricated quote, release, precision, or provenance is backfilled.

The [acceptance checklist](acceptance-criteria-checklist.md) maps each criterion to a story and required runtime evidence.

## UX / Screens

No new or materially changed UI. The surface is an authorized internal service/consumer contract. Existing Review Panel behaviour is regression-tested; F0022 owns the new origin, mood, and drop display. Hooks must retain the required data for it.

## Screen Layouts (ASCII)

No UI — assertion storage, admission contracts, and existing-consumer compatibility only. No new screen, zone, or user editing flow is introduced.

## Data Requirements

- Fact mode: `ASSERTED`, `OBSERVED`, `DERIVED` only.
- Assertion origin: `DOCUMENT_INTERPRETATION`, `SYSTEM_OBSERVATION`, `HUMAN_REVIEW`, `CONVERSATION_DISCOVERY`, `RULE_DERIVATION`, `AGENT_ANALYSIS` (master blueprint §11). Representing an origin does not enable its future producer.
- Interpretation basis: `EXPLICIT`, `INFERRED`, `AMBIGUOUS`; independent of mode and supplied confidence. Open statements are `EXPLICIT`.
- Evidence text origin is inherited from its F0004 block; it is distinct from assertion origin. Preserve F0004's legacy/unqualified provenance rather than asserting a legacy block was qualified.
- Every authoritative reference must respect tenant and knowledge-base ownership; a claim's time is not a canonical bitemporal fact interval.
- Admission outcomes name run/block, reason, model/prompt identity and raw-item hash; protected excerpts must remain within existing source-access restrictions. F0016 owns durable drop storage.
- Existing runtime origin `MACHINE_EXTRACTION` differs from the section 11 vocabulary. Phase B must define a compatible mapping retaining original provenance, without rewriting evidence or correction history.

## Role-Based Access

Use the verified principal and typed resource scope from F0002. Existing authorized service principals may import within their granted scope; reviewers may append corrections through the existing review service. These jobs do not confer canonical approval. Cross-tenant/KB reference attempts and unauthorized mutations must be denied with zero assertion/canonical effects; existing authorization decision audit remains in force. No broker/MGA access or new grants are introduced.

## Success Criteria

- All 35 ACs pass with observed evidence in the later feature run.
- Zero unauthorized rows/references or rejected-candidate assertion rows in the negative cases.
- Zero physical conversion/OCR calls during assertion admission or replay.
- At least 80% changed-code coverage in implementation, with PostgreSQL and existing-consumer tests in addition to unit checks. No new extraction-quality or latency threshold is invented here.

## Risks & Assumptions

- ADR-0063 is accepted direction; ADR-0065 remains Proposed. F0006 implements only the authorized storage/contracts/checks/hooks, not formal acceptance of the broader ADR.
- Grounding is structural: a genuine quote containing $500,000 can still accompany a misread $5,000,000 value. Admission does not replace semantic review (EX-SEM-005b).
- Repeated text and normalization cannot justify invented span offsets. Phase B owns normalization, ambiguity policy, selector crosswalk, schema version strategy, and legacy migration mechanics, constrained by these requirements.
- Compatibility must not silently qualify old claims. Unsupported new semantics fail closed at old boundaries; compatible legacy records remain usable under their existing review/commit rules.

## Dependencies

Direct delivered foundations: [F0001](../F0001-repository-and-engineering-foundation/README.md), [F0002](../F0002-tenancy-aware-domain-kernel-and-principal-contracts/README.md), [F0003](../F0003-postgresql-persistence/README.md), [F0004](../F0004-content-artifact-model/README.md), [F0005](../F0005-one-time-docling-ingestion/README.md). F0005 is a compatibility dependency, not a requirement to activate its rejected pipeline.

Future consumers are F0007/F0009/F0010/F0015–F0018/F0022/F0026/F0065/F0066 and F0052/F0053. Their undelivered implementations do not block the bounded F0006 contract; their integration obligations remain explicit. Dependency evidence and audit-pending qualifications live in the plan run's `artifact-trace.md`.

## Related Stories

| Story | Outcome | ACs |
|---|---|---|
| [F0006-S0001](F0006-S0001-preserve-typed-source-claims.md) | Durable typed claims with independent dimensions | 7 |
| [F0006-S0002](F0006-S0002-retain-open-statements-and-version-contracts.md) | Open storage and compatible versioned payloads | 7 |
| [F0006-S0003](F0006-S0003-check-structural-admission-and-evidence.md) | Structural admission and honest server selectors | 8 |
| [F0006-S0004](F0006-S0004-guard-mood-and-described-evidence.md) | Eligibility safeguards and review hooks | 6 |
| [F0006-S0005](F0006-S0005-preserve-existing-consumer-boundaries.md) | Legacy integration and append-only compatibility | 7 |

## Rollout & Enablement

Phase B must specify the additive migration, compatibility/readers, guarded consumer integration, and rollback boundary before implementation. Existing defaults stay active. Fixture/harness support for new kinds is not activation of a live open-statement producer. Reuse synthetic EX-GL-001 and EX-SEM-001/005–007; keep development fixtures outside the frozen holdout. Runtime delivery must compare independently authored expectations against observed outcomes.

## Source Traceability

[BLUEPRINT](../../../BLUEPRINT.md) §§0–4.11; [master blueprint](../../../architecture/master-blueprint.md) §§11, 17, 28, 76, 95; accepted [ADR-0005](../../../architecture/decisions/ADR-0005-three-plane-knowledge-model.md), [ADR-0035](../../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md), [ADR-0063](../../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md); proposed [ADR-0065](../../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md); the dated scope amendment in [README](README.md); strict [existing result schema](../../../schemas/interpretation-result.schema.json); [F0005 closeout](../F0005-one-time-docling-ingestion/STATUS.md) and accepted [ADR-0074](../../../architecture/decisions/ADR-0074-local-document-job-execution-controls.md). No external business authority or new insurance rule is asserted.

## Architecture Traceability (Architect, Phase B approved 2026-11-01)

The [assembly plan](feature-assembly-plan.md) maps every AC to contract/storage/service/consumer proof. [ADR-0075](../../../architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md) resolves schema dispatch, additive storage, labelled legacy-origin projection, quote normalization, current consumer guards and rollback. The current pilot commit's unregistered legacy evidence references remain an explicit compatibility boundary; F0018 owns complete source/provenance orchestration. F0006's new-claim restrictions apply to attributable v2 evidence and review/correction lineage without changing the approved Phase A scope.

New design schemas: [candidate v2](../../../schemas/assertion-record-v2.schema.json), [result v2](../../../schemas/interpretation-result-v2.schema.json), [protected admission result](../../../schemas/assertion-admission-result-v1.schema.json). [Worked examples](worked-examples.md) supply definitions, worked and boundary cases, owning stories/contracts and synthetic provenance. These artifacts do not establish implementation completion or formal acceptance of Proposed ADRs.
