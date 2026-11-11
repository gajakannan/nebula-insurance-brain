# F0007 Code Reviewer completion audit

Reviewed current commit `fa8fc1d` against `ff0a619`, archived F0007 stories, ADR-0077, source and representative unit/integration tests. Original completion run: `2026-11-09-b94cfa12`. This fresh audit did not edit implementation, tests, plans or original evidence.

## Decision

**FIX CRITICAL FIRST.** A completed feature cannot pass with the member identity defect below. The primary auditor owns the combined FR4 decision and fresh validation summary.

## CR-AUDIT-01 — Critical — PRESENT answers can change the value that defines an immutable MULTI member

- **Location:** `engine/packages/brain-factslots/src/brain_factslots/answers.py:102` and `:106`–`:116`.
- **Contract:** `F0007-S0002-distinguish-single-multi-and-relationship-slots.md:24` derives each member identity from its normalized value/entity; ADR-0077 D4 (`:73`–`:74`) says the member key encodes that value/entity, and D6 (`:117`) defines normalized name as the name-member key. `brain_domain/fact_slots.py:196` implements the canonical `member_key` function.
- **Trigger:** Resolve a MULTI member for entity A, then commit a PRESENT `entity_ref` to a different entity B in the same KB. The answer policy only checks that B belongs to the KB. The same issue affects the deployed system predicates: resolve `sys:hasTradeName@v1` with member key `acme restoration`, then submit a PRESENT name `Zed Services` with eligible evidence.
- **Observed:** Both submissions are accepted and canonicalized. The immutable member key remains A / `acme restoration`, while its answer names B / `zed services`.
- **Impact:** Two different member slots can carry the same accepted member value, and a version addressed to A can describe B. Resolution still returns the old immutable key, so deduplication and per-member temporal close semantics no longer describe the stored answer. This affects the core S0002 member identity requirement and production `sys` name members; it does not depend on adding future ontology predicates.
- **Reproduction:** `artifacts/code-member-identity-repro.txt` records direct execution of the actual resolver and answer policy using the repository's in-memory `FactSlotStore` fake. `artifacts/code-member-identity-repro.py` preserves the source. No database or product file was mutated.
- **Existing test gap:** `engine/tests/integration/test_factslot_answers.py:382`–`:399` creates a member for a fresh insured entity, commits a different entity (`w.subject`) to it, and explicitly expects HTTP 201. The test encodes the defect instead of exercising member identity consistency. High aggregate line coverage cannot establish this invariant.
- **Remediation:** When a PRESENT answer targets a MEMBER slot, derive its member key with the slot's pinned predicate contract and require equality with `StoredSlot.member_key` before the commit writes. Define a named rejection and add negative tests for entity references, names and identifier/value-derived members; preserve positive tests for differently formatted values whose canonical key is equal. A changed member value must resolve/use its own member slot. Owner: Backend Developer + Architect (rejection contract) + QE (test correction). Fix before renewed feature closeout.

## Review dimensions

| Dimension | Assessment |
|---|---|
| Correctness | Critical member/answer identity inconsistency confirmed. Decimal round-trip and migration NULL checks are independently owned by the Architect lane; exponent allocation is owned by Security. |
| Clean architecture | Domain remains pure; application ports and persistence adapters follow SOLUTION-PATTERNS. Temporal integration adds a protocol rather than an outward package dependency. |
| SOLID / boundaries | No additional blocking finding in inspected services. |
| Test quality / coverage | Existing entity-member acceptance test asserts corrupt semantics; add negative invariant tests. Primary QE owns full AC disposition and raw coverage reconciliation. |
| Error handling | Named reason mapping is present, but the missing member mismatch guard has no rejection outcome. |
| Performance | Name hook performs per-slot authorization; already disclosed as a design handoff to F0017/F0023. No new finding here. |
| Readability / naming | New application source passes the framework code-quality scan: no TODO/FIXME, overlong lines or oversized files. |
| AC mapping | This lane directly challenges S0002 AC3 and S0005 member identity. It does not substitute for primary PM/QE's 39-AC matrix. |
| Over/under-engineering | No additional actionable finding. |

## Validation and routing evidence

- `artifacts/code-quality.txt`: PASS.
- `artifacts/code-member-identity-repro.txt`: confirmed mismatched entity and system-name members accepted.
- `artifacts/code-diff-impact.txt`: read-only KG impact output; affected nodes: assertion-eligibility-guards, backup-and-restore, bitemporal-canonical-commit, durable-authorization-decisions, factslot-identity-resolution, runtime-roots-and-toolchain, typed-fact-answer, versioned-assertion-semantics, fact-slot-qualifier, f0007-factslot-identity migration.
- `artifacts/code-risk.txt`: factslot-identity-resolution risk score 3, routine band; bus-factor guidance asks for primary owner acknowledgement. Owner identity is the original PR author; this routing signal is not a new integrity defect.
- Primary auditor runs required closeout/KG/template/tracker validators and fresh unit baseline. This lane does not claim a fresh PostgreSQL suite run.

## Self-review

Rechecked the code location, contract and test lines. The reproduction uses an authorized owner tuple and eligible name evidence, so the result is not a missing-authorization artifact. It calls the same answer policy wired in HTTP commits (`brain_api/routes/facts.py:122`–`:123`). The finding does not assume that every relationship answer must equal `object_entity_id`; relationship contracts may define a separate value type.
