# Gate Decisions — F0004-content-artifact-model plan run 2026-10-17-620b7618

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G1 | PASS | Product Manager | 2026-10-17T11:35:35-04:00 | The operator directed the six review fixes ("go ahead and apply the fixes"), which accepts the medium-gap recommendation (fallback keeps ADR-0073 source/version identity). Dispositions are in action-context.md. No other business question is open. | No | - |
| G2 | PASS | Product Manager | 2026-10-17T11:35:35-04:00 | Phase A changes only the PRD and checklist status lines. No story or AC text changed; validate-stories passes. | No | - |
| G3 | PASS | Product Manager | 2026-10-17T11:38:46-04:00 | Phase A checkpoint token: **`approve-phase-a`**, typed verbatim by the operator after reviewing the rework summary. | No | - |
| G4 | PASS | Architect | 2026-10-17T11:40:11-04:00 | Phase B fixes all six gaps. The sweep, backfill, repair and worker denial now use synchronous in-transaction authorization (`decide` over `SyncAuthorityStore`, decision and effects in one commit). Fallback keeps the ADR-0073 version ID (v1 bundle, namespace and artifact derivation only). Insert order follows the foreign keys. The orphan key is CONTENT_ARTIFACT with require_record=False. RESTORE_DRILL and RESTORE_MISMATCH are removed. Header and status lines are refreshed. ADR-0073 §1/§2/§3 and the proof gates, the SQL comments and enums, GETTING-STARTED, STATUS and the KG shard are updated. SQL parses (27 statements, 3 plpgsql bodies); KG and plan-readiness exit 0. | No | - |
| G5 | PASS | Architect | 2026-10-17T11:41:08-04:00 | All exit commands exit 0. validate-trackers first failed on the known generate-story-index.py hard-break backslash defect; the committed STORY-INDEX.md was restored (story metadata unchanged) and the stage resumed from validate-trackers. Phase B checkpoint token: **`approve-phase-b`**, typed verbatim by the operator. | No | Framework: generate-story-index backslash defect; manifest placeholder drift |

## Planning approval supersession reconciliation

2026-10-18T00:52:01.871081+00:00 — Codex (Product Manager role), authorized by the operator in the current session. Kept this run approved and marked the three earlier approved F0004 planning manifests superseded. Historical approval decisions remain valid. See [planning-approval-reconciliation.md](planning-approval-reconciliation.md).
