# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0021
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0021-native-react-semantic-shell-and-oidc-session
- **feature_slug:** native-react-semantic-shell-and-oidc-session
- **mode:** clean
- **phase:** A+B
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-28-831962b8
- **run_id:** 2026-11-28-831962b8

## Inputs

- FEATURE_ID=F0021, PHASE=A+B, FEATURE_MODE=existing (targeted planning rework).
- Trigger: plan review `2026-11-27-d1148686` (CONDITIONALLY READY: 0 Critical, 5 High, 1 Medium) of approved plan run `2026-11-27-6cda122a`.
- Operator choices (2026-11-28): rework, including PM-01; Chromium + Firefox proof; read-only throttle once over the limit; confirm the IdP end-session on return.

## Assumptions

- The approved plan from run 2026-11-27-6cda122a is the baseline; only what the findings require changes. D1–D4 and A1–A8 are unchanged.

## Scope Boundaries

- Phase A: PM-01 status/error layouts; S0005 AC7 end-session outcomes; S0008 AC2/NFR wording (read-only throttle, clock-aligned window); S0009 per-browser evidence; R1/R2 wording fixes already confirmed by the operator on 2026-11-27.
- Phase B: ARCH-01 recoverable CSRF secret; ARCH-02 terminal-state mapping; ARCH-03 end-session lifecycle; BUILD-01 Firefox harness; BUILD-02 read-only throttle path.
- No source code, no feature evidence package, no compiled KG file hand edits.

## Lifecycle Stage

- plan run initialized
