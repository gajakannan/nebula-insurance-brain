# Architect — F0007 Completion Audit

Reviewer: Codex / Architect. Date: 2026-11-09. Scope: approved completion run `2026-11-09-b94cfa12`, commit range `ff0a619..fa8fc1d`, raw F0007 source/schema/ADR/archived plan. Manifest and latest-run pointer were read before selecting the cited architect report. No implementation, plan, KG or canonical completion evidence was changed.

## High — ARCH-FEATURE-01: accepted canonical decimal/money cannot be read back

Location: `engine/packages/brain-domain/src/brain_domain/fact_values.py:143` (input limit), lines 158–167 (output construction and distinct output limit), constants at lines 26–27; `engine/packages/brain-domain/src/brain_domain/fact_answers.py:224` (stored value revalidated). Schema: `planning-mds/schemas/fact-slot-key-v1.schema.json:108` (decimal input maxLength 64) and line 178 (money amount maxLength 64).

`canonical_decimal` accepts at most 64 input characters but emits up to 128 canonical characters. A short, schema-valid `1E+64` is accepted by `parse_answer` and becomes a 65-character amount/value. `stored_answer` passes that canonical value back through the input validator, which raises `ValueRejected: DECIMAL_INVALID`. This reproduces for both money and decimal, without database writes. The stored carrier also violates the shared schema's 64-character limit. Identity normalization and answer reload are not closed under the declared canonical encoding.

Impact: a valid exponent-form answer can commit successfully but cannot be loaded through the typed internal reader; replaying its canonical form is rejected. The current proof gates cover ordinary large amounts, not this valid exponent boundary. Remediation: align accepted input, canonical output and stored-carrier schema limits (or use a separate trusted canonical parser) and verify canonicalization idempotence plus commit/reload at positive/negative exponent limits. Owner: Backend with Architect schema reconciliation and QE regression evidence.

Evidence: `artifacts/architect-probes.json` contains both safe reproductions: input `1E+64`, canonical length 65, reload `ValueRejected: DECIMAL_INVALID`. The probe script is `/tmp/f0007_architecture_probes.py`. The security lane owns the separate unbounded exponent allocation defect; do not merge that different failure mode into this one.

## High — ARCH-FEATURE-02: database identity guard admits NULL identities

Location: `engine/migrations/versions/0012_f0007_factslot_identity.py:75` (`ck_fact_slot_identity`, through line 88); partial unique index at line 90; generated subject-KB key at line 69; deferred integrity function at line 154 onward.

Nullable v1 fields are compared without explicit non-null guards. SQL CHECK accepts UNKNOWN, so a v1 SINGLE SLOT with a NULL fingerprint satisfies the check, bypassing uniqueness on canonical identity. A NULL `identity_version` plus otherwise populated v1 fields is accepted too, outside the v1 index and the generated subject-KB FK. The integrity trigger only checks MEMBER parent shape or qualifier ownership; it does not reject incomplete SLOT rows. The identity immutability trigger makes any admitted malformed identity permanent rather than repairing it.

Proof: evaluate the exact migration CHECK in PostgreSQL using a read-only candidate CTE. For both NULL-fingerprint and NULL-version cases, `check_result IS NULL` and `check_result IS NOT FALSE` return true. The guard is not guaranteed TRUE. No shared database insert or update was attempted. See `artifacts/architect-postgres-proof.md` and the query text in `artifacts/architect-probes.json` (initial sandbox-denied attempt is preserved; the successful direct approved Docker invocation is recorded separately).

Remediation: a follow-up migration should make the complete legacy-or-v1 expression require TRUE, explicitly constrain every required v1 field, and audit existing malformed rows before adding the tightened constraint. Add service-role direct-SQL negatives for each NULL mandatory field, NULL version with populated fields, and duplicate NULL fingerprints. Owner: Backend/Architect; QE verifies real PostgreSQL behavior. The same defect exists in the approved plan SQL and is also recorded as ARCH-PLAN-01.

## Alignment and limitations

- Source follows the intended Domain → application ports/services → persistence → API composition boundaries. `brain-temporal` uses a protocol rather than a reverse dependency on `brain-factslots`.
- MULTI children preserve per-member temporal exclusion without changing the F0008-owned version table. Legacy-slot bypass and downstream RLS, temporal close, schema-publication and precedence ownership are explicit.
- New capabilities/entities/schema/migration paths are represented in the authored F0007 bindings. Global KG validators are owned by the primary reviewer; raw source overrides any stale prose notes.
- Prior `architect-implementation-review.md` says PASS and claims typed-value and ownership proof gates. The concrete counterexamples above contradict a full completion verdict despite those summaries.
- The code-review lane owns the separate member-key/value mismatch; architecture supports it under ADR-0077:73 and :117. It is not counted again here.
- Fresh verification here is pure domain execution and PostgreSQL expression evaluation; this lane did not rerun the full migration/application test suite or alter live schema/data.

## Recommendation

Two High findings in this Architect section. Do not declare TRULY DONE before repair and regression evidence. Overall severity verdict is the primary reviewer's responsibility and includes the other role lanes.

