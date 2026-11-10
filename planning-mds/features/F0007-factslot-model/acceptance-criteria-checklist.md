# F0007 acceptance criteria checklist

**Status:** Planned. Requirements are drafted in plan run `2026-11-09-60865e32`, and no criterion has runtime evidence yet.
**Total:** 39 acceptance criteria across six stories. A checkbox records observed implementation evidence, not planning completeness.

| Story | Criteria | Required runtime evidence in the feature run | State |
|---|---|---|---|
| S0001 | AC1–AC7 (7) | Concurrent resolve-or-create on PostgreSQL, qualifier-order and normalization fixtures, collision and omitted/null rules, cross-KB denial, predicate-key rejection, creation audit | Not Started |
| S0002 | AC1–AC6 (6) | Cardinality conflict, pilot ADR-0008 regression, two-insureds member identity, out-of-scope relationship object, named rejections | Not Started |
| S0003 | AC1–AC7 (7) | All nine carrier states, state/value mismatch, scope required and scope ownership, unread slot reads `NOT_PROCESSED`, EX-OWN-003 round trip, T-08 non-disclosure | Not Started |
| S0004 | AC1–AC7 (7) | Float/currency/basis rejections, decimal equality and precision round trips, converted-money rejection, two-carrier policy number, FEIN normalization | Not Started |
| S0005 | AC1–AC5 (5) | Name predicate cardinalities, EX-SEM-008 same-slot rename, evidence reference required, cross-KB trade-name negative, precedence-free display hook | Not Started |
| S0006 | AC1–AC7 (7) | Pilot before/after snapshot, legacy label without fabrication, pilot regression suites, composite-key and trigger negatives, RLS inventory, up/down/up cycle | Not Started |

- [ ] Every story criterion has an observed test/result reference in the feature action's evidence package.
- [ ] Changed-code coverage is at least 80%, and real PostgreSQL paths are exercised.
- [ ] Rejected identities, carriers and values have zero prohibited rows.
- [ ] Pilot slots, fact versions and evidence are unchanged.
- [ ] Existing permission grants and routes remain as specified in the PRD.
- [ ] Obligations owned by F0008, F0011, F0016, F0017 and F0018 are not reported as delivered by F0007.

Requirements review happens at plan G3 and architecture review with KG exit checks at G5. Neither review supplies runtime acceptance evidence.
