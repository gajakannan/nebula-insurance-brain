# Feature Assembly Plan — F0021: Native React semantic shell + OIDC/session contract and safe re-auth behavior

**Created:** 2026-11-27
**Author:** Claude / Architect
**Status:** Phase B approved 2026-11-27 by operator token `approve-phase-b` (confirms R1 and R2); plan-review rework approved 2026-11-28 by operator token `approve-phase-b` (run 2026-11-28-831962b8)
**Plan Run:** 2026-11-27-6cda122a (A+B, new); plan-review rework run 2026-11-28-831962b8 (A+B, existing)
**Requirements:** Phase A approved on 2026-11-27 (operator reply recorded as `approve-phase-a`); nine stories, 55 ACs; G1 decisions D1–D4; PM assumptions A1–A8.
**Governing design:** [ADR-0082](../../architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md) (Proposed), refining [ADR-0051](../../architecture/decisions/ADR-0051-browser-session-and-revocation-contract.md) (Proposed; decision recorded 2026-11-08). Uses [ADR-0049](../../architecture/decisions/ADR-0049-shared-identity-and-verified-principal-boundary.md) for verification and principal resolution, and [ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) for the route seam.

## Overview

Add a backend-for-frontend (BFF) to the engine API process. It handles sign-in, the session cookie, CSRF and origin checks, coalesced renewal, logout with upstream revocation, a session endpoint, and a rejected-credential throttle.

The work has five parts:

- **Persistence:** migration 0018 adds four tables and two display-name columns.
- **Identity provider:** the authentik `brain` client becomes confidential.
- **Shell:** `experience/` becomes a React Router shell. It has a route, flag and lazy-loading registry; in-memory session state; one API client; hygiene triggers; and a popup re-authentication flow with explicit re-confirmation.
- **Review Panel:** moves behind the cookie session.
- **Real-browser suite:** proves master blueprint section 121.2 items 8 and 9.

The existing bearer path, route handlers, authorization and the non-disclosing 404 are unchanged.

Design inputs in this folder:

- [bff-api-design.yaml](bff-api-design.yaml): OpenAPI fragment, merged into `brain-api.yaml` by the feature run.
- [migration-design.sql](migration-design.sql)
- [contract-inventory.yaml](contract-inventory.yaml)
- Three design schemas under `planning-mds/schemas/`: `browser-session-v1`, `active-knowledge-base-update-v1` and `logout-result-v1`.

## Plan Review Rework (run 2026-11-28-831962b8)

Plan review `2026-11-27-d1148686` was CONDITIONALLY READY with five High findings and one Medium. The operator chose rework (not risk acceptance) and answered the three requirement questions; Phase A rework was approved with `approve-phase-a` on 2026-11-28.

| Finding | Resolution | Where |
|---|---|---|
| ARCH-01 CSRF token not recoverable from a digest | The CSRF secret is stored encrypted under the session key ring (same key ID as the tokens; re-encrypted on each token write) beside its digest. Every `GET /session` for one live session returns the same token from any worker, tab or reload; a new session gets a new token. | ADR-0082 D3, D5; `browser_session.csrf_ciphertext`; Step 1, Step 6; proof S0006 AC1, S0002 AC2 |
| ARCH-02 ended timeout session lost `session_expired` | The response follows the stored end reason: `idle_timeout`, `absolute_timeout`, `renewal_failed` → `401 session_expired` for as long as the row exists; logout, replacement, principal endings and unknown digests → `401 unauthenticated`. Renewal waiters re-read the end reason; a lock timeout is `503`. | ADR-0082 D5 step 3, D6; Step 5; proof S0002 AC4, S0003 AC2, S0004 AC1 |
| ARCH-03 end-session outcome not observable | authentik returns to the BFF route `GET /auth/end-session/return`, which sets `completed` (within 2 min), `failed` (`error` parameter or no endpoint) or `unconfirmed` (late) once and appends a `session_event`; a sweep marks never-returned logouts `unconfirmed` after 2 minutes. The signed-out page confirms only on `completed`. | ADR-0082 D7; migration columns `end_session_*`; `logout-result-v1`; bff-api-design.yaml; Step 6, Step 7, Step 8; proof S0005 AC7, S0009 AC3 |
| BUILD-01 Chromium-only proof | S0009 runs as two Playwright projects, `chromium` and `firefox`, against one stack; both must pass in CI; per-browser versions and results recorded. | ADR-0082 D4; Step 8; S0009 rows |
| BUILD-02 throttle writes while throttled | Read first; upsert only while the count is at or below the limit; throttled requests after the window's `rate_limited` event write nothing. Limit and window are settings; the window divides one hour and is clock-aligned. | ADR-0082 D9; migration-design.sql; Step 4; proof S0008 AC2/AC3 |
| PM-01 status/error layouts | PRD now has one shared status/error block (desktop and narrow) with a per-page table; `SignInUnavailable` page added. | PRD; New Files; Step 7 |

R1 and R2 wording fixes were applied to S0002 AC4 and S0008 AC2 in the same rework (no longer deferred to feature G0).

## Phase B Reconciliation (for operator review at G5)

| # | Item | Resolution |
|---|---|---|
| R1 | **S0002 AC4 says "an authorization denial → `403`".** No engine route returns 403 for a denial. Every denial is the non-disclosing 404 (`brain-api.yaml` `Forbidden`: "user denials are reported as 404"; master blueprint section 118.2). | The design keeps the engine unchanged. 403 is used only for `csrf_rejected`, and a denial stays the existing 404 with the session kept (never 401). The AC4 proof shows each outcome is distinct and the session survives a denial. **Proposed PM wording correction at feature G0:** "an authorization denial → the engine's existing non-disclosing `404`, with the session kept". Confirmed by the operator with `approve-phase-b` (2026-11-27). |
| R2 | **S0008 AC2 says "no credential verification runs"**, but AC4 requires a valid credential from a throttled client to be served, which needs verification. | Verification stays local while throttled: cached JWKS, session lookup, no JWKS refetch, no IdP call. A rejected credential then gets 429 with no event row. AC2 is proven as "no per-request `authentication_event`, no upstream IdP call". **Proposed PM wording correction at feature G0.** Confirmed by the operator with `approve-phase-b` (2026-11-27). |
| R3 | S0005 AC7 depends on authentik's end-session behavior. | The provider's invalidation flow becomes `default-invalidation-flow` (ADR-0082 D2). The end-session URL carries `client_id`, `post_logout_redirect_uri` (the BFF return route) and `state`, with no `id_token_hint`. The signed-out page's "Sign in" sends `prompt=login`. Feature G0 verifies against authentik 2026.2, before S0005 is built, that it ends the session, returns to `post_logout_redirect_uri` with `state`, and what it does on error (the 2-minute `unconfirmed` bound covers an IdP that never returns). |
| R4 | S0006 AC1 needs tenant and knowledge-base display names; `tenant` and `knowledge_base` have no name column. | Migration 0018 adds nullable `display_name` (expand-only). Null names show a localized "Unnamed knowledge base" with a short ID suffix. Dev seed data sets names. |
| R5 | `/reviews/{id}` is both an engine path and the natural shell route. | One public origin: the shell at `/`, the engine under `/api/`, with the prefix stripped by the front. The OpenAPI paths stay at the root (SOLUTION-PATTERNS section 3: no `/api` prefix in the contract). The shell route is `/reviews/:reviewItemId`. |
| R6 | ADR-0051 says "tenant switch". | Implemented as the active knowledge-base selector (Phase A reconciliation 3). A change of tenant is a change of selected membership. |
| R7 | BLUEPRINT section 2.1 still calls the session transport "proposed direction (ADR-0051, open)" and leaves the frontend test stack to Phase B. | Updated in this run: ADR-0051 decision recorded, ADR-0082 runtime, stack confirmed (ADR-0082 D12). |

## Build Order

| Step | Scope | Stories | Depends on |
|---|---|---|---|
| 1 | Settings, key ring, migration 0018, stores, new reason codes | S0001–S0003, S0005, S0006, S0008 (persistence) | F0002 |
| 2 | authentik confidential client and dev tooling | S0001, S0009 harness | — |
| 3 | OIDC client, sign-in and callback, cookies, return routes | S0001 | Steps 1–2 |
| 4 | Cookie request path, CSRF, ambiguity, throttle | S0002, S0008 | Step 3 |
| 5 | Renewal and lifetime limits | S0003 | Step 4 |
| 6 | Logout, revocation, end-session; session endpoint and active knowledge base | S0005 (server), S0006 (server) | Steps 4–5 |
| 7 | Shell: stack, route registry, API client, hygiene, Home, header, re-authentication, sign-out, Review Panel rehost | S0003 AC6, S0004, S0005 AC5/AC6, S0006, S0007 | Step 6 |
| 8 | Real-browser proof and IdP recorder harness | S0009 | Steps 1–7 |

## Existing Code (Must Be Modified)

| Path | Change |
|---|---|
| `engine/apps/api/src/brain_api/config.py` | Add `public_origin`, `public_api_prefix`, `oidc_client_secret`, `oidc_backchannel_url`, `session_keys`, `trusted_proxies`, `throttle_limit`, `throttle_window_seconds` (must divide 3600), `experience_flags_path`, `experience_routes_path`; the BFF is enabled only when the secret and key ring are present |
| `engine/apps/api/src/brain_api/deps.py` | `current_principal` becomes the ADR-0082 D5 pipeline: ambiguity check, bearer path unchanged, cookie path; the throttle wraps `_reject`; compose the session store and OIDC client |
| `engine/apps/api/src/brain_api/app.py` | Mount `auth` and `session` routers when the BFF is enabled; add a `Cache-Control: no-store` / `Vary: Cookie` middleware for cookie requests |
| `engine/apps/api/src/brain_api/errors.py` | `SessionExpiredError` (401 `session_expired`), `CsrfRejectedError` (403), `AmbiguousCredentialsError` (400), `RateLimitedError` (429 with `Retry-After`), `KnowledgeBaseNotAvailableError` (422), `IdpUnavailableError` (503) |
| `engine/packages/brain-domain/src/brain_domain/authx.py` | Twelve new `AuthenticationReason` values (ADR-0082 D5) |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | ORM models for the four tables; `display_name` on `Tenant` and `KnowledgeBase`; composite FK targets declared (F0009 lesson) |
| `engine/packages/brain-persistence/src/brain_persistence/identity.py` | Authentication-event sink accepts a payload (session reference, CSRF cause, client key for `rate_limited`) |
| `config/authx-identity-profile.yaml` | Unchanged (issuer, audience and `human_clients: [brain]` stay); comment notes that the client is confidential |
| `docker/authentik/blueprints/nebula-brain-dev.yaml` | `brain` provider: `client_type: confidential`, dev-only `client_secret`, redirect URIs `http://localhost:5173/api/auth/callback` and `http://localhost:4173/api/auth/callback` (stale `:8100` removed), `invalidation_flow: default-invalidation-flow`, `post_logout_redirect_uris` (or authentik's equivalent field) for `/api/auth/end-session/return` on both origins |
| `scripts/dev/seed_principals.py` and engine test token fixtures | Send the dev client secret on ROPC token requests; seed tenant and knowledge-base display names |
| `experience/vite.config.ts` | Replace the `/reviews` and `/health` proxies with one `/api` proxy (prefix rewrite, `xfwd: true`); same proxy for `vite preview` on 4173; manual chunks for `pdfjs-dist`/`fflate` |
| `experience/package.json` | Add `react-router` 7, `@tanstack/react-query` 5, `zustand` 5, `tailwindcss` 4 with `@tailwindcss/vite`, shadcn/ui primitives (`@radix-ui/*`, `class-variance-authority`, `clsx`, `tailwind-merge`), `i18next` with `react-i18next`, `@playwright/test`, `@axe-core/playwright`; scripts `e2e`, `budget`; description updated |
| `experience/src/App.tsx`, `main.tsx` | Proof launch form and `?token=` entry removed; `main.tsx` mounts the router, the QueryClient, i18n and the session bootstrap |
| `experience/src/review-panel/**` | Moved to `src/features/review-panel/`; `api.ts` uses the shared `apiClient` (no token parameter); existing component tests kept |
| `engine/tests/**` bearer regression | Unchanged and must pass (S0002 AC6) |

## New Files

- **Engine (`brain_security.bff`):** `engine/packages/brain-security/src/brain_security/bff/`
  - `oidc_client.py`: discovery cache, authorize URL, code exchange, refresh, revoke and end-session URL, all over the backchannel base URL with bounded timeouts.
  - `pkce.py`, `cookies.py`, `csrf.py`, `return_routes.py`, `token_crypto.py` (AES-256-GCM key ring), `client_key.py` (trusted-proxy resolution).
  - Tests for each module.
- **Engine persistence and API:**
  - `engine/packages/brain-persistence/src/brain_persistence/browser_sessions.py`: login attempts, sessions, row-lock renewal, session events.
  - `engine/packages/brain-persistence/src/brain_persistence/credential_throttle.py`
  - `engine/apps/api/src/brain_api/routes/auth.py`, `routes/session.py`; `engine/apps/api/src/brain_api/bff_pages.py` (popup-completion and failure HTML with a CSP nonce).
  - `engine/migrations/versions/0018_f0021_browser_sessions.py`
- **Engine tests:**
  - `engine/apps/api/tests/test_auth_login_callback.py`, `test_auth_logout.py`, `test_session_routes.py`, `test_cookie_request_path.py`, `test_credential_throttle.py`
  - `engine/tests/integration/test_browser_session_renewal.py`: concurrent workers on PostgreSQL.
- **Config:** `config/experience-flags.yaml` (`review-panel: true`), `config/experience-routes.yaml` (return-route allowlist).
- **Shell (`experience/src/shell/`):**
  - `router.tsx`, `routes/registry.ts`
  - `api/client.ts`, `api/hygiene.ts`
  - `session/sessionStore.ts`, `session/bootstrap.ts`, `session/signOut.ts`, `session/reauth.ts`, `session/blockedQueue.ts`, `session/crossTab.ts`, `session/idleWarning.tsx`
  - `pages/StatusPage.tsx` (the shared PRD status/error block), `pages/Home.tsx`, `pages/SignedOut.tsx`, `pages/SignInFailed.tsx`, `pages/SignInUnavailable.tsx`, `pages/TooManyAttempts.tsx`, `pages/NotFound.tsx`, `pages/RouteLoadError.tsx`
  - `layout/ShellFrame.tsx`, `layout/Header.tsx`, `layout/KnowledgeBaseSelector.tsx`
  - `dialogs/SessionExpiredDialog.tsx`, `dialogs/ReconfirmDialog.tsx`
  - `i18n/en-US.json`
  - Tests for each.
- **Shell styling and tooling:**
  - `experience/src/components/ui/**`: shadcn/ui primitives in use.
  - `experience/src/styles/tokens.css`: semantic theme tokens.
  - `experience/scripts/check-bundle-budget.mjs`
  - `experience/eslint.config.js`: storage-API and `Authorization` header bans.
- **Real-browser suite:**
  - `experience/e2e/**`: Playwright suite with `session-transport.spec.ts`, `mutation-continuity.spec.ts`, `principal-isolation.spec.ts`, `return-routes.spec.ts` and `a11y.spec.ts`.
  - `experience/e2e/harness/idp-recorder/`: test-only HTTP proxy between the BFF and authentik. It counts refresh grants and injects revocation failures and end-session failures (an error redirect, or no return).
  - `docker-compose.e2e.yml`

## Step 1 — Persistence and Settings

- Migration 0018 follows [migration-design.sql](migration-design.sql). `down_revision` is `0017_f0012_ontology_releases`.
  - The `session_event` append-only trigger reuses `brain_append_only()` from migration 0007.
  - The downgrade refuses when sessions or session events exist.
- `BrowserSessionStore` operations:
  - `start_attempt` and `consume_attempt` (single use);
  - `create_session`: ends the old session as `replaced` or `principal_changed`, in the same transaction;
  - `lookup(cookie_digest)`;
  - `touch`, at most once every 30 s;
  - `renew_locked`: separate transaction, `FOR UPDATE`, `lock_timeout` 15 s;
  - `end` and `record_event`;
  - `csrf_token(session)`: decrypts the stored CSRF secret; `verify_csrf` compares digests in constant time;
  - `begin_end_session`, `complete_end_session(state_digest, error)` (single use, 2-minute rule) and `sweep_unconfirmed(limit=100)` (`FOR UPDATE SKIP LOCKED`).
- Key ring parsing refuses an empty ring, duplicate key IDs and any key that is not 32 bytes.

## Step 2 — Identity Provider Client

- Blueprint changes are as listed above. Feature G0 records the authentik 2026.2 field names for post-logout redirect URIs and refresh-token rotation, and confirms that `default-invalidation-flow` ends the authentik session (R3).
- Dev tooling sends the client secret. The bearer regression suite must pass before Step 3 starts.

## Step 3 — Sign-in and Callback (S0001)

**`GET /auth/login`**

1. Validate `return_to` (ADR-0082 D11), `mode`, `reauth` and `prompt`.
2. Create the attempt with the PKCE verifier, state, nonce and binding.
3. Set `__Host-nebula_login` and redirect to authentik. Discovery failure → 503 `idp_unavailable`.

**`GET /auth/callback`** — each check fails closed to `/sign-in-failed`, or to the popup failure page.

1. Throttle check on failure (S0008 AC5).
2. IdP `error` → `idp_error`.
3. State missing, unknown, expired or used → `state_invalid`.
4. Binding cookie digest mismatch → `binding_mismatch`.
5. Code exchange: `client_secret_basic` with the verifier. Failure → `code_exchange_failed`.
6. ID token: signature, issuer, audience, expiry and `nonce` digest. Mismatch → `nonce_mismatch`.
7. Access token through the existing `OidcJwksVerifier`.
8. `PrincipalResolver`: a non-human client or a DISABLED principal is refused with its F0002 reason.
9. Create the session, set the session cookie and clear the login cookie.
10. Redirect to the sanitized route, or render the popup completion page.

Every failure writes exactly one `authentication_event` and sets no session cookie.

## Step 4 — Cookie Request Path, CSRF, Throttle (S0002, S0008)

- Implement the ADR-0082 D5 order in `current_principal`. CSRF and origin checks run in the dependency, before any route handler.
- The throttle (D9) wraps every rejection point: bearer, cookie and callback. It reads the window row first; at a count above the limit it returns 429 with `Retry-After` and writes nothing. Otherwise it upserts: returned ≤ 20 → normal 401 and event; = 21 → one `rate_limited` event and 429; > 21 (concurrent overshoot) → 429, no event.
- The cookie lookup maps the stored end reason to the response (ADR-0082 D5 step 3): timeout and renewal-failure endings → `session_expired`; all other endings and unknown digests → `unauthenticated`.
- Every response to a cookie request carries `Cache-Control: no-store` and `Vary: Cookie`. No CORS middleware is added.

## Step 5 — Renewal and Lifetime (S0003)

- Renewal margin is 60 s.
- The lock is a row lock, and the lock owner re-checks the expiry after acquiring it.
- One retry after 500 ms, for network errors and 5xx only. `invalid_grant` ends the session immediately.
- Idle limit 30 min and absolute limit 8 h, enforced at lookup. The absolute limit is never extended.
- `X-Nebula-Activity: background` does not touch the idle deadline.
- Disabled principal or principal mismatch ends the session and returns `401 unauthenticated`.
- A waiter that gets the lock after the session ended re-reads `end_reason` and applies the D5 mapping (`renewal_failed` → `session_expired`); `lock_timeout` → `503`, never `unauthenticated`.

## Step 6 — Logout and Session Endpoint (S0005, S0006 server)

**Logout (ADR-0082 D7)**

- Takes the same row lock as renewal.
- Revocation uses RFC 7009 with a 5 s timeout and no retry.
- The outcome is recorded in `session_event` `logout`, and the response follows `logout-result-v1`.
- An expired session gives `not_attempted` (`no_live_tokens`). Its logout needs the origin checks; `X-CSRF-Token` is checked when present but not required (ADR-0082 D7).
- End-session: store the `state` digest and `pending`; the response carries `end_session: {status: pending, url}` or `{status: failed, reason: no_endpoint}`.
- `GET /auth/end-session/return` applies the 2-minute rule once and redirects to `/signed-out?end_session=<outcome>`. Login, logout and `GET /session` sweep stale `pending` rows to `unconfirmed` first.
- A double submit: the second request finds the session ended and returns `not_attempted` (`session_already_ended`), so only one revocation is attempted.

**Session endpoint and active knowledge base (ADR-0082 D10)**

- `GET /session` and `PUT /session/active-knowledge-base`. `csrf_token` is the decrypted per-session secret, identical on every read of the same session.
- `grant_revision` is SHA-256 over the sorted current `(membership_id, grant_revision)` pairs; revoked and expired memberships are excluded.
- Flags are read from `config/experience-flags.yaml`, with an mtime cache.

## Step 7 — Shell (S0003 AC6, S0004, S0005 AC5/AC6, S0006, S0007)

**Stack and layout**

- Stack as ADR-0082 D12.
- Feature-slice folders (SOLUTION-PATTERNS section 5): `src/shell/` for the frame and session, `src/features/review-panel/` for the rehosted panel.

**Bootstrap**

1. `GET /api/session`.
2. On 401, `location.assign('/api/auth/login?return_to=' + current route)`.
3. On 200, validate the body with the generated AJV validator and store it in the Zustand session store, in memory.

**API client**

- One `apiClient` handles every request. It maps the D5 outcomes and never retries an unsafe method.
- `401 session_expired` (from any request, including the background poll, because the server maps by end reason):
  - unsafe request → push it to the blocked queue (label, method, route, body; memory only);
  - GET → mark it for one retry;
  - then open `SessionExpiredDialog`.
- `403 csrf_rejected`: refetch the session to refresh the CSRF token, then show an inline error. No retry.

**Re-authentication (ADR-0082 D8)**

- Popup with a `ref`. The completion signal is accepted from BroadcastChannel or `postMessage`, only from the shell's own origin and only with the pending `ref`.
- After the signal, `GET /session`:
  - same principal → retry blocked GETs once, then `ReconfirmDialog` with "Submit now" or "Cancel" for each blocked mutation;
  - different principal → discard the work, run hygiene, go to Home.
- A blocked popup, or one closed without completing, offers "Sign in on this page", with the lost-input warning.

**Hygiene and cross-tab**

- `hygiene.reset()`:
  - aborts every registered request;
  - calls `queryClient.clear()`;
  - resets resource stores;
  - is awaited before rendering the new state.
- Triggers: sign-out, principal change, active knowledge-base change, `grant_revision` change.
- Cross-tab: BroadcastChannel messages, plus a background session poll every 30 s while the page is visible and on focus.
- Sign-out: `signOut.ts` stores `{revocation, end_session: pending, started_at}` under `nebula.signout`, then navigates to the end-session URL. `SignedOut.tsx` shows the confirmation line only for `?end_session=completed` and the end-session warning for `failed`, `unconfirmed`, or a `pending` record older than 2 minutes found on any shell load.

**Idle warning**

- Shown from `idle_expires_at − idle_warning_seconds`, against server time.
- "Stay signed in" sends one user-initiated `GET /api/session` without the background header.

**Route registry and Review Panel**

- Registry entries are `{path, flagKey, lazy}`.
  - Flag off or unknown: not-found screen, no module request, not shown in navigation.
  - Module load failure: `RouteLoadError` with a retry.
- The Review Panel route is `/reviews/:reviewItemId`. Engine paths, behavior and receipts are unchanged.
- A `token` query parameter is removed with `history.replaceState` before anything else runs, and its value is never read or sent anywhere.

**Accessibility, language and budget**

- WCAG 2.2 AA with semantic theme tokens. All strings come from `en-US.json`.
- Budget script: the entry chunk's initial JavaScript must be at most 180 kB gzip, measured from the Vite manifest.

## Step 8 — Real-Browser Proof (S0009)

**Stack and run conditions**

- `docker-compose.e2e.yml` starts:
  - PostgreSQL and authentik from the dev blueprint;
  - the engine, with `BRAIN_OIDC_BACKCHANNEL_URL` pointing at `idp-recorder`;
  - the built shell under `vite preview` on 4173.
- Runs start from a clean volume. Results record the authentik and Playwright versions.
- **Browser matrix (BUILD-01):** `playwright.config.ts` defines two projects, `chromium` and `firefox`, over the same specs and fixtures (one stack, distinct synthetic sessions per project; projects run one after the other so recorder counts stay per project). The report records each browser's version and per-spec result. The CI job fails unless both projects pass. Firefox needs no special flag for `Secure` cookies on `http://localhost`; feature G0 confirms it, and if not, both projects use the HTTPS profile (ADR-0082 D4).

**Proofs**

- **Token absence (S0009 AC1):** inspect cookies, every storage API, every URL, and every response body and header.
- **Single refresh (AC2):** the recorder counts refresh grants per refresh-token family while 20 parallel requests run against an expired access token. The test-only `BRAIN_TEST_ACCESS_SKEW` setting is absent outside the e2e composition, and startup refuses it when `BRAIN_PUBLIC_ORIGIN` is not localhost.
- **Revocation failure (AC3):** the recorder injects a 503 or a drop on `/revoke`. A follow-up refresh grant with the revoked token is refused by authentik.
- **End-session outcomes (S0005 AC7):** success → `completed` and the next sign-in asks for credentials; recorder makes authentik's end-session redirect back with `error` → `failed`; recorder holds the browser (no return) → after 2 minutes (test clock) a `GET /session` sweep records `unconfirmed` and the next shell load shows the warning; discovery without an end-session endpoint → `failed` (`no_endpoint`).
- **Principal isolation (AC4):** alice and bob; a list of malicious return routes.
- **Mutation continuity (AC5):** a Review Panel decision is blocked by an expired session, is not received (the engine decision count is unchanged), and is sent only on "Submit now". A stale or revoked variant is refused without retry.

## Acceptance Criteria to Implementation / Proof Map

| Story / AC | Step | Proof |
|---|---|---|
| S0001 AC1 | 3 | Login redirect carries `code_challenge_method=S256`, state and nonce; attempt row holds digests and ciphertext only; no verifier or nonce in any response |
| S0001 AC2 | 3 | Callback success test: cookie attributes asserted (`__Host-`, Secure, HttpOnly, Lax, Path=/, no Domain, 256-bit value); session row with the resolved principal |
| S0001 AC3 | 3, 8 | API tests scan bodies and headers; e2e storage, cookie and URL scan |
| S0001 AC4 | 3 | One fixture for each failure reason; zero sessions; no session cookie; one `authentication_event` each; failure page text has no reason |
| S0001 AC5 | 3, 8 | `return_routes` unit table (absolute, `//`, backslash, encoded, unregistered → `/`); e2e malicious list |
| S0001 AC6 | 3 | Non-human `azp` and DISABLED principal fixtures → failure page, reason recorded |
| S0001 AC7 | 3, 7 | Same principal: old cookie → 401 at once. Different principal: old session `principal_changed` and the shell hygiene test |
| S0002 AC1 | 4 | Cookie request to `/reviews`, `/content` and `/facts` reaches the handler under the session principal; verifier and resolver call order asserted |
| S0002 AC2 | 4 | Matrix: missing or wrong token, foreign Origin, missing Origin and Referer, Referer fallback, `Sec-Fetch-Site: cross-site` → 403 `csrf_rejected`; handler spy not called; zero writes; event cause recorded |
| S0002 AC3 | 4 | Cross-site GET answered under normal authorization; no `Access-Control-*` headers |
| S0002 AC4 | 4, 5 | Distinct codes: unauthenticated, session_expired (idle, absolute, renewal), denial = existing 404 with the session still valid afterwards (R1), csrf 403. For each of idle, absolute and renewal-failed: a background poll ends the session first, then a user mutation still gets `session_expired`; a logged-out or replaced cookie gets `unauthenticated` |
| S0002 AC5 | 4, 7 | Cookie plus `Authorization` → 400 `ambiguous_credentials`; shell lint rule and client test confirm no `Authorization` header |
| S0002 AC6 | 4 | Existing bearer suites pass unchanged |
| S0003 AC1 | 5 | Expired access token → one refresh, request served, `Set-Cookie` absent |
| S0003 AC2 | 5, 8 | Two-worker PostgreSQL test with N concurrent requests → one token-endpoint call (stub) and all succeed or all `session_expired` (including waiters that lock after the failure); e2e recorder count = 1 |
| S0003 AC3 | 5, 8 | Rotated refresh token stored atomically; each failure kind ends the session, writes `renewal_failed` and returns 401 |
| S0003 AC4 | 5 | Frozen-clock idle test; background header does not extend the deadline |
| S0003 AC5 | 5 | 8 h absolute limit despite activity and renewals; no renewal attempted after it |
| S0003 AC6 | 7 | Component test: warning at 28 min (server time), countdown, "Stay signed in" sends one request, dismissing changes nothing |
| S0004 AC1 | 7, 8 | Client test: page and input kept; dialog lists blocked mutations as "not submitted"; zero retries. e2e: another tab or the background poll ends the timed-out session first; the later mutation still keeps its input and needs re-confirmation |
| S0004 AC2 | 7, 8 | Popup flow; completion signal carries only `ref`; dialog closes with input intact |
| S0004 AC3 | 7, 8 | GET retried once; mutation sent only on "Submit now"; "Cancel" discards it |
| S0004 AC4 | 7, 8 | Re-confirmed request carries the new CSRF token; stale or revoked variant → engine 404 or 409 shown in context, no retry; engine audit row present |
| S0004 AC5 | 7, 8 | Different principal → work and queue discarded, hygiene, Home; e2e principal isolation |
| S0004 AC6 | 7 | Blocked popup → "Sign in on this page" with the warning; storage spy shows no input written |
| S0004 AC7 | 7 | Messages from a foreign origin, a wrong `ref` or an unexpected source are ignored |
| S0005 AC1 | 6 | Logout: CSRF required; revoke called; session ended; expired cookie with identical attributes |
| S0005 AC2 | 6, 8 | Revoked token = the token held after rotation; authentik refuses a refresh grant with it |
| S0005 AC3 | 6, 8 | Each injected failure (unreachable, non-2xx, timeout): session ended, tokens NULL, `session_event` with reason, response `failed`, signed-out page warning |
| S0005 AC4 | 6 | Old cookie → 401 from every route, including when replayed from another client |
| S0005 AC5 | 7 | One hygiene test per trigger: requests aborted, cache empty before the new render |
| S0005 AC6 | 7, 8 | BroadcastChannel and a 30 s poll; e2e second tab shows signed-out within 60 s without old data |
| S0005 AC7 | 6, 7, 8 | End-session URL has no `id_token_hint`; return route single use and 2-minute rule (API tests); e2e `completed`, `failed` (error redirect and no endpoint) and `unconfirmed` (no return, sweep) each with its `session_event` and page text; next sign-in after `completed` asks for credentials |
| S0006 AC1 | 6 | Schema-validated response; no OIDC token; only the caller's memberships; display-name fallbacks. `csrf_token` identical across repeated reads from two workers and after reload; two tabs both mutate with it; after re-authentication the old token is refused |
| S0006 AC2 | 7 | Home and header component tests; axe at desktop and 360 px |
| S0006 AC3 | 7 | No-membership principal: "no access yet", empty selector, zero engine data calls |
| S0006 AC4 | 6, 7 | Member switch persists across reload; non-member → 422 and value unchanged; hygiene runs before render |
| S0006 AC5 | 6 | Engine request for another readable knowledge base still decided by policy; authorization code never reads the active value |
| S0006 AC6 | 6, 7 | Membership revoked mid-session → new `grant_revision` and list; active value reset; caches cleared |
| S0007 AC1 | 7 | Flag off or unknown: not-found, no chunk request (network spy), absent from navigation |
| S0007 AC2 | 7 | Flag on: lazy load inside the frame; forced import failure → retry screen, shell usable |
| S0007 AC3 | 7 | Build report: lazy route chunks separate; entry chunk free of them; budget script passes in CI |
| S0007 AC4 | 6, 7 | Flag file change reflected in the next `GET /session` without a rebuild |
| S0007 AC5 | 7, 8 | Review Panel at `/reviews/:id` through the cookie; receipt and audit row as before; denied item → not found |
| S0007 AC6 | 7 | Launch form and token field gone; `?token=` stripped and never sent (network spy) |
| S0008 AC1 | 4 | First 20 rejections: generic 401 and one event each |
| S0008 AC2 | 4 | 21st: 429, `Retry-After`, one `rate_limited` event; later: 429 and no event (R2). Sequential: the counter row's `xmin` and `pg_stat_user_tables` insert/update counts are unchanged across 100 further throttled requests. No IdP or JWKS call while throttled |
| S0008 AC3 | 4 | 1,000 rejections across two workers → at most 21 rows in the window; counter updates past 21 ≤ requests in flight when the threshold is crossed; a 30 s window setting is honored and a 7 s setting is refused at startup |
| S0008 AC4 | 4 | Throttled client with a valid bearer or session is served; other clients unaffected |
| S0008 AC5 | 3, 4 | Bearer, unknown cookie and callback failures all count; spoofed `X-Forwarded-For` from an untrusted peer ignored; trusted proxy honored |
| S0009 AC1 | 8 | `session-transport.spec.ts` (all S0009 rows run in the `chromium` and `firefox` projects; both must pass) |
| S0009 AC2 | 8 | Recorder refresh count = 1 for 20 parallel requests; revoked token = rotated token |
| S0009 AC3 | 8 | Injected revocation failure; then the success path with authentik refusing the revoked token; end-session outcomes as S0005 AC7 |
| S0009 AC4 | 8 | `principal-isolation.spec.ts`, `return-routes.spec.ts` |
| S0009 AC5 | 8 | `mutation-continuity.spec.ts` (fresh, stale and revoked variants) |

## Scope Breakdown and Handoffs

- **F0022:** Review Panel functional changes, renderers and batching on top of the rehosted route.
- **F0023:** Entity 360 routes registered through the seam.
- **F0067:** Observatory route behind a flag; inherits the D12 stack.
- **F0026:** production ingress (same origin, `/api` mount, CSP, HSTS), secret store for the client secret and session keys, `authentication_event` and `session_event` retention, back-channel logout, administrator session termination.
- **Later hardening (section 120.5):** idempotent command protocol for controlled retry.

## Integration Checkpoints and Completion Criteria

1. After Step 2: bearer regression green with the confidential client.
2. After Step 4: cookie path and CSRF matrix green; bearer suite unchanged.
3. After Step 5: two-worker renewal test green on PostgreSQL 18.
4. After Step 7: Vitest suites, axe checks and budget green; old Review Panel tests pass under the new route.
5. Feature complete:
   - all 55 ACs have observed proof;
   - S0009 is green from a clean volume;
   - at least 80% changed-line coverage;
   - security review of the cookie, CSRF, renewal, throttle and popup messaging;
   - ADR-0051 and ADR-0082 acceptance evidence recorded.

## Risks and Blockers

| Risk | Mitigation |
|---|---|
| authentik 2026.2 field names or behavior for post-logout redirect, rotation and invalidation differ | Feature G0 verification (R3) before Step 6; the `prompt=login` fallback keeps AC7's user-visible rule |
| IdP opener policy severs `window.opener` | BroadcastChannel is the primary completion signal (D8) |
| Safari (or Firefox) rejects `Secure` cookies on `http://localhost` | Chromium and Firefox are the proof browsers; G0 confirms Firefox; the HTTPS profile covers Safari and is the fallback for both (D4) |
| authentik does not return to `post_logout_redirect_uri` on error | Outcome becomes `unconfirmed` after 2 minutes and the user is warned (D7) |
| A renewal holds the row lock while calling the IdP | Bounded at about 11 s; per session only; separate transaction |
| Bundle growth from Radix and Tailwind | 180 kB gzip budget enforced in CI; lazy routes |
| Test-only access-token skew could leak into production | Absent outside the e2e composition; startup refuses it on non-localhost origins |

## DI Registration / Runtime Deployment

- `deps.py` composes these once at startup:
  - `OidcClient` (discovery cached for 1 h; backchannel base URL);
  - `TokenCipher` (key ring);
  - `BrowserSessionStore` and `CredentialThrottle` factories over the session factory;
  - `ReturnRouteAllowlist` and `FlagSource` (mtime-cached files).
- New environment variables: `BRAIN_PUBLIC_ORIGIN`, `BRAIN_PUBLIC_API_PREFIX`, `BRAIN_OIDC_CLIENT_SECRET`, `BRAIN_OIDC_BACKCHANNEL_URL`, `BRAIN_SESSION_KEYS`, `BRAIN_TRUSTED_PROXIES`, `BRAIN_THROTTLE_LIMIT`, `BRAIN_THROTTLE_WINDOW_SECONDS`.
- Committed non-secret configuration: `config/experience-flags.yaml`, `config/experience-routes.yaml`.
- Secrets are never committed except the dev-only client secret in the dev blueprint, which follows the existing dev-password pattern.

## Planning Status and Follow-ups

- Phase B approved 2026-11-27 with `approve-phase-b`; R1 and R2 confirmed.
- Plan review `2026-11-27-d1148686`: CONDITIONALLY READY (5 High, 1 Medium); all six resolved by rework run `2026-11-28-831962b8` (see Plan Review Rework), approved 2026-11-28 (`approve-phase-a`, `approve-phase-b`). R1/R2 wording applied in that run.
- Next: the feature run (feature G0 performs the R3 authentik checks and the Firefox cookie check).
- ADR-0051 and ADR-0082 stay Proposed until S0009 passes.
