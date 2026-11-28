# F0021 — Getting Started

Implementation guide for the feature run. Phase A and Phase B are approved (2026-11-27); the feature run has not started.

## Planning resume

Canonical `NEBULA_PRODUCT_ROOT`: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
The plan run is `2026-11-27-6cda122a` (action plan, phase A+B, feature mode new). Keep this run ID across sessions.

From `/home/gajap/uSandbox/repos/nebula/nebula-agents`:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-27-6cda122a
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

Read these before starting:

- the [PRD](PRD.md), [STATUS](STATUS.md) and the nine stories;
- the [assembly plan](feature-assembly-plan.md) and its R1–R7 reconciliation;
- proposed [ADR-0082](../../architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md) and [ADR-0051](../../architecture/decisions/ADR-0051-browser-session-and-revocation-contract.md);
- the [BFF API design](bff-api-design.yaml), [migration design](migration-design.sql) and [contract inventory](contract-inventory.yaml);
- the run's [gate decisions](../../operations/evidence/runs/2026-11-27-6cda122a/gate-decisions.md);
- the plan review [report](../../operations/evidence/runs/2026-11-27-d1148686/plan-review-report.md) and the rework run's [gate decisions](../../operations/evidence/runs/2026-11-28-831962b8/gate-decisions.md) (assembly plan section Plan Review Rework).

## Carry-ins and gotchas

- **Contract paths:** paths stay at the root (no `/api` prefix in the contract; SOLUTION-PATTERNS section 3). `/api` is a public mount stripped by the Vite proxy locally and by the F0026 ingress in production.
- **Denial responses (R1):** engine denials stay the non-disclosing 404. Only `csrf_rejected` uses 403.
- **Throttled verification (R2):** while a client is throttled, verification still runs locally; a throttled rejection writes no event and makes no IdP call.
- **Throttle is read-first (BUILD-02):** read the window row before any upsert; above the limit, write nothing. Prove it with `xmin` and `pg_stat_user_tables`, not only event counts.
- **CSRF token is stored encrypted (ARCH-01):** never generate a new token per `GET /session`; decrypt the stored one.
- **End reason decides the 401 (ARCH-02):** timeout and renewal-failure endings return `session_expired` even after another request ended the session.
- **End-session return route (ARCH-03):** `post_logout_redirect_uri` is `/api/auth/end-session/return`, not `/signed-out`. Register it in the blueprint for both origins.
- **Two browsers (BUILD-01):** S0009 runs in the `chromium` and `firefox` Playwright projects; both must pass.
- **authentik G0 check (R3):** before building S0005, verify the 2026.2 field names for post-logout redirect URIs and refresh-token rotation, that `default-invalidation-flow` ends the authentik session, that authentik returns `state` to `post_logout_redirect_uri`, and what it does on an end-session error.
- **Confidential client:** making `brain` confidential breaks any ROPC helper that omits the client secret. Update `scripts/dev/seed_principals.py` and the engine token fixtures in the same change, and run the bearer regression suite before anything else.
- **Append-only trigger:** reuse `brain_append_only()` from migration 0007 for `session_event`; do not create a second function.
- **Composite FKs:** declare the `knowledge_base(id, tenant_id)` composite FK targets in the ORM models (F0009 lesson).
- **New files and the KG:** KG wildcard bindings resolve only git-tracked files. Bind new engine and `experience/` files with literal paths until they are committed, `git add` new planning files, then rerun `validate.py --write-coverage-report`.
- **GPU:** never run GPU-using tests during live lanes. None are expected here: there is no parse or model call.

## Local stack (planned)

1. `docker compose up -d postgres authentik-server authentik-worker`. The dev blueprint provisions the confidential `brain` client.
2. Start the engine with:
   - `BRAIN_PUBLIC_ORIGIN=http://localhost:5173`
   - `BRAIN_OIDC_CLIENT_SECRET=<dev value from the blueprint>`
   - `BRAIN_SESSION_KEYS=dev1:<base64 32 bytes>`
   - `BRAIN_TRUSTED_PROXIES=127.0.0.1/32`
3. `pnpm --dir experience dev`, then open `http://localhost:5173/`. Sign in as `alice.tenant-a` or `bob.tenant-b` with the dev password.
4. Real-browser proof: `docker compose -f docker-compose.yml -f docker-compose.e2e.yml up -d`, then `pnpm --dir experience e2e`.
