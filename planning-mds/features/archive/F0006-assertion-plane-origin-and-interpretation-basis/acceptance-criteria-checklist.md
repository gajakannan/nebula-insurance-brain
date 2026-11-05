# F0006 acceptance criteria checklist

**Status:** Done — all 35 ACs verified in feature run `2026-11-02-5a00b0ff`; archived 2026-11-05
**Total:** 35 acceptance criteria across five completed stories. Checkboxes indicate observed implementation evidence, not planning completeness.

| Story | Criteria | Observed evidence in the feature run | State |
|---|---|---|---|
| S0001 | AC1–AC7 (7) | PostgreSQL typed-claim round trips, conflicting claims, independent enums/confidence, ownership rejection and additive correction | Done |
| S0002 | AC1–AC7 (7) | Open-statement round trip, kind invariants, legacy/new schema validation, unsupported-reader rejection and scoped refs | Done |
| S0003 | AC1–AC8 (8) | Each ADR-0065 reason/signal, normalization/source mapping, four-format server selectors, truncated and unparsed outcomes, semantic-review boundary | Done |
| S0004 | AC1–AC6 (6) | Mood fixtures, operative-policy boundary, described/OCR/transcribed/legacy origin cases and independent eligibility guards | Done |
| S0005 | AC1–AC7 (7) | Existing import/replay/review/commit integration, legacy migration, atomic rollback/retry, unauthorized attempts and independently authored examples | Done |

- [x] Every story criterion has an observed test/result reference in the feature action's evidence package.
- [x] Changed-code coverage is at least 80%; real PostgreSQL and current consumer paths are exercised.
- [x] Rejected claims and ineligible canonical attempts have zero prohibited effects.
- [x] Original claims, correction history and legacy provenance survive.
- [x] Existing defaults and permission grants remain as specified in the PRD.
- [x] Future F0016/F0018/F0022/F0066 obligations are not reported as delivered by F0006.

Requirements review occurs at plan G3; architecture review and KG exit checks occur at G5. Neither review supplies runtime acceptance evidence.

Observed per-AC test references: [test-execution-report.md](../../../operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md). Changed-code coverage is 1170/1266 (92.4171%); 336 unique final product cases pass. Planning examples remain illustrative, distinct from runtime proof. SEC-01 limits approval to trusted local synthetic fixtures and carries preproduction remediation/isolation obligations.
