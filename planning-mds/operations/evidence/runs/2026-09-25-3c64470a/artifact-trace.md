# Artifact trace — F0002 plan 2026-09-25-3c64470a

## Requirements sources

| Source | Use / authority |
|---|---|
| planning-mds/BLUEPRINT.md §§0–4 | Product process, scope, stack and ownership |
| docs/agent-instructions.md | Explicit product-root, compiled KG and semantic-example procedure |
| planning-mds/architecture/master-blueprint.md §§65–66, 110, 116–121 | Tenancy, current authority, delegation, audit and carryover matrix |
| planning-mds/architecture/decisions/ADR-0030-tenancy-is-structural.md | Accepted structural hierarchy |
| planning-mds/architecture/decisions/ADR-0049-shared-identity-and-verified-principal-boundary.md | Accepted, bounded verified identity proof |
| planning-mds/architecture/decisions/ADR-0050-native-policy-evaluation-and-resource-scope.md | Accepted, bounded policy/scope proof |
| planning-mds/architecture/decisions/ADR-0042-resource-and-derivation-authorization.md | Proposed broader resource/dependency requirements; not accepted by this plan |
| planning-mds/security/policies/policy.csv | Exact existing pilot role/action grants |
| planning-mds/domain/glossary.md; planning-mds/examples/personas/*.md | Existing vocabulary and personas, targeted profiles read |
| planning-mds/kg-source/features/F0002.yaml; F0002 KG lookup | Reserved identity, F0001 dependency and F0065 consumer routing |

## Authored Phase A outputs

In planning-mds/features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/: PRD.md, personas.md, six F0002-S#### story files, STATUS.md skeleton, acceptance-criteria-checklist.md and worked-examples.md. BLUEPRINT section 3 story links are synchronized. STORY-INDEX generation and G2 validation are recorded in commands.log when executed.

No KG source/projection, ADR, schema, API or feature assembly plan is authored in Phase A. The README-only reservation is preserved for Architect’s Phase B index update. No feature evidence package exists for F0002.

## Direct dependency evidence

- F0001 pointer: planning-mds/operations/evidence/features/F0001-repository-and-engineering-foundation/latest-run.json.
- Approved manifest: planning-mds/operations/evidence/runs/2026-09-12-855d2b93/evidence-manifest.json (status approved, inspected during this run).
- Bounded raw proof summaries: ADR-0049/0050 and archived F0001 assembly plan. Full report/test revalidation: audit pending for the implementation run, not claimed here.

## Impacted consumers

F0065 depends on F0002 in the KG. Raw blueprint-derived impact: F0003–F0017, F0018, F0020–F0023, F0026, F0033–F0040, F0047. These downstream features remain unimplemented or separately governed; dependency acceptance audit pending where relevant. Do not run repo-wide feature-evidence checks at plan.

## Phase B authored artifacts

Feature assembly plan, README ERD/component diagram, GETTING-STARTED, contract-examples.json, ADR-0061/0062, schemas/authx-kernel.schema.json and api/brain-api.yaml. Updated data-model, architecture assembly index, glossary/example coverage, BLUEPRINT 4.10 and STATUS reviewer matrix. Authored KG feature/node shards only; G4 compiles projections. Existing pilot policy files are unchanged.

Source inspection: brain_domain/principal.py; brain_security verification/principals/authorization/audit/casbin_adapter; brain_persistence models/repositories; brain_api deps and content/facts/reviews routes; brain_temporal/commit.py; brain_worker/document_delivery.py; brain_jobs/queue.py and migration 0004. These are reads, not runtime edits. Concrete findings (first-grant selection, unused classification, non-committed read audit, separate worker evaluator) drive the proposed architecture.

Dependency update: F0005 worker is a compatibility consumer identified from current source, not an accepted prerequisite or authorization to activate ADR-0060. Its separate production evidence remains audit pending.

Additional planning helper: scripts/validation/validate_authx_contract_examples.py validates declared synthetic valid/invalid examples without runtime authorization claims. G4 compiled node and feature projections; G5 refreshed coverage and verified exact reproducibility. No code bindings to nonexistent runtime paths were introduced.

## Approved planning handoff

User explicitly approved Phase B with `approve-phase-b` on 2026-09-25. Approval metadata and the F0002 source shard were synchronized, projections recompiled, and all seven G5 automated checks passed again before attestation. G1–G5 are completed in gate-state.json; manifest status is approved for this base plan run only. Removed initializer template references to a nonexistent feature G0 report and replaced them with the actual plan gate journal. Runtime stories and proof remain unstarted.
