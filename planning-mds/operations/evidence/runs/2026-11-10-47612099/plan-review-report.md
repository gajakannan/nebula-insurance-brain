# F0007 Plan Review — 2026-11-10-47612099

## Decision

**READY** (`gate_policy.py --profile review-family --variant plan`: 0 Critical, 0 High). The plan as amended in the working tree states the identity, member-value, decimal-bound and read-authorization rules precisely enough to build from. Scope is PLAN_SCOPE=feature, TARGET=F0007, read against the working tree on `fix/f0007-review-remediation`.

## Findings By Severity

### PR-M1 — Medium — Consequential ADRs remain Proposed while the feature is Done and depended on
- **Evidence:** `architecture/decisions/ADR-0077-*.md`, `ADR-0039-*.md` and `ADR-0066-*.md` all have `- [x] Proposed` under Status. ADR-0077:188 adds the remediation rules as a trailing note "without accepting the Proposed ADR" instead of updating decisions D4/D5. ROADMAP:126 and STATUS:169 acknowledge this.
- **Impact:** F0008, F0013 and F0017 list F0007 as a prerequisite, so they would plan against a decision record that is not authoritative and whose body does not yet contain the member-value or 64-character rules.
- **Owner:** Architect proposes, operator decides. Accept ADR-0077 and fold the 188 note into D4/D5, or record why it stays Proposed, before F0008 Phase B.

### PR-L1 — Low — Story S0002 AC3 does not state the member-value rule it now tests
- **Evidence:** `F0007-S0002-*.md:24` derives member identity from the value but never says a later PRESENT answer must match it. The rule and `MEMBER_VALUE_MISMATCH` appear only in `feature-assembly-plan.md:287`, the ADR-0077:188 note and `brain-api.yaml:296`.
- **Owner:** PM. Add one sentence to AC3 on the next touch. Not blocking.

## Product Readiness
- Six stories with specific, testable ACs (validate-stories passes). Each story has a written "No screen" justification. Non-goals and the downstream owners (F0008, F0012/F0013, F0016/F0017, F0018) are explicit.
- The entry documents (README, PRD, STATUS) agree with REGISTRY and ROADMAP.

## Architecture Readiness
- `feature-assembly-plan.md:186-205` now specifies the identity CHECK as `(...) IS TRUE` and adds the immutable-0012 → 0013 lineage (lines 345-350, 420).
- Line 287 specifies the member-value rejection with zero writes.
- The schema `fact-slot-key-v1.schema.json:109,179` and the ADR note align on the 64-character decimal bound.
- `brain-api.yaml` lists the new reason code.
- KG validate and drift pass.

## Buildability Challenge
- Each repair names an owning role and a concrete proof (direct-SQL NULL negatives, canonical round-trip boundaries, a revocation interleaving), and the delivered tests match them.
- Risk hotspot: `AuthorizationExecution.read` is shared security infrastructure. The plan correctly scopes the change to an optional `additional_reads` that mirrors `mutate`.

## Validation Evidence
PR2 via `run-gate.py --action plan-review --stage PR2`: `check-plan-approvals`, `validate-stories`, `validate-trackers`, KG validate, KG `--check-drift`, `validate_templates` and the project checks all exit 0 (lifecycle-gates.log).

## Artifact Trace
- Archived `F0007-factslot-model/**`
- ADR-0077, ADR-0039 and ADR-0066
- `schemas/fact-slot-key-v1.schema.json`
- `api/brain-api.yaml`
- REGISTRY and ROADMAP
- plan approval history (via check-plan-approvals)
