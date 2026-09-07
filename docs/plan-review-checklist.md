# Brain plan review checklist

These are product review criteria for `plan-review`. The script validates the structure and source references in this checklist and the target planning package. Reviewers judge whether the referenced plan addresses the criteria adequately; a script pass does not mean approval or regulatory compliance.

For each target, record each applicable rule's outcome and a feature-specific planning evidence reference in the review report. If a rule does not apply, record the reason explicitly. The governing references below orient the reviewer; they do not assert that every target already satisfies each rule.

| Rule ID | Owner | Criterion | Governing source | Planning evidence to inspect |
|---|---|---|---|---|
| BRAIN-SCOPE | product-manager | Requirements, exclusions, and acceptance criteria are explicit. | planning-mds/BLUEPRINT.md | Target PRD.md and story acceptance criteria |
| BRAIN-AUTHORITY | architect | Accepted requirements and proposed decisions remain distinguishable. | planning-mds/architecture/master-blueprint.md | Target dependencies, design decisions, and referenced ADR status |
| BRAIN-EVIDENCE | architect | Assertion and canonical fact authority are tied to evidence or derivation lineage. | planning-mds/architecture/decisions/ADR-0010-provenance-is-mandatory.md | Target data requirements and proof/evidence plan; or an explicit scope exclusion |
| BRAIN-PARSE-ONCE | architect | Reinterpretation preserves the accepted content artifact. | planning-mds/architecture/decisions/ADR-0003-one-time-content-extraction.md | Target ingestion/interpretation requirements; or an explicit scope exclusion |
| BRAIN-TEMPORAL | architect | Changes preserve the valid-time and recorded-time contract. | planning-mds/architecture/decisions/ADR-0007-full-bitemporality.md | Target persistence requirements and planned tests; or an explicit scope exclusion |
| BRAIN-AUTHORIZATION | security | Protected reads and writes establish identity and enforce resource scope. | planning-mds/security/authorization-review.md | Target permission requirements and negative test plan; or an explicit scope exclusion |
| BRAIN-BUILDABILITY | code-reviewer | Ownership, prerequisites, interfaces, and planned validation let implementation begin without invented rules. | planning-mds/features/TRACKER-GOVERNANCE.md | Target stories, dependencies, planning artifacts, and required signoff roles |
| BRAIN-EXAMPLES | architect | Each introduced/changed semantic concept has a definition, worked example, boundary example, and owning feature/story/contract links; structured examples validate, phases/provenance are labeled, and runtime reproduction/holdout separation are planned. | planning-mds/examples/README.md | Target example coverage, schema/reference checks, story acceptance, and actual reproduction evidence when implemented; or an explicit no-semantic-change rationale |

## Evidence boundary

Required planning artifacts must exist and contain substantive sections. Runtime paths explicitly described as future deliverables are allowed to be absent. Do not require completed runtime proof results merely to review the plan for conducting those proofs.

Record review findings in the action's base evidence package. Preserve its normal PR0–PR4 ownership and readiness rules. A failing required local check blocks completion; a passing check supplies validation evidence for reviewer judgment.
