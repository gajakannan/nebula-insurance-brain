# Plan review report — F0004 content artifact model (re-review)

**Run:** `2026-10-16-b98c71c4` · **Action:** plan-review · **PLAN_SCOPE:** feature · **TARGET:** F0004\
**Product root:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`, branch `docs/f0004-plan-review-rework` (uncommitted; DIFF_RANGE `main`@`99efd49` → working tree)\
**Prior review:** `2026-10-16-a186bc18` (CONDITIONALLY READY) · **Rework plan run:** `2026-10-16-fce2ff91` (approved)\
**Framework executor:** nebula-agents pin `c218bf1`\
**Independence limit:** the rework was written in this same session. This review re-reads raw artifacts and looks for regressions the rework introduced, but a fresh-session or different-tool review is still recommended.

## Decision

**CONDITIONALLY READY.** Findings: 0 critical, 1 high, 1 medium, 1 low. Verdict from `gate_policy.py` (review-family) at PR4.

All nine prior findings are resolved (table below). The rework itself added one high: the new read-path quarantine writes durable rows from a read-authorized request outside `AuthorizationExecution.mutate`. That conflicts with ADR-0062's single-entry-point rule, and no principal or action is defined for the write (R-H1).

## Findings By Severity

| ID | Severity | Owner | Summary | Evidence |
|---|---|---|---|---|
| R-H1 | High | architect | Read-path quarantine writes outside `AuthorizationExecution.mutate`, with no defined action or principal | assembly plan Step 2 item 8 (line 162); `persistence-design.sql:246` and assembly plan line 174 ("no application grant reads or writes" repair records); `brain_security/execution.py:1-12` (the only way to perform a protected operation; the allowed-read flow is evaluate → load → append decision → commit → return) |
| R-M1 | Medium | architect (+PM) | After a Step 1a PASS, any new document with an unattributable item fails publication with no fallback | assembly plan Step 1a pass criteria (line 67), Step 1b item 2 (line 115), compatibility matrix "New source" row (line 270) |
| R-L1 | Low | architect | The state-event guard's same-transaction check depends on unstated insert ordering and defaulted `created_at` | `persistence-design.sql` `f0004_guard_content_artifact` (`e.created_at = now()`) |

### Prior findings (from `2026-10-16-a186bc18`)

| ID | Status | Verified at |
|---|---|---|
| H-1 | Resolved | Step 1a (lines 62-75) with pass criteria, evidence and exit decision; new sources on v1 while `content.v2_writer_enabled=false` (line 270); S0002 provenance gate; ADR-0073 §1/§3 |
| H-2 | Resolved | `publication_state` transitions, `content_artifact_state_event`, guard trigger (persistence-design.sql); Step 2 items 7–8; GET row (line 253); v1 matrix row (line 264); ADR-0073 §2; S0004-AC3 |
| M-1 | Resolved | BLUEPRINT §4.8 "Document-date candidate producer"; PRD Dependencies "Unassigned" row; S0003 Dependencies |
| M-2 | Resolved | `HumanDateSelectionVerifier` and `human_decision_id` (lines 214, 226, 239); schema `human_decision` required; SQL `human_*` columns; S0003-AC6; invalid case `selection-without-human-decision` |
| M-3 | Resolved | `content_repair_record` (persistence-design.sql); migration sequence (line 174); orphan path (line 160) |
| L-1 | Resolved | no remaining "Phase B must" wording in stories, PRD, checklist or worked examples |
| L-2 | Resolved | S0002-AC7 shares S0001-AC6's event |
| L-3 | Resolved | `content_artifact_guard` DDL (pglast parse in plan run fce2ff91) |
| L-4 | Resolved | PRD Role-Based Access; S0004 test row (line 301) |

## Product Readiness

*Owner: product-manager.*

**BRAIN-SCOPE: pass.** The rework kept every AC ID. Its changed criteria (S0002-AC7, S0003-AC6, S0004-AC3) are specific and testable, and the checklist mirrors them exactly. The S0002 provenance gate states the FAIL path: back to the operator, never inferred origin. Rosa's and Ingrid's outcomes still trace to stories. The PRD Dependencies and the BLUEPRINT §4.8 open decision make the "undated until owner assigned" consequence explicit. The §4.11 guard is now stronger (no automated selector).

Trackers: REGISTRY, ROADMAP (regenerated; validation-gate text names the rework run and Step 1a), STATUS, README, STORY-INDEX (unchanged) and the KG shard agree.

**R-M1 is partly a product question.** It is recorded under Architecture with PM input.

## Architecture Readiness

*Owner: architect.*

**Checklist outcomes:**
- **BRAIN-AUTHORITY: pass.** ADR-0073 remains Proposed, and the amendment is attributed to the operator decisions.
- **BRAIN-EVIDENCE: pass.**
- **BRAIN-PARSE-ONCE: pass.** Quarantine never triggers a reparse (Step 2 failure table).
- **BRAIN-TEMPORAL: pass.** Exclusion unchanged; selection history is append-only, with a human basis.
- **BRAIN-EXAMPLES: pass.** 40 cases, glossary "Artifact publication state" row, examples README count updated.
- **BRAIN-AUTHORIZATION: conditional (R-H1).**

**R-H1: the read-path quarantine has no authorized write path.** Step 2 item 8 says a definitive verification failure on read "quarantines the row in its own short transaction, after the read decision is audited". It writes a state event (actor = the reading principal, decision = its read decision), a `content_artifact_quarantined` audit event and a repair record. Its justification is "Quarantine only removes visibility, so the read grant is enough". This leaves three conflicts:

- `brain_security/execution.py` makes `AuthorizationExecution` "the only way an async consumer performs a protected operation". Its allowed-read flow ends at commit → return, with no mutation in the unit of work. A second write transaction from the API read path is therefore outside both `read` and `mutate`.
- Using a read decision ID as the authority for a durable write blurs ADR-0062's read/mutate separation.
- The SQL and migration text say "no application grant reads or writes" repair records, but the API read path writes one.

An implementer must invent the principal, the action and the unit of work for this write. For example: a system ServicePrincipal acting through `mutate` with `content_artifact:ingest`; a new internal action; or recording the failure and leaving the transition to an operator or DevOps job. This touches authorization, so it is build-critical. **Route:** the architect picks one, records it in Step 2 item 8 and ADR-0073 §2, aligns the repair-record ownership wording, and gets Security Reviewer confirmation.

**R-M1: no per-document fallback once v2 is enabled.** Step 1a can PASS while the adapter still returns `ORIGIN_UNAVAILABLE` for some mixed-page items (line 67). With v2 enabled, origin failure "fails that publication instead of silently downgrading it to v1" (line 270). So after PASS, every new document with even one unattributable item becomes unpublishable. It gets failed-attempt diagnostics only: no repair record and no fallback. The behavior is specified, so this isn't build-critical, but the operator decision ("keep v1 until proven") didn't address it. **Route:** the operator chooses between two options, and the architect records the choice:
- tighten PASS to require full attribution on representative mixed fixtures;
- allow a per-document v1 fallback with a recorded reason.

**R-L1:** the guard's `EXISTS … e.created_at = now()` proves same-transaction only if the event is inserted before the `UPDATE` and `created_at` is left to its default. State that ordering in the SQL comment or the Step 2 text.

**KG alignment:** the shard and its compiled projections match. Coverage was regenerated and PR2 drift passes.

## Buildability Challenge

*Owner: code-reviewer.*

**BRAIN-BUILDABILITY: conditional (R-H1).** Step 1a now comes first, with a named test file, fixtures, pass criteria and an owner for the exit decision. The build path no longer has an unresolved fork for new sources. The migration states have a test suite (`test_content_migration_states.py`) covering:
- v1 reads before, during and after the backfill;
- quarantine and the transient-error case;
- a blocked backfill;
- guard rejection.

The date-selection rejection cases are in S0003's row. Role ownership is unchanged and explicit.

The remaining blocker is R-H1: the API read route can't be implemented without inventing an authorization path for the quarantine write. R-M1 affects F0005 throughput expectations after activation, not F0004's buildability.

## Validation Evidence

| Validator | Exit | Summary |
|---|---|---|
| `validate-stories.py {FEATURE_PATH}` | 0 | PASS |
| `validate-trackers.py` | 0 | PASS |
| `scripts/kg/validate.py` | 0 | PASS |
| `scripts/kg/validate.py --check-drift` | 0 | PASS: no drift |
| `validate_templates.py` | 0 | PASS |
| Project check `plan-readiness` (run-gate `before_stage_complete`) | 0 | pass, 0 findings; `artifacts/project-checks/PR2-plan-readiness-e401cef96ba2464088241551522d7ac3.*` |
| Supplementary: `validate-contract-examples.py` | 0 | 40 cases (18 valid / 22 invalid), 0 failures; `artifacts/test-results/contract-examples.json` |

Validators confirm structure only. R-H1 was found by reading the AuthX source, not by any validator.

## Artifact Trace

Read (raw):
- `git diff main` of the 22 rework files, all F0004 feature files
- ADR-0073
- `persistence-design.sql`
- `schemas/document-date-record.schema.json`, `contract-examples.json`
- `api/brain-api.yaml` 409 text
- BLUEPRINT §4.8, glossary F0004 rows, `examples/README.md`
- `kg-source/features/F0004.yaml`, ROADMAP F0004 row, `coverage-report.yaml` diff stat
- `engine/packages/brain-security/src/brain_security/execution.py` (module docstring; read/mutate)
- plan run `2026-10-16-fce2ff91` action-context and gate decisions

Written: only this run folder.
