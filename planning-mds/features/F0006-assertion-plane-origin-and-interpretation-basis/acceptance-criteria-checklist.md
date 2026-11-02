# F0006 acceptance criteria checklist

**Status:** Phase A+B approved 2026-11-01; runtime criteria unverified
**Total:** 35 acceptance criteria across five unstarted stories. Checkboxes indicate observed implementation evidence, not planning completeness.

| Story | Criteria | Required evidence in the future feature run | State |
|---|---|---|---|
| S0001 | AC1–AC7 (7) | PostgreSQL typed-claim round trips, conflicting claims, independent enums/confidence, ownership rejection and additive correction | Not Started |
| S0002 | AC1–AC7 (7) | Open-statement round trip, kind invariants, legacy/new schema validation, unsupported-reader rejection and scoped refs | Not Started |
| S0003 | AC1–AC8 (8) | Each ADR-0065 reason/signal, normalization/source mapping, four-format server selectors, truncated and unparsed outcomes, semantic-review boundary | Not Started |
| S0004 | AC1–AC6 (6) | Mood fixtures, operative-policy boundary, described/OCR/transcribed/legacy origin cases and independent eligibility guards | Not Started |
| S0005 | AC1–AC7 (7) | Existing import/replay/review/commit integration, legacy migration, atomic rollback/retry, unauthorized attempts and independently authored examples | Not Started |

- [ ] Every story criterion has an observed test/result reference in the feature action's evidence package.
- [ ] Changed-code coverage is at least 80%; real PostgreSQL and current consumer paths are exercised.
- [ ] Rejected claims and ineligible canonical attempts have zero prohibited effects.
- [ ] Original claims, correction history and legacy provenance survive.
- [ ] Existing defaults and permission grants remain as specified in the PRD.
- [ ] Future F0016/F0018/F0022/F0066 obligations are not reported as delivered by F0006.

Requirements review occurs at plan G3; architecture review and KG exit checks occur at G5. Neither review supplies runtime acceptance evidence.
