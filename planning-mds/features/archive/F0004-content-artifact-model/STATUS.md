# F0004 — Content artifact model — Status

**Overall Status:** Done\
**Delivery Status:** Done — approved implementation; archive closeout\
**Last Updated:** 2026-10-21\
**Plan Run:** `2026-10-15-bbd8df01`; rework run `2026-10-16-fce2ff91`

## Planning Position

Phase A approved by operator “proceed with Phase B”; G1–G3 passed. Phase B design explicitly approved with `approve-phase-b` on 2026-10-16 after G4 and all seven G5 exit checks passed. The plan is ready for the separate feature action. Registry/roadmap retain Planned/Next. Planning does not authorize implementation or change delivery priority.

Plan-review run `2026-10-16-a186bc18` returned CONDITIONALLY READY (2 high, 3 medium, 4 low). Plan run `2026-10-16-fce2ff91` reworks those findings using four operator decisions (2026-10-16): new sources stay on v1 until per-item provenance is proven; legacy v1 artifacts stay readable through the v1 verifier; the date-candidate producer is an open decision; only a verified human decision may select a date in v0.1. The operator re-approved both phases (`approve-phase-a`, `approve-phase-b`) on 2026-10-16. The plan is ready for the feature action, starting with the Step 1a provenance spike. Re-review run `2026-10-16-b98c71c4` returned CONDITIONALLY READY (R-H1 high, R-M1 medium, R-L1 low). Plan run `2026-10-16-06e0131a` reworks those findings using two operator decisions (2026-10-16): a read only fails, and an operator-run integrity sweep quarantines through `AuthorizationExecution.mutate`; after v2 activation, a document with an unattributable item falls back to v1 with a recorded reason. The operator re-approved both phases (`approve-phase-a`, `approve-phase-b`) on 2026-10-16. A full in-session review found six gaps. Plan run `2026-10-17-620b7618` fixes them: the sweep and backfill are synchronous, so they authorize with `decide` over `SyncAuthorityStore`, with the decision and effects in one transaction, rather than `AuthorizationExecution.mutate`; fallback documents keep the ADR-0073 version ID; the insert order and the orphan authorization key are corrected; the restore-drill lifecycle values with no writer are removed. The operator re-approved both phases on 2026-10-17.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0004-S0001](F0004-S0001-publish-and-reuse-content-bundle.md) | Publish and reuse an immutable content bundle | Done |
| [F0004-S0002](F0004-S0002-content-structure-and-text-origin.md) | Preserve content structure and text origin | Done |
| [F0004-S0003](F0004-S0003-document-date-provenance.md) | Preserve document-date provenance | Done |
| [F0004-S0004](F0004-S0004-authorized-consumers-and-compatibility.md) | Protect artifact consumers and compatibility | Done |

## Story × Role Progress

All four stories passed all required role signoffs and are Done. Contract, projection, persistence, date-history,
authorized-read and operator-job implementation and G2 proofs have passed. No frontend
screen is in scope. Quality Engineer, Code Reviewer, Security Reviewer, DevOps
and Architect acceptance remains required for every story.

Feature action run: `2026-10-17-8a6cc79f`. G0/G1 and the provenance spike passed;
G2 acceptance passed. G3 independent reports pass with recommendations after SEC-H1 and the date-read
race were corrected and independently verified. The ordered G3 validator passed. G4 was explicitly approved on 2026-10-21. G5, G6 and G7 passed; G8 publishes this completed archive. See that run's
action-context.md and test artifacts for the current position.

| Story | Backend | Frontend | AI | QA | DevOps | Code Review | Security | Overall |
|---|---|---|---|---|---|---|---|---|
| F0004-S0001 | PASS | not-in-scope | PASS | PASS | PASS | PASS | PASS | Done |
| F0004-S0002 | PASS | not-in-scope | PASS | PASS | PASS | PASS | PASS | Done |
| F0004-S0003 | PASS | not-in-scope | not-in-scope | PASS | PASS | PASS | PASS | Done |
| F0004-S0004 | PASS | not-in-scope | PASS | PASS | PASS | PASS | PASS | Done |

## Backend Progress

- [x] Versioned content/date contracts and durable integration implemented.
- [x] Publication, authorized consumer reads and history verified.
- [x] Compatibility, restart, failure and restore cases pass.

## Frontend Progress

N/A — no new screen or control. Existing evidence consumers must stay compatible.

## Required Role Matrix

Required Signoff Roles (set in planning):

| Role | Required | Why Required | Set By |
|---|---|---|---|
| Quality Engineer | Yes | Framework minimum; acceptance and negative cases | Product Manager — baseline |
| Code Reviewer | Yes | Framework minimum; contract/integration review | Product Manager — baseline |
| Security Reviewer | Yes | Current authorization, origin/date authority and owner constraints | Architect — Phase B |
| DevOps | Yes | Additive migration, restart and isolated restore proof | Architect — Phase B |
| Architect | Yes | Versioned contract and ADR reconciliation | Architect — Phase B |

All five roles apply to all four stories. G2 implementation acceptance passed; G3 review reports pass with recommendations; G3 validation passed. G5 signoffs are recorded below after explicit G4 approval; ordered G5 validation passed.

## Story Signoff Provenance

Append-only history. All five required roles have a passing G5 row per story;
independent review report dates and scoped recommendations are preserved.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0004-S0001 | Quality Engineer | Codex (Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/test-execution-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0001 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0001 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0001 | DevOps | Codex (DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/deployability-check.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0001 | Architect | Codex (Architect role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/architect-review.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0002 | Quality Engineer | Codex (Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/test-execution-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0002 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0002 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0002 | DevOps | Codex (DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/deployability-check.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0002 | Architect | Codex (Architect role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/architect-review.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0003 | Quality Engineer | Codex (Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/test-execution-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0003 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0003 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0003 | DevOps | Codex (DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/deployability-check.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0003 | Architect | Codex (Architect role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/architect-review.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0004 | Quality Engineer | Codex (Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/test-execution-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0004 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0004 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0004 | DevOps | Codex (DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/deployability-check.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0004 | Architect | Codex (Architect role) | PASS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/architect-review.md | 2026-10-21 | G5 recorded after G4 approval; scoped report and recommendations retained |
| F0004-S0001 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0001 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0002 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0002 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0003 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0003 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0004 | Code Reviewer | Codex (independent Code Reviewer subagent) | APPROVED WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/code-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |
| F0004-S0004 | Security Reviewer | Codex (independent Security Reviewer subagent) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/security-review-report.md | 2026-10-21 | G8 records full scoped report verdict; PM accepts bounded recommendations in pm-closeout.md |

## Phase Boundaries and Design Handoff

- Approved assembly plan, versioned schemas/API boundary, compatibility matrix, ADR reconciliation and KG source bindings are the implementation baseline.
- Preserve accepted PDF/BoxSelector behavior; do not imply full W3C/OOXML or new transcription/description engine delivery.
- Document date and text origin are bounded storage/contract carry-ins; broader ADR-0064/0065 behavior stays Proposed.
- F0005 production activation and F0026 release qualification remain separate.

## Tracker Sync Checklist

Story index and BLUEPRINT links include all four stories. REGISTRY/ROADMAP remain Planned/Next. Story and tracker validation passed; the earlier strict story pass retained one nonblocking dependency advisory. KG drift/reproducibility and template validation passed. Phase A and Phase B approvals are recorded in the plan run. All four stories passed; no orphaned story. G4 approval and twenty required G5 rows are recorded. G6/G7 passed; G8 publishes the archive and regenerated trackers.

## Closeout Summary

Completed 2026-10-21, feature run 2026-10-17-8a6cc79f; user explicitly approved
G4. All four stories and 25 ACs are delivered with all five required role
signoffs. Runtime: 229 engine, 93 neuron and four restore tests pass; four
optional live-inference/tokenizer skips. Changed runtime coverage 90.60%.
Independent review defects (PDF polyglot and date-read race) and repeated JSONL
scanning are corrected and verified. G7 binds as-built code and regenerates
symbols/decisions; G8 archives, synchronizes trackers and publishes evidence.

Deferred follow-ups: baseline security documents/strict planning audit (Security
and Architect, F0026, 2026-11-03); fixed Docling/hook qualification and exact OCR
asset provenance (AI Engineer and DevOps/Architect, F0005, before broader
activation); public API headers (Backend/DevOps, F0026, 2026-11-03); static Python
caller extraction limits (Architect/tooling, F0026). G7 bindings are complete;
the source caller ledger preserves the injected-call routing limits. Existing
PR hotspot/owner acknowledgement remains a merge obligation.

The v2 writer remains disabled pending deployment reconciliation and consumer
gates. Human/source verification defaults deny; no production date producer
or new UI/grant/endpoint/model engine. ADR-0073 and broader ADRs remain Proposed;
production Graph qualification is separate. No shared DB migration, production
deployment, commit, push or merge is claimed. Named PM recommendation acceptances
and exact evidence are in the run's pm-closeout.md.
