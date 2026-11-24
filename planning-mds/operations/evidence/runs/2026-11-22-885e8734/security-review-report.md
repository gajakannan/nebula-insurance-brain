# Security Review Report — F0011-json-schema-contract-system run 2026-11-22-885e8734

## Scope

- Feature ID: F0011
- Run ID: 2026-11-22-885e8734
- Date: 2026-11-23
- Reviewer: Claude / Security Reviewer (final G3 verdict). This builds on the
  preparatory independent work by Codex / Security Reviewer
  (`artifacts/security/dependency/soupsieve-disposition.md`, scan receipts and
  CR-F0011-04 observation).

`security_sensitive_scope = true`: the feature adds offline parsers and decoders,
a closed schema registry, response guards on authorized FactSlot reads and commits,
and new dependency/build controls.

## Reviewed Surfaces

- API: `engine/apps/api/src/brain_api/{contract_guards,contract_openapi,errors,app}.py`,
  `routes/facts.py` (GET fact, POST commit).
- Domain write path: `brain_temporal/commit.py` (temporal carrier guard),
  `brain_factslots/{answers,resolution}.py`, `brain_content/contracts.py`,
  `brain_contracts/assertions.py`.
- Parser/registry: `brain_contracts/schema_runtime.py`, `model_adapter.py`,
  `experience/scripts/contracts/runtime.mjs`.
- Build/tooling: `scripts/contracts/*.py` (generator, checker, stored-history
  sweep, install smoke), `docker/contracts/Dockerfile`, `.dockerignore`,
  `.github/workflows/ci-gates.yml`, both Python locks and the pnpm lock.
- Dependency exposure: Engine, Neuron and experience installed pins.

## Threat Boundary

| Subject | Resource | Operation | Boundary change in F0011 |
|---|---|---|---|
| Authenticated principal | FactSlot version (GET) | READ | Response is guarded **after** the existing authorization, source READ checks and read audit. Denied source READ still returns 404 before any guard runs. |
| Authenticated principal | FactSlot commit (POST) | COMMIT | Response is guarded **inside** the existing mutation operation, so a guard failure rolls back versions, changes and outbox. Tests reread authoritative state after injected failure. |
| Any caller | `/openapi.json` | READ | Served from the installed, hash-admitted bundle snapshot. A corrupt bundle refuses startup. |
| Build/CI | Contract bundle, generated models | Generate/verify | Closed local registry (`Registry(retrieve=_no_retrieve)`), no network retrieval; JS has no `loadSchema` callback. |
| CI runner | Locked wheels | Fetch | `install_smoke.py` fetches only URLs from committed `uv.lock` and verifies the locked SHA-256 before writing. |

## Auth / Authz

No new route, permission key, grant, role gate or tenant-scope rule. Guards consume
already-authorized, normalized output and never broaden or narrow access. Existing
F0007/F0008 authorization suites pass in the PostgreSQL consumer lane (81/81).

## Validation

- The portable profile bounds untrusted JSON: raw bytes ≤ 16 MiB
  (`MAX_BYTES`), depth ≤ 128 including scalar leaves (`MAX_DEPTH`), nodes ≤ 1,000,000
  (`MAX_NODES`); strict UTF-8; no comments or trailing commas in JS; duplicate and
  unsupported constructs are refused. Decoded-value byte accounting uses pinned
  RFC 8785 (`rfc8785==0.1.4`) identically across languages (CR-F0011-03).
- Caller-selected fragments must be admitted schema positions in both languages
  (CR-F0011-04). Annotation data (`default`, `examples`) cannot be selected as an
  accepting schema.
- Pattern end-anchors are exact in the portable registry (CR-F0011-02); native
  legacy readers keep their frozen behaviour, and no failed portable read falls
  back to a laxer reader.
- Request validation for existing routes is unchanged (FastAPI/Pydantic).

## Audit / Logging

- Read audit semantics (PR-L3): see Recommendation Disposition.
- The new `contract_invariant_failed` 500 handler returns a fixed generic body with
  `detail: null` and `instance: null`, and carries every baseline security header.
  This was verified by a reviewer probe in the Engine runtime
  (`artifacts/security/contract-error-headers-probe.json`). No instance data,
  pointer or exception text crosses to the client.
- Both 500 handlers (`contract_invariant_failed` and the existing `internal_error`)
  now log at ERROR with the same `traceId` the client receives, so operators can
  correlate a reported failure. The contract handler logs only the fixed code,
  contract id, schema pointer, method and path. The generic handler logs only the
  exception class, never its message or traceback, preserving F0008's rule that
  database text (which can quote rows) does not propagate. Unit tests assert trace
  correlation and that exception text is absent from both log and body. This was
  fixed at G4; see Findings.

## Secrets / Config

No secret is added or read. CI uses the existing ephemeral service-container
database credentials (the same `brain:brain` URLs already present eight times at
base `bf78e11`), triggers on `pull_request` (not `pull_request_target`) and uses no
repository secrets. Validation containers set only non-secret build variables. The
secrets scan on current source found 0 leaks.

## Scan Disposition

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|-------|-----|--------------------------|---------------------------|
| dependency | Yes | Engine 75 pins: 0 advisories. Experience: 0. Neuron 171 pins: **0 advisories** after the G4 SoupSieve 2.9.2 → 4.1.3 lock-only upgrade (the earlier 4 advisories are retained in `neuron-before-soupsieve-remediation.json`) | `artifacts/security/dependency/summary.json`, `artifacts/security/dependency/soupsieve-disposition.md` |
| secrets | Yes | 0 findings, 166 changed/untracked files, redacted, network none; final re-run after the G4 fixes and the G8 archive move | `artifacts/security/secrets/2026-11-24-closeout-final/execution.json` |
| sast | Yes | 1 WARNING `dynamic-urllib-use-detected` at `scripts/contracts/install_smoke.py:119`. Accepted as informational: CI/dev tooling only, URL comes from the committed lock, and the content is SHA-256-verified against the lock before use. Fresh scan of all 37 current changed code files after the G4 fixes; no new finding. | `artifacts/security/sast-closeout/execution-summary-closeout.json`, `artifacts/security/sast-closeout/current-input-reconciliation.json` |
| dast | Yes | ZAP OpenAPI active scan of the private candidate API: 119 pass, 0 fail, 0 warn | `artifacts/security/dast/execution.json` |

## OWASP Top 10 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | OK | No authz change; guards run post-authorization; 404-before-guard for denied source READ preserved. |
| A02 Cryptographic Failures | N/A | No crypto change. RFC 8785 is canonicalization, not cryptography. |
| A03 Injection | OK | No query or command construction added. Schema patterns are ASCII-class only; no user-controlled regex. |
| A04 Insecure Design | OK | Fail-closed profiles, no fallback, closed registry, rollback on commit-guard failure. |
| A05 Security Misconfiguration | OK | Invariant 500 carries baseline security headers (probed). No debug detail. |
| A06 Vulnerable / Outdated Components | OK | Pre-existing SoupSieve 2.9.2 upgraded to 4.1.3 at G4; all workspaces audit clean. |
| A07 Identification & Authentication | N/A | Unchanged. |
| A08 Software & Data Integrity | OK | Bundle hash/version/ref closure admitted before any instance; generated-artifact drift refused; locked-wheel digests verified; publication rollback tested. |
| A09 Security Logging & Monitoring | OK | 500 handlers log a correlatable traceId without instance data or exception text (fixed at G4). |
| A10 Server-Side Request Forgery | OK | No runtime retrieval (`_no_retrieve`); install-smoke fetch is lock-sourced, build-time only. |

## Findings

Open: critical 0, high 0, medium 0, low 0.

Two Lows were raised at G3 and **fixed before approval** at the user's G4 direction:

1. SEC-F0011-01 (low, closed): Neuron locked SoupSieve 2.9.2, which had four
   availability advisories (CVE-2026-126190..126193). It was pre-existing at base
   `bf78e11` and not reachable through the PDF-only adapter. Fixed by a
   single-package lock upgrade to 4.1.3. The fresh audit is clean, the full Neuron
   suite passes, and docling's `p:has(...)` selector shape works
   (`artifacts/security/dependency/soupsieve-disposition.md`, Remediation).
2. SEC-F0011-02 (low, closed): the 500 handlers returned a `traceId` that was never
   logged server-side. Fixed in `brain_api/errors.py` with tests in
   `engine/apps/api/tests/test_errors.py`.

## Recommendation Disposition

- SEC-F0011-01 SoupSieve: mitigated now (upgraded). No residual and no PM acceptance needed.
- SEC-F0011-02 invariant-500 logging: mitigated now (implemented and tested). No residual.
- SAST WARNING (`install_smoke.py:119`): accepted as informational, not a finding.
- **PR-L3 (read audit before response guard): accepted, no finding.** An
  authorized GET whose normalized output then fails the response invariant leaves
  a SUCCEEDED read-audit row and returns a generic 500 with no data. The audit
  therefore errs toward over-reporting access. It never under-reports, which is
  the safe direction for an access log. Denied source READ still returns 404
  before guard evaluation, so the guard reveals nothing about inaccessible
  resources. Fault injection proving this is in the consumer integration suite.
  Both actual environment histories passed the signed READ ONLY sweep, so no
  stored row currently triggers the path. A redesign is not required.

## Result

Result: PASS
