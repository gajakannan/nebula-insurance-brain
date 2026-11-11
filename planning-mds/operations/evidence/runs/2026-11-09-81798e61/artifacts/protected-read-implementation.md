# FR-M1 protected-read remediation

Role: Backend Developer, with security-boundary review. Operator authorized the F0007 remediation; primary Architect approved the design and G0 before these edits.

## Change

`AuthorizationExecution.read` accepts an optional asynchronous `additional_reads(payload)` callback. It authorizes the primary resource, loads the payload once without releasing it to the caller, derives keys from that exact payload, authorizes the additional READs with current authority/resource locks still held, rechecks time-sensitive decisions, audits every decision, and commits once before returning. Existing callers without extra keys retain their interface and behavior.

The internal FactSlot answer reader derives the artifact key from the loaded `FactAnswer.scope`. The HTTP GET derives it from the already-selected `FactVersion.value` through `FactAnswerReader.scope_keys_for_value`, retaining the legacy-slot bypass. Neither path performs a separate committing scope precheck or reselects the answer after checking a different scope. The unused `AuthorizedFactSlots.authorize_scope_reads` precheck method was removed.

Denied primary resources never load/discover payload dependencies. A denied scope produces a FAILED primary decision and DENIED scope decision, committed durably with no payload. Discovery/load failures audit FAILED; audit storage failure releases no payload. Existing 404 mapping for missing/denied slots is retained.

## Files

- `engine/packages/brain-security/src/brain_security/execution.py`
- `engine/packages/brain-factslots/src/brain_factslots/service.py`
- `engine/packages/brain-factslots/src/brain_factslots/answers.py` — reader section only; member-validation edits belong to the parallel value/member lane.
- `engine/apps/api/src/brain_api/routes/facts.py`
- New `engine/packages/brain-security/tests/test_payload_reads.py`
- New `engine/tests/integration/test_factslot_authorized_reads.py`

## Verification

- `artifacts/protected-read-unit.txt`: 28 passed, including six new payload-read tests and the existing execution suite.
- `artifacts/protected-read-lint.txt`: relevant source/new test files pass Ruff.
- `artifacts/protected-read-format.txt`: relevant files formatted.
- `artifacts/protected-read-mypy.txt`: 17 security/factslot/route source files pass mypy.
- PostgreSQL tests are written for the existing owned-database harness. Primary QE owns their combined execution and resulting evidence; this note does not claim a fresh PostgreSQL pass.

## Meaningful regression expectations

The HTTP test simulates an earlier scope discovery returning a readable artifact while the actual selected version contains a restricted artifact. GET must deny the exact selected version. The PostgreSQL concurrency test pauses the private answer load, attempts supported `revoke_membership` in a separate transaction under a short lock timeout, and requires revocation to block on the held authority lock. Both successful READ audits must share the same authority revision; the answer is selected exactly once. After read commit, revocation succeeds and both internal/HTTP subsequent reads deny.

The old audit fake revokes immediately after the first commit. With this repair that is the grouped read's final commit, so the old output label alone is not a correct pass/fail assertion; same-revision grouped decisions and real lock contention are the relevant proof.
