# Backend Developer fix report

The Account 360 query now selects ownership independently and enriches owned rows with optional current insured roles. Its named-on branch excludes owned policies, preserving the normal four rows without double listing ownership. Missing and expired roles do not manufacture insured status.

The illustrative ontology adds accountStatus as a STATE fact. Four current-account assertions carry source evidence and review/commit lineage. SHACL requires a known single status and rejects two CURRENT accounts for one organization, while allowing a CLOSED account alongside its replacement. The snapshot builder remains unchanged; generated Turtle, JSON-LD and lineage index were rebuilt from authored records, and release digests refreshed. Existing negative fixtures gained explicit status so their original constraints remain exercised.

The design handoff, glossary, worked/boundary cases and authored KG notes/bindings were aligned under the Architect role. No production runtime, feature folder or sibling contract changes were made. Verification: 12 focused regressions and all 63 validation tests pass; strict RDF expectations pass. Final broader checks are in quality-report.md.
