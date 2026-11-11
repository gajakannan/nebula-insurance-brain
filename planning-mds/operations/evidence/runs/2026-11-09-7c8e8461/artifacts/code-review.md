# F0007 Code Reviewer planning readiness audit

## Buildability Challenge

The plan names the backend packages, migration, predicate registry, canonical identity rules, source authorization, commit policy and downstream ownership clearly enough to locate the intended work. Backend, QE, Security and DevOps handoffs are inferable; no build-critical owner is missing. No UI is justified, and F0018 row security / F0008 temporal semantics and database envelope enforcement / F0017-F0023 display precedence are explicit handoffs rather than accidental omissions. The per-feature assembly plan was read as completion context; it is not required as a planning deliverable.

One concrete clarification is needed at the identity/answer boundary: ADR-0077 D4 (`:73`–`:74`) defines a MULTI member key from its value/entity and D6 (`:117`) defines a name member key from the normalized name, while D5's answer validation (`:94`) specifies generic envelope validation without stating that a PRESENT member answer must retain that member key. The implementation handoff's `Answer Validation at the Existing Commit` section lists contract/state, scope, type and value-detail checks but no member-key equality check. A competent builder needs an explicit invariant, a named mismatch rejection and negative test expectations here. The completed implementation's Critical CR-AUDIT-01 confirms the missing check is consequential; `test_factslot_answers.py:382`–`:399` even asserts success for a mismatched value.

**Readiness recommendation for this clarification:** High, Architect-owned contract detail, with Backend/QE implementation and regression ownership. The primary auditor should reconcile this with the Architect's readiness findings rather than count the same identity defect twice. There is no separate missing-owner blocker.

The original plan's malformed-row shape SQL is reviewed by the Architect lane, which owns its NULL-semantics finding. Decimal bounds and round-trip behavior are reviewed there and by Security. Required plan approval, story, tracker, KG and template validation are owned by the primary auditor.

## Evidence and limits

Direct sources read: all six story summaries/ACs consulted as needed; archived PRD and assembly-plan contract sections; ADR-0077 D1–D8; source in brain-domain, brain-factslots, brain-persistence, migration0012 and changed temporal/API integration; representative unit and PostgreSQL test source; original manifest-cited code review report. New feature-audit evidence `2026-11-09-8b8456df/artifacts/code-member-identity-repro.txt` demonstrates the consequential boundary gap. Audit notes and generated command evidence only were written; planning and completion artifacts were not repaired.
