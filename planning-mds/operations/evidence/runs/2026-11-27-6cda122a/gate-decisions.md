# Gate Decisions — F0021 plan 2026-11-27-6cda122a

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Action plan, PHASE=A+B, FEATURE_MODE=new, contract 2026-07-11, severity profile none.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-11-27T15:34:49+00:00 | Four scope questions answered by the operator (D1–D4); nine stories / 55 testable ACs; remaining items are PM assumptions A1–A8 or explicit Phase B technical decisions | No | Operator reviews A1–A8 at G3 |
| G2 | PASS | Product Manager | 2026-11-27T15:34:49+00:00 | STORY-INDEX regenerated (82 stories); strict story validation (9/9, zero warnings) and validate-trackers --skip-feature-evidence (0 errors, 0 warnings) pass; dependency audit recorded in artifact-trace.md | No | Architect completes KG source bindings at G4 |

## G1 operator clarification decisions (2026-11-27)

The operator answered four questions in the current conversation, each with the recommended option.

| ID | Question | Decision |
|---|---|---|
| D1 | Session bounds | Server-enforced 30-minute idle and 8-hour absolute lifetime; idle warning 2 minutes before expiry; no silent renewal past the absolute limit |
| D2 | Shell scope | Sign-in/out, session status, Home with identity and memberships, active knowledge-base selector (narrows only; switching clears caches), route/flag/lazy-load seam, proof Review Panel rehosted behind the cookie session with token-in-URL removed; its decision submission is the §121.2 item 9 mutation |
| D3 | Re-auth UX | Popup re-authentication keeps in-memory work; blocked mutations shown as not submitted and re-confirmed explicitly; redirect fallback restores only the sanitized route |
| D4 | Rejected-credential throttling | 20 per client per 60 s with normal events, then 429 + Retry-After, no per-request row, one rate_limited event per client per window; bearer API and BFF cookie path |

## Requirements reconciliation

1. BLUEPRINT §2.1 still calls the BFF session transport "proposed direction (ADR-0051, open)"; the ADR-0051 decision was recorded 2026-11-08 and stays Proposed until S0009 proves §121.2 items 8 and 9. No requirement conflict; Phase B refreshes the §2.1 wording.
2. The F0001-S0004 proof Review Panel belongs to F0022 for functional change. D2 moves only its entry point and transport; F0022 still owns renderers, batching and reviewer authority (S0007 Out of Scope).
3. ADR-0051 D6 says "tenant switch". F0002 memberships are per tenant and knowledge base, and authorization is resource-based, so the shell's switch is the active knowledge-base selector (S0006 AC4/AC5), which covers a tenant change.
4. The authentik dev client `brain` is `public`. A BFF needs a confidential client; registering it is a Phase B design item, not a requirement change.

## Dependency audit

See artifact-trace.md: F0002 (direct) and F0011 (impacted) approved manifests read; F0001-S0004/S0006 reused as archived; downstream consumers (F0022, F0023, F0067, F0026) are audit pending. No repo-wide feature-evidence validation.

## Pending checkpoint (superseded by the approval below)

G3 requires the operator's explicit approval of the PRD, personas, nine stories / 55 ACs, decisions D1–D4 and assumptions A1–A8. Suggested token: `approve-phase-a`. After the response: record the exact token/actor/time here, make Phase A approval-status edits, attest `approve-phase-a` as product-manager, and rerun G3. Do not attest before the response.

## G3 explicit Phase A approval

- Stage: G3
- Checkpoint: approve-phase-a
- Approval token: operator reply "approve and proceed to next" (exact text), given in response to the `approve-phase-a` request; recorded as checkpoint `approve-phase-a`
- Actor: user (operator)
- Recorded at: 2026-11-28T02:49:40+00:00
- Scope: F0021 Phase A requirements — PRD, personas (incl. new Noor), nine stories / 55 ACs, G1 decisions D1–D4 and PM assumptions A1–A8 as written. Run 2026-11-27-6cda122a.
- Decision: APPROVED. Phase A approval-status edits (PRD, STATUS, README, BLUEPRINT §3.3) were made before attestation. Architecture proceeds in this A+B run; the manifest stays draft until G5 publication.
- Attestation note: the first `approve-phase-a` attestation omitted `--actor`, so approve-plan rejected it as incomplete. It was re-attested with actor `operator` after this note was added; the approval itself is unchanged.

## Architecture gates and reconciliation

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G3 | PASS | Operator / Product Manager | 2026-11-28T03:01:36+00:00 | Operator approval recorded and attested as approve-phase-a (re-attested with actor operator); approve-plan Phase A operation passed in the A+B run | No | Manifest stays draft until G5 |
| G4 | PASS | Architect | 2026-11-28T03:01:36+00:00 | kg-source shards compiled (F0021 shard: coverage_excluded removed, affects/governed_by adr:0082/uses_schema/nine story mappings; adr:0082; three schemas; capabilities browser-session-bff, credential-rejection-throttle, shell-route-seam; entities browser-session, session-event); validate --check-drift passed on the first attempt through run-gate.py | No | G5 exit validation and explicit Phase B review |

Phase B outputs: ADR-0082 (Proposed, refines ADR-0051), feature-assembly-plan.md, GETTING-STARTED.md, bff-api-design.yaml, migration-design.sql (0018), contract-inventory.yaml, three design schemas (browser-session-v1, active-knowledge-base-update-v1, logout-result-v1), data-model.md F0021 section, BLUEPRINT §2.1 refresh and §4.20.

Phase B reconciliation (details in the assembly plan, R1–R7):

1. R1 — S0002 AC4 names 403 for an authorization denial; every engine denial is the non-disclosing 404 (brain-api.yaml, blueprint §118.2). Design keeps 404 (session kept); 403 only for csrf_rejected. Proposed PM wording fix at feature G0; operator confirmation requested.
2. R2 — S0008 AC2 "no credential verification runs" conflicts with AC4 (valid credentials from a throttled client are served). Design: local verification continues; a throttled rejection writes no event and makes no IdP call. Proposed PM wording fix at feature G0; operator confirmation requested.
3. R3 — authentik 2026.2 end-session / rotation behaviour verified at feature G0 before S0005; prompt=login fallback.
4. R4 — tenant and knowledge_base gain nullable display_name (migration 0018).
5. R5 — one public origin, engine under a stripped /api mount; contract paths stay at the root (SOLUTION-PATTERNS §3).
6. R6 — tenant switch = active knowledge-base selector.
7. R7 — BLUEPRINT §2.1 session-transport and frontend-testing wording refreshed.

G5 exit validation (validate-stories, generate-story-index, validate-trackers --skip-feature-evidence, kg-write-coverage, kg-check-drift-exit, kg-check-reproducible, validate-templates) passed through run-gate.py.

## Pending checkpoint (Phase B) (superseded by the approval below)

G5 requires the operator's explicit approval of the Phase B architecture (ADR-0082, assembly plan, design files, KG bindings) and confirmation of reconciliations R1 and R2. Suggested token: `approve-phase-b`. After the response: record the exact token/actor/time here, make approval-status edits (STATUS/README/PRD/assembly plan/ADR/kg-source shard/BLUEPRINT), attest `approve-phase-b` as architect with actor operator, and rerun G5. Do not attest before the response.

## G5 explicit Phase B approval

- Stage: G5
- Checkpoint: approve-phase-b
- Approval token: `approve-phase-b` (exact operator reply)
- Actor: user (operator)
- Recorded at: 2026-11-28T03:37:29+00:00
- Scope: F0021 Phase B architecture — ADR-0082 (Proposed), feature-assembly-plan.md, GETTING-STARTED.md, bff-api-design.yaml, migration-design.sql, contract-inventory.yaml, three design schemas, data-model.md, BLUEPRINT §2.1/§4.20 and KG bindings. Per the approval request, the token also confirms reconciliations R1 (engine denials stay the non-disclosing 404; S0002 AC4 wording fixed by the PM at feature G0) and R2 (local verification continues while throttled; S0008 AC2 wording fixed by the PM at feature G0). Run 2026-11-27-6cda122a.
- Decision: APPROVED. Approval-status edits (STATUS, README, PRD, assembly plan, ADR-0082, kg-source shard, BLUEPRINT §3.3/§4.20) were made before attestation. ADR-0051 and ADR-0082 remain Proposed until F0021-S0009 passes.
