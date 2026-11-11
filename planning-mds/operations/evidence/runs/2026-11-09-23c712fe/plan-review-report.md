# F0007 amended plan review

## Decision

**READY — substantive review: 0 Critical, 0 High, 0 open Medium/Low findings.** The amended package now lets an implementation agent perform the bounded remediation without inventing identity, authorization, validation, rollback or test rules. The primary coordinator must attach successful PR2 results and the `review-family` PR4 calculation before marking this action complete; this reviewer does not infer those procedural results from a semantic review.

Target: `planning-mds/features/F0007-factslot-model`, reopened active package, branch `fix/f0007-review-remediation`, baseline `fa8fc1d` through the current working tree. Original approved plan: `2026-11-09-60865e32`. Current authorized remediation candidate: `2026-11-09-81798e61`. This fresh reviewer did not implement the fixes or edit the plan. Proposed ADRs remain Proposed.

## Findings By Severity

No open substantive readiness finding remains after the owner corrected the handoff documentation identified during this review. Final validator failures, if any, remain independent gate blockers and must be addressed before the action is declared complete.

| Prior finding | Disposition | Raw current evidence |
|---|---|---|
| PR-H1: missing member-value invariant and rejection contract | Resolved in plan | Assembly plan “Answer Validation at the Existing Commit”, lines 287–292: PRESENT MEMBER value must derive the immutable stored key under the pinned predicate contract; `MEMBER_VALUE_MISMATCH`; zero versions/commits/outbox; authorization and evidence checks precede detail. Remediation section line 419 requires entity/name/identifier negatives and canonical-equivalence positives. |
| PR-H2: identity CHECK accepts SQL UNKNOWN | Resolved in plan | Assembly plan lines 186–205 explicitly requires the complete legacy/v1 expression `IS TRUE`, with mandatory v1 fields non-null. Remediation line 420 specifies follow-up0013 after immutable0012, locked refusal-only inventory, atomic constraint replacement, exact prior guard on downgrade and owned-PostgreSQL negative/round-trip proofs. |
| Current setup/status drift discovered during re-review | Corrected by owner, not this reviewer | GETTING-STARTED line 3 names current remediation; lines 48–65 remove obsolete head0011/renumber0012 instructions and state correct lineage, guarded rollout and semantic rules. STATUS lines 23/50 separate current progress from prior completion provenance. Assembly plan line 5 and Rollout section lines 345–350 now describe remediation and preserve original history. |

The numeric carrier and protected-read clarifications also have explicit contracts: the assembly plan line 288 and schema descriptions use a common 64-character total bound including sign/point, require checking canonical length before expansion and require accepted canonical reload idempotence. The remediation section line 421 defines one private payload selection, payload-derived dependencies, current-authority locking, final rechecks, durable audit and one commit before return. These restore existing requirements and introduce no new product scope.

## Product Readiness

The PRD states user value, explicit MVP scope, exclusions, personas and measurable success criteria; the six stories have 39 named ACs and internal mutation contracts. No UI is explicitly justified in PRD “UX / Screens” and “Screen Layouts (ASCII)”. The active README, story headers, STATUS, blueprint, registry/roadmap and authored feature shard now identify remediation as In Progress; original plan/completion records remain history rather than current signoff.

The clarified work fits the original stable identity, typed value, scoped absence, evidence-bound names and pilot preservation requirements. It adds no insurance business rule, user role, grant, route, producer, display precedence or currency-conversion behavior. Deferrals to F0008, F0011, F0012/F0013, F0016, F0017/F0023, F0018 and F0026 remain explicit and owned. Formal ADR acceptance is not inferred from remediation authorization or passing tests.

## Architecture Readiness

Raw requirements and contracts define the slot/header/member/relationship shapes, pinned predicate contract, authoritative qualifier normalization, immutability, tenant/KB ownership, audit boundaries, legacy handling and named rejection behavior. The current SQL invariant removes the NULL ambiguity in the earlier plan. The member-value boundary now prevents divergent canonical values on one immutable member identity. Numeric input/output/schema limits agree; the plan explicitly distinguishes semantic expansion validation from the schema's input-shape bound.

The existing commit interface remains intact with lowercase 422 rejection codes documented in `planning-mds/api/brain-api.yaml:295`. Protected reads retain non-disclosing denial and current grant semantics while authorizing the exact selected envelope's scope in one unit of work. The migration plan preserves shipped0012 and existing evidence; detected historical corruption requires explicit governed resolution, not fabricated/deleted data. Pilot version-table DDL and temporal close remain with F0008. The current feature path/shard and KG routing agree; root-owned final KG validator and binding reconciliation evidence is still required for lifecycle completion.

### Brain review criteria

| Rule | Outcome | Feature-specific planning evidence |
|---|---|---|
| BRAIN-SCOPE | Pass | PRD Scope & Boundaries, Acceptance Criteria Overview, six story AC sections; remediation section explicitly limits the seven findings. |
| BRAIN-AUTHORITY | Pass | PRD Risks & Assumptions; ADR-0077 Status/Design review/Formal acceptance and remediation clarification; no Proposed ADR is accepted by inference. |
| BRAIN-EVIDENCE | Pass | S0003 absence scope/denial ACs; S0005 admitted-evidence name requirements; assembly plan Answer Validation and exact-scope read rules. |
| BRAIN-PARSE-ONCE | Not applicable to new parsing | No parsing, ingestion or producer activation is added. References to accepted artifacts and admitted evidence are reused; no content is reparsed or replaced. |
| BRAIN-TEMPORAL | Pass within explicit boundary | S0002 AC2/AC5; S0006 AC1/AC6; per-member existing exclusion, byte-preserving migration/rollback, F0008 ownership of close/supersession. |
| BRAIN-AUTHORIZATION | Pass at plan level | PRD Role-Based Access; S0001 AC5/AC7, S0003 AC6, S0006 AC4/AC7; assembly plan current-authority private-payload dependency checks and exact-version/revocation negative proof plan. |
| BRAIN-BUILDABILITY | Pass | Existing file/handoff tables, unchanged role matrix, remediation owners and explicit new guard/rejection/bounds/read sequence; no build-critical owner is missing. |
| BRAIN-EXAMPLES | Pass for planning | Glossary FactSlot/information state/money/identifier definitions; worked-examples and contract-examples; EX-OWN-003/EX-SEM-008 references and frozen-holdout separation; remediation names exact member, decimal-boundary, NULL-field and revocation runtime proofs. Structured example validation remains a required recorded check, not proof inferred from prose. |

## Buildability Challenge

Backend owns the value/member/authorization and migration implementation; Architect owns shared invariants, reason/schema and binding alignment; QE owns AC-derived negative/positive, concurrency, round-trip and regression proof; Code/Security reviewers own independent quality/authorization assessments; DevOps owns migration/runtime deployability. No frontend/AI implementation is needed. The appendix defines enough method sequencing and expected effects to avoid speculative implementation.

Existing system scope is preserved, including no new producer activation or RLS enablement. Historical data inventory is an explicit rollout prerequisite, and invalid rows block rollout rather than silently changing evidence. The current getting-started instructions name immutable0012/new0013 and the new regression files. An assembly plan was inspected because one exists; this action does not demand it as an additional plan deliverable.

## Validation Evidence

Reviewer-generated evidence:

- `artifacts/scope-routing.txt` — current F0007 routing resolves unambiguously to the active package; raw files were inspected directly.
- `artifacts/amended-handoff-citations.txt` — corrected setup/status/rollout and remediation contract citations.
- `artifacts/feature-document-link-check.txt` — 59 local feature Markdown links checked, zero missing targets.

Primary coordinator owns required PR2 framework operations: current planning approvals, all six story files, trackers, KG integrity, KG drift, templates, plus the required local `plan-readiness` check. **PR2 PASS:** all six framework validators and the required product-local plan-readiness extension passed in the gate driver. Raw output: artifacts/plan-pr2.txt; operation records: lifecycle-gates.log and gate-state.json. PR3 completed, and review-family PR4 computed READY with0 Critical/High in artifacts/plan-readiness-verdict.txt. No runtime pass, original approval token, summary or prior checklist is treated as proof those checks have passed for this action. Fresh feature runtime tests and security scans are separate implementation evidence and are not invented as plan prerequisites.

PR3 substantive self-review rechecked exact contracts, corrected owner changes and read-only scope, reconciled duplicates and stated exclusions. PR4 used zero Critical/High counts after successful required validation; no missing-owner override applies.

## Artifact Trace

See `artifact-trace.md` and `commands.log`. Reviewed active F0007 raw planning/story/setup/status files, governing ADR-0077, schema and API mapping, local Brain checklist, examples/glossary links, authored shard and tracker state. No original report, completion evidence, source, plan, schema, KG or tracker was repaired by this reviewer. All writes are within this new base plan-review run, apart from its temporary `/tmp` command runner. Documentation corrections were performed by the owning primary coordinator and independently reread here.
