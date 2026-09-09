# Acceptance Criteria Checklist — F0001

Applied to stories F0001-S0001 to F0001-S0007 at Phase A (2026-09-06). Items marked N/A carry the reason.

## 1) Clarity & Testability

- [x] Each criterion is specific and measurable (counts, exit codes, timestamps, HTTP statuses, or recorded values)
- [x] No vague terms
- [x] Pass/fail is unambiguous

## 2) Coverage

- [x] Happy path covered in every story
- [x] At least one error or edge case covered in every story (failed page, duplicate callback, concurrent commit, expired token, restore of a corrupted backup)
- [x] Permission behavior specified where relevant (S0004, S0006); other stories state N/A with reason
- [x] Role-based visibility is per-role exhaustive where roles exist (S0006 tenant A, tenant B, service principal)

## 3) Data Validation

- [x] Required fields enforced (artifact manifest, non-empty time ranges, webhook hash)
- [x] Formats and constraints specified (sha256, ISO timestamps with timezone, exclusion constraints)
- [x] Duplicates and conflicts handled (duplicate callbacks, concurrent commits, duplicate source notifications)

## 4) Error Handling

- [x] Error messages are actionable (named service failures, version mismatch messages)
- [x] System errors have a user-safe message (authorization denials do not disclose existence)

## 5) Navigation & Feedback

- Proof-scope Review Panel only (S0004, ADR-0057); the full shell and Document 360 are F0021 and F0022

## 6) Non-Functional Criteria

- [x] Performance expectations stated as measured baselines or bounded CI durations
- [x] Security expectations stated (verification before storage access, revocation propagation, scan classes)
- [x] Reliability expectations stated (idempotent replay, restore drill)

## 7) Audit & Timeline

- [x] Mutations name their audit records (ReviewDecision audit event, commit audit and outbox, authorization decision audit)
- N/A for S0001 and S0002: no runtime mutation of business data

## 8) Out of Scope

- [x] Explicit non-goals listed in every story
