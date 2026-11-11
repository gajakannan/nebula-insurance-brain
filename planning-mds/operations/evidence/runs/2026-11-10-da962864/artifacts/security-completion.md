# Security completion assessment — F0007

**PASS — no open security findings.** Critical: 0; High: 0; Medium: 0; Low: 0. This is the Security lane verdict for the final `feature-review` closeout audit, not an independent deployment authorization.

Reviewer: Codex / independent Security Reviewer. Date: 2026-11-10. Audit run `2026-11-10-da962864`; approved completion run `2026-11-09-81798e61`; working tree relative to `fa8fc1d`. The reviewer did not author implementation or tests. Writes were limited to this new audit package.

## Final source and evidence continuity

- Read the current F0007 `latest-run.json` and cited manifest before the approved Security report and selected raw artifacts. The pointer and manifest agree on `2026-11-09-81798e61`, approved/Archived. The prior `2026-11-09-b94cfa12` manifest is `superseded` by this run. The approved Security role result is PASS; all four scan entries ran, resolve to raw artifacts and have no waiver. The terminal manifest has no active validator waiver.
- Independently compared all **51** engine/Neuron/tool/CI files in the scan snapshot to current source bytes: zero changed, zero missing. No existing runtime path in the final manifest's changed-file inventory is missing from that snapshot. This includes both inherited Neuron test adaptations, new migration0013 and all protected-read, member and numeric runtime changes. The final archive/approval/metadata updates did not invalidate that runtime evidence. Exact comparisons: `security-completion-source-match.txt`, `security-completion-raw-evidence.txt`.
- Ran scoped terminal evidence validation directly: exit0, `validated=1`, no skips. Advisory `commands_log_absolute_cwd_warns` was emitted for missing Run Environment justification of absolute working directories. It is evidence-format housekeeping, not a security finding or a failed closeout check. See `security-completion-closeout.txt`.

## Security control disposition

| Prior finding | Current source and evidence |
|---|---|
| FR-M1 — scope-read revocation/selection race | `AuthorizationExecution.read` privately loads once after primary authorization, derives the exact returned payload's scope keys, authorizes/rechecks under the same current-authority locks and commits all decisions before return. HTTP and internal FactSlot reads both use this path. Real PostgreSQL regression shows revocation waits until the grouped read completes, then a subsequent read denies. Primary denial, scope denial, expiry and failed audit do not release the payload. |
| FR-M2 and FR-H1 — numeric expansion and canonical round trip | Decimal normalization calculates the total canonical length before exponent padding. The 64-character bound includes sign/point and matches the input/schema limit. Oversized work is rejected before allocation; accepted boundary answers round trip through canonical storage. |
| FR-C1 — member identity mismatch | A PRESENT answer must derive the stored immutable member key under the pinned contract. Evidence/ownership checks and outer commit authorization precede the named mismatch detail. Entity, name and identifier regressions cover rejection without canonical writes and canonical-equivalent success. |
| FR-H2 — incomplete identity accepted by SQL CHECK | Follow-up0013 requires complete legacy-or-v1 shape to be TRUE, preserving immutable0012 and the composite tenant/KB ownership keys. It inventories malformed rows under lock, refuses with count/limited IDs and does not repair or expose values. Owned PostgreSQL regressions cover required NULL fields, partial legacy, malformed-data refusal and up/down/up preservation. |

Raw JUnit reconfirms 319 targeted container tests and 868 final engine tests, each with zero failures, errors or skips. The earlier authorization, test and scan evidence is used because the final runtime/source snapshot is unchanged; this audit did not rerun active tests or scans. It does not infer deployment on the shared database or formal acceptance of ADR-0077.

## Raw scan disposition

| Class | Approved raw artifact in `2026-11-09-81798e61` | Independent closeout disposition |
|---|---|---|
| Dependency | `artifacts/security/dependency-engine.json` | 57 packages, zero vulnerability entries in the recorded fresh result |
| Secrets | `artifacts/security/secrets.sarif` | Zero SARIF results |
| SAST | `artifacts/security/sast.sarif` | Two `avoid-sqlalchemy-text` results at `0013_f0007_identity_guard.py:70` and `:73`; both false positives. `invalid` is composed solely from the literal `IDENTITY_SHAPE` constant, and returned row IDs are used only in the refusal message. No request, environment or database value enters SQL text. Preserve the manifest's raw `findings` result and the approved `artifacts/security/sast-triage.md` disposition; no suppression or waiver. |
| DAST | `artifacts/security/dast/api-scan.json` | Console records 113 PASS and zero WARN/FAIL. Raw JSON has two risk-code-0 informational alert types. The scan covered unauthenticated OpenAPI reach; authenticated scope/denial behavior is supported by code inspection and real PostgreSQL HTTP/facade regressions, not inferred from the scanner. |

No new permission, secret, public endpoint, grant, external service call or RLS bypass was introduced in the audited changes. F0018 restriction re-derivation/RLS and F0008 database-level answer envelope enforcement remain explicit downstream boundaries. No Security recommendation or mitigation acceptance remains open. No canonical artifact, source, test or tracker was changed during this final audit.
