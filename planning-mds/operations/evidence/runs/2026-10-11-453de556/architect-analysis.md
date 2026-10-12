# Architect analysis

## Scope and root cause

ADR-0070 sections 2, 3 and 6 already authorize closed-account replacement and separate policy ownership from named-insured roles. The worked query incorrectly requires a role before selecting an owner. SHACL counts eternal organization links rather than current accounts. These are example-contract defects, not a new product capability.

## Reproduction

`artifacts/test-results/reproduction.txt`: 3 failures / 2 passes. Owned GL disappears for missing and expired roles; the closed-plus-current fixture fails inverse-link cardinality. Non-owned auto correctly disappears when its role is absent. Regression tests execute the existing snapshot builder, SPARQL and SHACL.

## Design and implementation handoff

1. Union an independent policy-ownership branch (optional role enrichment) with a named-insured branch that excludes owned policies. Preserve exact normal rows; never infer first-named status from ownership.
2. Keep accountOrganization ETERNAL. Add illustrative accountStatus as a STATE string with CURRENT/CLOSED values. At a selected valid/known coordinate each admitted account must have one known lifecycle status. Count only CURRENT accounts for each organization in the single-tenant graph. Retain CLOSED accounts, their identity links and policy history.
3. Add status assertions with source evidence, review/commit references and state intervals for the four existing accounts. Regenerate projections and digests from records. No new kernel table or production field is delivered.
4. Add a conforming closed/replacement boundary and negative status/duplicate-current tests; test temporal status selection through the existing builder. Update existing account boundaries to include status so their original negative constraints remain meaningful.
5. Align ADR, data-model table, glossary, example index/cases, ontology and projection mapping. Update authored account KG notes and new fixture binding, then compile projections.

## Constraints and tradeoffs

Use the existing temporal fact mechanism instead of deleting closed-account identity/history or filtering away its organization link. CURRENT means non-closed for this teaching constraint, not a production CRM status-code enumeration. Unknown/missing status is incomplete data and does not certify uniqueness. Snapshot selection is bitemporal; runtime transactional uniqueness across tenant/KB records remains F0012/F0017 implementation work. This does not introduce account reopening/merge workflows or automatic policy reassignment. ADR-0070 stays Proposed; feature folders and sibling products remain unchanged.

## Validation plan

Focused failing tests first, then complete semantic tests, strict RDF gate, structural validation suite, project/F0001 readiness, KG drift/compilation and repository lifecycle gates. These checks concern synthetic planning examples, not runtime delivery or ADR acceptance.

## Final review

PASS. The query preserves ownership even with missing/expired role evidence and does not infer role kind. SHACL scopes uniqueness to current accounts while independently requiring complete lifecycle status. The valid/recorded-time tests retain both organization links, and the static close/reopen example retains the old policy. Source assertions carry evidence and temporal kind; projections and digests are regenerated. Final fidelity checks confirm all prior identity, run, commit, assertion, slot and fact records were preserved, with four added status assertions/slots/facts; no runtime or feature folders changed. All required checks pass as recorded in quality-report.md. Both findings are resolved within the proposed teaching scope, with no new blocking findings in this self-review.
