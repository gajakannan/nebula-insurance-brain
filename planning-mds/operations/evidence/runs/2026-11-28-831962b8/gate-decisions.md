# Gate Decisions — F0021 plan 2026-11-28-831962b8

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Action plan, PHASE=A+B, FEATURE_MODE=existing (rework), contract 2026-07-11, severity profile none. Reworks approved plan run `2026-11-27-6cda122a` to resolve plan review `2026-11-27-d1148686`.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-11-28T15:19:33+00:00 | Four rework questions answered by the operator (approach, browsers, throttle, end-session); no other open requirement question | No | Operator reviews the Phase A delta at G3 |
| G2 | PASS | Product Manager | 2026-11-28T15:19:33+00:00 | STORY-INDEX regenerated (82 stories); strict story validation 9/9 zero issues; validate-trackers --skip-feature-evidence 0 errors / 0 warnings | No | Architect updates design and KG at G4 |

## G1 operator rework decisions (2026-11-28)

| ID | Finding | Decision |
|---|---|---|
| RW1 | Approach | Rework through a new A+B plan run, including PM-01 (not risk acceptance) |
| RW2 | BUILD-01 | Keep the requirement: the S0009 proof runs in Chromium and Firefox, both must pass, per-browser evidence |
| RW3 | BUILD-02 | Keep the no-write NFR: read the counter first; upsert only below the limit; throttled requests after the window's `rate_limited` event write nothing |
| RW4 | ARCH-03 | Confirm on return: authentik returns to the signed-out page; outcomes `completed` / `failed` / `unconfirmed` (2-minute bound), durable record and warning |

ARCH-01 (recoverable CSRF secret) and ARCH-02 (expired-session mapping) are architect design fixes with no operator decision.

## Phase A delta

1. PRD: two screen rows (Route load error, Sign-in unavailable); signed-out layout shows revocation and end-session outcomes; one shared status/error content block with desktop and narrow layouts and a per-page content table (PM-01).
2. S0005 AC7, Interaction Contract and Data Requirements: observed end-session outcome `completed` / `failed` / `unconfirmed` (RW4).
3. S0008 AC2: R1-style wording fix R2 (local check only, no IdP call). NFR: read-only after the window's event, bounded counter overshoot, clock-aligned window that divides an hour (RW3).
4. S0002 AC4: wording fix R1 (denial → existing non-disclosing 404; 403 only for CSRF/origin refusal).
5. S0009 NFR and checklist rows: per-browser versions and results; both browsers must pass (RW2).
6. acceptance-criteria-checklist.md: S0005 AC7, S0008 AC2 and S0009 AC1–AC5 proof wording. AC count unchanged (55).

R1 and R2 were confirmed by the operator with `approve-phase-b` on 2026-11-27 as wording fixes deferred to feature G0; this run applies them now.

## G3 explicit Phase A approval

- Stage: G3
- Checkpoint: approve-phase-a
- Approval token: operator reply "approve-phase-a" (exact text)
- Actor: user (operator)
- Recorded at: 2026-11-28T15:20:25+00:00
- Scope: the Phase A delta above (PRD layouts and screens, S0002 AC4, S0005 AC7/contract/data, S0008 AC2/NFR, S0009 NFR, checklist rows). D1–D4 and A1–A8 unchanged. Run 2026-11-28-831962b8.
- Decision: APPROVED. Approval-status edits (STATUS, README, PRD, BLUEPRINT §3.3) made before attestation. Architecture proceeds in this A+B run; the manifest stays draft until G5 publication.

## Architecture gates and reconciliation

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G4 | PASS | Architect | 2026-11-28T15:25:58+00:00 | kg-source shards updated (F0021 feature notes; browser-session-bff, credential-rejection-throttle, browser-session, session-event notes); compile.py and validate.py --check-drift exit 0 | No | — |
| G5 (exit validation) | PASS | Architect | 2026-11-28T15:25:58+00:00 | validate-stories, generate-story-index, validate-trackers --skip-feature-evidence, kg-write-coverage, kg-check-drift, kg-check-reproducible, validate-templates all exit 0 | No | Operator approval approve-phase-b |

### Plan-review findings resolved

| Finding | Severity | Resolution (Phase B) |
|---|---|---|
| ARCH-01 | High | CSRF secret stored AES-256-GCM encrypted (`browser_session.csrf_ciphertext`, same key ID as tokens) beside its digest; GET /session returns the same token per session from any worker/tab/reload (ADR-0082 D3, D5) |
| ARCH-02 | High | Stored end reason decides the 401: idle/absolute/renewal-failed → `session_expired` for as long as the row exists; others → `unauthenticated`; renewal waiters re-read the reason; lock timeout → 503 (D5 step 3, D6) |
| ARCH-03 | High | End-session lifecycle pending → completed / failed / unconfirmed via BFF route `GET /auth/end-session/return` (2-minute rule, single use) plus a sweep; new `session_event` types; `logout-result-v1` end_session = pending+url or failed/no_endpoint (D7) |
| BUILD-01 | High | S0009 Playwright projects `chromium` and `firefox`, both required in CI, per-browser versions/results (D4, Step 8) |
| BUILD-02 | High | Read-first throttle: no write above the limit; upsert only at or below; configurable clock-aligned window dividing 3600 (D9, migration design) |
| PM-01 | Medium | Resolved in Phase A (PRD status/error layouts) |

Design checks: artifacts/phase-b-design-checks.log (migration design applied to a scratch PostgreSQL database with positive and negative constraint cases; logout-result-v1 schema examples; YAML parse; contract hashes recomputed).

## G5 explicit Phase B approval

- Stage: G5
- Checkpoint: approve-phase-b
- Approval token: operator reply "approve-phase-b" (exact text)
- Actor: user (operator)
- Recorded at: 2026-11-28T15:28:38+00:00
- Scope: the Phase B rework above (ADR-0082 D3/D4/D5/D6/D7/D9/D12, assembly plan, migration design, API fragment, logout-result-v1 and browser-session-v1, contract inventory, data model, KG sources), including the two architect calls presented with it: ended-session logout needs the origin checks but not the CSRF token; feature G0 confirms Firefox `__Host-` cookies on http://localhost, with the HTTPS profile as the fallback for both browsers.
- Decision: APPROVED. Approval-status edits (STATUS, README, PRD, assembly plan, ADR-0082, BLUEPRINT §3.3, kg-source/features/F0021.yaml) made before attestation. approve-plan.py publishes this run and supersedes planning run 2026-11-27-6cda122a.
