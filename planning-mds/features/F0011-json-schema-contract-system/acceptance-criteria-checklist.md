# F0011 — Acceptance criteria checklist

Phase A draft, plan run `2026-11-20-ccb1bd39`. Every AC is defined in its owning
story; this index does not duplicate or override that definition.

| Story | Criteria | Count | Required observed proof | State |
|-------|----------|-------|-------------------------|-------|
| F0011-S0001 | AC1–AC7 | 7 | Resolve versioned offline contracts | Not Started |
| F0011-S0002 | AC1–AC7 | 7 | Validate information state and scoped absence | Not Started |
| F0011-S0003 | AC1–AC7 | 7 | Validate qualified money and scoped identifiers | Not Started |
| F0011-S0004 | AC1–AC7 | 7 | Prove cross-language contract conformance | Not Started |
| F0011-S0005 | AC1–AC7 | 7 | Preserve existing consumer contracts | Not Started |
| F0011-S0006 | AC1–AC6 | 6 | Verify reproducible contract delivery | Not Started |

**Total:** 41 numbered acceptance criteria; 0 implemented/verified in this plan.

- [ ] Versioned bundle and supported subset/reference/annotation policy complete.
- [ ] All nine information states and scoped-absence failures exercised.
- [ ] Exact money and scoped identifiers retain precision and namespace.
- [ ] Python/Pydantic/AJV run every shared case; OpenAPI resolves the same definitions.
- [ ] Actual consumer integration, historical compatibility and denied/refused paths pass.
- [ ] Clean-package reproduction and intentional drift failure verified in CI.
- [ ] Feature-run evidence maps all 41 ACs to observed results with at least 80% changed executable-line coverage.
- [ ] Required independent signoff provenance is appended to STATUS.md.

Semantic worked/boundary references: [EX-GL-001](../../examples/neurosymbolic-gl/README.md),
[EX-OWN-002/003](../../examples/source-authority-and-information-state.md),
and [information-state/value glossary](../../domain/glossary.md#requirement-ownership-decisions-2026-11-08-proposed).
Phase B binds exact schemas/cases and keeps structural, domain and access outcomes distinct.
