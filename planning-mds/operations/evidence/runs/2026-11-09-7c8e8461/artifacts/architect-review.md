# Architect — F0007 Plan Readiness

Reviewer: Codex / Architect. Date: 2026-11-09. Scope: archived F0007 planning package and governing raw ADR/schema artifacts. Findings were self-reviewed against the raw sources. No plan or canonical feature evidence was modified.

## High — ARCH-PLAN-01: planned identity CHECK accepts incomplete identity rows

Location: `planning-mds/features/archive/F0007-factslot-model/feature-assembly-plan.md:186` (identity CHECK through line 199); nullable columns at line 172; unique index at line 201.

The proposed SQL combines a legacy branch with a v1 branch using ordinary comparisons on nullable identity fields. SQL CHECK rejects FALSE but accepts UNKNOWN. A v1 SINGLE SLOT with `identity_fingerprint = NULL` and otherwise valid values makes the entire expression UNKNOWN and passes. A row with `identity_version = NULL` but populated v1 role/predicate/fingerprint fields also passes. The deferred trigger described at line 223 only validates member parents and qualifier targets, so it does not make these SLOT rows fail.

This undermines the promised database identity backstop: NULL fingerprints do not conflict in the unique index, and a NULL version also skips the generated subject-KB ownership key. The approved DDL needs explicit non-null requirements for every required v1 field and an expression guaranteed TRUE (for example `CHECK ((legacy_branch OR v1_branch) IS TRUE)` with correctly complete branches). Add direct-SQL negative cases for each nullable required field and for partially populated legacy rows. Owner: Architect and Backend; resolve before build/re-approval.

Evidence: exact migration check expression has the same defect; read-only PostgreSQL SELECT evaluation recorded in `artifacts/architect-postgres-proof.md` returns `t|t` for both cases (`check_returns_unknown`, `postgres_check_accepts`). No shared database rows were written. This is review of an available design artifact; no assembly plan is demanded as a new plan deliverable.

## Contract observations

- Cardinality, versioned predicate keys, qualifier normalization, absence scopes, typed values, security actions, legacy handling, ownership, rollout/downgrade and role handoffs are concretely specified.
- The no-UI/no-new-route justification is explicit. F0018 RLS/restriction re-derivation, F0008 envelope DB backstop and temporal close, F0017/F0023 display precedence, and F0011 schema publication are explicit downstream ownership decisions; none is falsely reported missing from F0007 scope.
- The code-review lane owns the additional missing MULTI member/value commit invariant. Architectural support is ADR-0077:73 (member key is canonical member value/entity), ADR-0077:117 (normalized name is its member key), and S0002 AC3 at story line 24. Avoid counting that finding twice across roles.

## Recommendation

Architecture readiness: CONDITIONALLY READY, with one High finding owned in this section. Final action verdict and global validator evidence are owned by the primary reviewer.

