## Buildability Challenge

Reviewer: code-reviewer, independent PR1 lane. Scope: F0021 current planning package; no DIFF_RANGE. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Review run: `2026-11-27-d1148686`.

**Lane assessment: CONDITIONALLY READY. Counts: 0 critical, 2 high, 0 medium, 0 low.** Implementation ownership is present. Two requirements conflict with the prescribed implementation/proof handoff and need planning-owner reconciliation before feature implementation. Architecture findings are owned and counted in the Architecture Readiness section, not duplicated here.

### Findings

#### BUILD-01 — High — The real-browser proof plan omits required Firefox execution

- **Evidence:** `planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session/F0021-S0009-prove-session-transport-and-mutation-continuity.md:46`, Non-Functional Expectations, requires the proof to run in at least Chromium and Firefox. `planning-mds/architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md:49`, D4, explicitly specifies Chromium for S0009. `planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session/feature-assembly-plan.md:249`, Step 8, names authentik, Chromium and Playwright versions for the evidence, without a Firefox project or equivalent proof lane. PRD A1 at `PRD.md:210` also includes Firefox in the supported browsers.
- **Trigger / consequence:** A developer or QE follows the detailed Step 8 harness and runs the entire real-authentik proof in Chromium. Every listed design proof can pass while the stated two-browser requirement remains untested. Cookie handling, popup completion and cross-tab behavior are exactly the behavior for which a second browser matters. The handoff currently offers conflicting completion criteria.
- **Repair owner:** Architect and Product Manager reconcile the intended matrix; Quality Engineer and DevOps own the resulting harness/CI plan.
- **Required repair:** Specify Chromium and Firefox execution, shared fixtures, per-browser results/version evidence and mandatory CI outcome for the relevant S0009 proofs. If Chromium-only is intended instead, obtain an explicit requirement amendment and reconcile the story and support claims before implementation. This audit makes no amendment.
- **Acceptance evidence after repair:** A consistent S0009 story, ADR and harness plan; the subsequent feature run must produce actual evidence for the agreed matrix. No already-completed browser tests are required by this plan review.

#### BUILD-02 — High — The prescribed throttle writes on every rejected request despite its no-write NFR

- **Evidence:** `planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session/F0021-S0008-throttle-rejected-credentials.md:46`, Non-Functional Expectations, says the throttle check adds no database write for throttled requests. `planning-mds/architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md:92`, D9, increments the PostgreSQL rejection counter for each rejected credential, including counts above 21. The concrete statement in `planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session/migration-design.sql:100`, Counting statement, performs `ON CONFLICT ... DO UPDATE` without a saturated-counter/read-only path; `migration-design.sql:103` increments it unconditionally.
- **Trigger / consequence:** Once one client has reached the limit, every further invalid request still updates and locks its counter row. The audit-row bound can pass while the explicit no-database-write throttle condition fails. An implementation agent cannot both follow the prescribed SQL and satisfy the current NFR. The existing proof map at `feature-assembly-plan.md:308` through its S0008 rows checks HTTP outcomes and audit-row counts, but does not prove the no-write condition.
- **Repair owner:** Architect with Product Manager; backend-developer and Quality Engineer implement/prove the reconciled rule in the later feature run.
- **Required repair:** Define the post-threshold counter behavior and concurrent-worker policy so throttled rejections use a genuinely read-only path, or explicitly amend the NFR to permit bounded counter updates while suppressing per-request audit inserts. Add a proof of the agreed database-write behavior alongside the existing 1,000-request/two-worker audit-row bound. Preserve valid-credential pass-through and trusted-proxy behavior. Treat configuration semantics in the same reconciliation, because the story calls the limit/window configuration values while the design prescribes minute-aligned 60-second windows.
- **Approved reconciliation boundary:** R2 at `feature-assembly-plan.md:36` resolves local verification versus valid-credential pass-through and per-request `authentication_event` suppression. It does not amend this separate no-database-write NFR. R2 itself is not reported as an unresolved finding.

### Handoff and vertical-slice assessment

| Review item | Outcome and concrete planning evidence |
|---|---|
| Prerequisites and sequencing | F0002 verification/memberships and the existing Review Panel are explicit prerequisites; F0011 supplies generated contracts (`PRD.md:224`, Dependencies). Eight ordered build steps and their dependencies are specified at `feature-assembly-plan.md:43`, Build Order. The confidential-client tooling change has a mandatory bearer-regression checkpoint before sign-in construction (`feature-assembly-plan.md:124`, Step 2). |
| Ownership | Backend, frontend, QA and DevOps involvement is listed per story at `STATUS.md:24`, Story × Role Progress. `STATUS.md:40` and `STATUS.md:49` assign server and client deliverables. Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect are the required signoff roles at `STATUS.md:62`. Backend work supporting popup re-authentication belongs to S0001; server flag delivery belongs to S0006, so the front-end-only S0004/S0007 cells do not leave those operations ownerless. AI is explicitly out of scope. |
| File/interface direction | Existing files to change, new modules, tests, migration and harness locations are concrete at `feature-assembly-plan.md:56` and `feature-assembly-plan.md:76`. The API fragment has five BFF paths (`bff-api-design.yaml:13`); the contract inventory records planned consumer entry points, validation and regeneration (`contract-inventory.yaml:4`). These are sufficient to scope feature G0 without a broad speculative code search, subject to the architecture lane's contract findings. |
| Existing consumer compatibility | The planned bearer dependency change targets the actual `current_principal` verifier/resolver path (`engine/apps/api/src/brain_api/deps.py:163`). The current panel's bearer calls at `experience/src/review-panel/api.ts:21` and `experience/src/review-panel/api.ts:38` substantiate the specified shared-client rehost at `feature-assembly-plan.md:73`. Existing review/security test files are present; their future regression execution is explicitly required. |
| Slice size and boundaries | This is a substantial cross-cutting slice with nine stories. It still has a coherent deployable outcome, explicit ordered integration checkpoints, and a terminal end-to-end story (`feature-assembly-plan.md:327`). No unsupported duration estimate is asserted. F0022/F0023/F0067 consume the seam, while production ingress/retention/back-channel termination stay with F0026 (`feature-assembly-plan.md:319`). No new scope is inferred. |
| BRAIN-BUILDABILITY | **Gaps: BUILD-01 and BUILD-02.** Owners, prerequisites, interfaces, handoffs and test tiers otherwise have concrete references above. The gaps concern conflicting completion rules, rather than the absence of future runtime deliverables. |

### Acceptance criteria and planned validation

All nine raw stories were inspected. Their 55 acceptance criteria have a design-to-proof map at `feature-assembly-plan.md:259`; `acceptance-criteria-checklist.md:3` correctly reserves observed proofs and the final AC-to-test map for the feature run.

| Story | Planned proof layers and important negative cases |
|---|---|
| S0001 (7 ACs) | Login/callback API tests, return-route unit table, per-refusal fixtures, session-fixation/principal-change cases, browser token-absence inspection; `feature-assembly-plan.md:263`. |
| S0002 (6 ACs) | Cookie-route integration, per-cause CSRF matrix with no-handler spies, ambiguity, distinct error taxonomy and unchanged bearer regressions; `feature-assembly-plan.md:270`. R1's operator-confirmed 404 denial reconciliation is an accepted input, not a new finding. |
| S0003 (6 ACs) | PostgreSQL two-worker renewal concurrency, token rotation and failure cases, controlled idle/absolute time, component warning behavior; `feature-assembly-plan.md:276`. |
| S0004 (7 ACs) | API-client/component tests plus real-browser proofs for explicit reconfirmation, zero pre-confirmation effects, stale/revoked authority, principal isolation and popup failure/message rejection; `feature-assembly-plan.md:282`. |
| S0005 (7 ACs) | Server logout integration, actual rotated-token revocation, injected failures, replayed-cookie refusal, one hygiene test per trigger and a second-tab end-to-end case; `feature-assembly-plan.md:289`. |
| S0006 (6 ACs) | Generated-schema guard, component/axe checks, empty-membership isolation, selector persistence and refusal, grant-revision reset; `feature-assembly-plan.md:296`. |
| S0007 (6 ACs) | Flag and chunk network spies, failed import behavior, build-budget evidence/CI, rehosted panel integration and token-query stripping; `feature-assembly-plan.md:302`. |
| S0008 (5 ACs) | Two-worker PostgreSQL burst/audit-count proof, valid-credential pass-through and trusted-proxy tests; `feature-assembly-plan.md:308`. The no-write NFR proof is unresolved under BUILD-02. |
| S0009 (5 ACs) | Clean-volume real authentik/PostgreSQL/built-shell execution, recorder-based refresh/revocation observation, storage inspection, principal isolation and mutation continuity; `feature-assembly-plan.md:241`. Its Firefox matrix conflict is BUILD-01. |

The plan requires at least 80% changed executable-code coverage (`STATUS.md:60`, `feature-assembly-plan.md:336`), developer-owned component tests, integration tests and browser proofs. UI tests include WCAG 2.2 AA/axe checks at desktop and 360 px. DevOps owns the confidential-client/dev-tooling, proxy and disposable browser composition through S0001/S0007/S0009. Existing/source test execution, numerical coverage and runtime security scans are later feature evidence, not outputs asserted by this audit.

### Nine-dimension self-check adapted to a plan review

| Dimension | Review result |
|---|---|
| Correctness and logic | Inspected story edge cases, request outcome mapping and the implementation/proof map; contradictions reported above, architecture defects remain in that lane. |
| Architecture boundaries | Shared verifier/resolver and existing authorization facade remain the server boundary; module wiring and typed schema consumers are specified. Architecture lane owns detailed decision adequacy. |
| SOLID / responsibility separation | Distinct OIDC, cookie, CSRF, crypto, return-route, store and client modules are named (`feature-assembly-plan.md:78`). No executable implementation exists to judge for class-level compliance. |
| Test quality and coverage | Unit, API/integration, component, browser, concurrency, accessibility and deployment checkpoints are mapped; BUILD-01/02 identify uncovered completion requirements. |
| Error handling | Failure/status contracts, retry limits, no unsafe replay, revocation failure display and popup fallback are concrete; lifecycle contradictions are counted by the architecture reviewer. |
| Performance | Explicit idle-write coalescing, renewal lock/timeout, throttling, lazy chunks and 180 kB gzip initial-JavaScript budget are specified; BUILD-02 concerns counter writes under load. |
| Readability and naming | Handoff paths, owning modules and story references are usable; no naming/style findings justify distracting from readiness issues. |
| Acceptance-criteria mapping | All 55 ACs have planned proof references above. Runtime AC-to-code mapping is intentionally deferred to the feature action. |
| Over/under-engineering | One BFF module inside the existing deployable, PostgreSQL reuse and one request client fit the stated scope. Missing implementation ports or exact helper signatures are ordinary feature-G0 design details; the concrete contract gaps are not hidden as such. |

### Risk and extra-review handoff

Read-only KG risk results are retained in `artifacts/test-results/build-risk.log` and compacted in `artifacts/build-risk-summary.json`. F0021's maximum score is **6/10, elevated**. Credential verification and the existing review round trip each score 6; their reported hotspot ranks are 36 and 11 respectively, and both report one primary owner. The remaining 16 resolved nodes score 2. A separate file-risk check for the modified shared dependency `engine/apps/api/src/brain_api/deps.py` maps to runtime-roots/toolchain, score **5/10, elevated**, hotspot rank 23 (`artifacts/test-results/build-risk-shared-deps.log`). None of these results crosses the high/critical risk or top-five hotspot thresholds.

The primary-owner/bus-factor signals call for explicit owner acknowledgement on the eventual implementation PR. Regression attention belongs on verifier/resolver behavior, authorization consumers and review/commit/content callers because the shared dependency changes. Keep the multi-role code/security/architect reviews and the unchanged-bearer checkpoint. The risk tool's zero bound test-file count is a mapping signal: raw `test_verification.py`, `test_principals.py`, `test_reviews.py` and panel component tests exist, so it is not treated as proof that tests are absent. PR acknowledgement and runtime coverage are future merge obligations; this read-only planning review does not manufacture them or classify their future absence as a current finding.

### PR3 self-review confirmation

- Each finding cites exact raw files, line locations and sections, states a reproducible conflicting outcome, and assigns repair ownership. No build-critical gap was downgraded to low severity.
- R1/R2 operator-confirmed reconciliations were treated as current decisions. BUILD-02 identifies the separate untouched database-write condition.
- All nine story files, PRD, current design, STATUS/GETTING-STARTED, contract inventory, API fragment and migration design were inspected directly. Existing code was inspected only to substantiate the named handoffs.
- `feature-assembly-plan.md` was used as an existing design artifact; its existence is not a prerequisite asserted by this review.
- Runtime test execution/coverage, code lint, executable line-level AC mapping, SAST/DAST/dependency scans, implementation symbol regeneration and production ingress verification are explicitly not applicable to this planning-only lane. Core PR2 validators and the project check are owned by the root orchestrator.
- No new product/source/plan/KG/tracker/approval/feature-evidence artifact was edited. This independently authored section and risk/read logs are base-run evidence only.

Final lane counts: **critical=0; high=2; medium=0; low=0**. No missing build-critical owner was found. Repair routes back to the planning lifecycle owners; the review itself performs no repair.
