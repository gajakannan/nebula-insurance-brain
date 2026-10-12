# Action Context

## Run Identity

- Run: 2026-10-11-453de556
- Action: defect-bugfix
- Contract version/effective date: 2026-07-11
- Mode: clean

## Inputs, assumptions and scope


- Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (explicit review paths).
- Action: `defect-bugfix`; run: `2026-10-11-453de556`.
- Lifecycle Authority = none.
- Roles: architect, backend-developer, quality-engineer, exercised sequentially by Codex.
- User authorization: apply appropriate repository roles/actions to resolve both review findings while preserving repository fidelity.
- Defect summary: ADR-0070 teaching query loses owned policies without current named-insured roles; account uniqueness rejects closed-account replacement.
- Observed: mandatory insured-role join gates ownership; inverse accountOrganization count enforces lifetime uniqueness.
- Expected: ownership independently includes policies; insured-role enrichment is optional; at most one current account per organization per tenant while closed history remains available.
- Reproduction: mutate the Cedar Bridge synthetic bundle and execute SPARQL / SHACL, then add regression tests for missing/expired roles and close/reopen boundaries.
- Affected paths: commercial-pc-account example, semantic validation tests, ADR-0070, data model, glossary, example index, relevant authored KG node and generated projection.
- Feature references: none as action inputs; F0012/F0013/F0017/F0023 remain read-only ownership context.
- ALLOW_FEATURE_PROPOSAL = false. No feature folders, completion evidence, runtime authorization, production schema, or sibling repository changes.
- Scope classification: repair the proposed teaching contract; ADR-0070 remains Proposed.
