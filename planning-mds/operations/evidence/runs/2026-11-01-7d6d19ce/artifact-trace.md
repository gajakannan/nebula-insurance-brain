# Artifact Trace — F0006 / 2026-11-01-7d6d19ce

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Authority and Retrieval

Framework action/spec and Product Manager skill establish procedure. Product instructions and BLUEPRINT establish scope; raw feature/ADR/schema/source artifacts establish details. KG routing is non-authoritative. F0006 lookup returns an excluded/reserved stub and related F0065 consumer; Assertion definition lookup routes to brain-persistence models.py. Its callers index is empty, which is not evidence of no consumers. Phase B must inspect actual call sites. No automatic tier expansion beyond the allowed retrieval policy was requested.

| Input | Use |
|---|---|
| F0006 README dated 2026-09-25 amendment; BLUEPRINT §4.11 | Authorized storage/checks/hooks scope and guard against behavioural expansion |
| Master blueprint §§11,17,28; ADR-0005/0035 | Claim/truth separation, orthogonal dimensions and run/evidence linkage |
| ADR-0063 accepted direction; ADR-0065 Proposed | Open/typed representation, structural admission and mood; broader proof not claimed |
| schemas/interpretation-result.schema.json | Existing strict legacy contract; compatible versioned addition required |
| F0005 final STATUS; ADR-0074 Accepted | Latest rejection/controls decision governs current direct-baseline/v1 defaults despite older blueprint summaries |
| F0004 delivered content/legacy provenance contract | Evidence origin inherited, never retrospectively qualified |
| Existing persona files; EX-GL-001; EX-SEM-001/005–007 | User needs and synthetic worked/boundary examples |

## Authored Outputs

Feature path: `planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/`.

PRD.md, personas.md, five F0006-S0001–S0005 story files, acceptance-criteria-checklist.md, STATUS.md skeleton, README.md index and GETTING-STARTED.md. BLUEPRINT §3.3 gains F0006 story/status links. examples/README.md gains owning story/contract routing. STORY-INDEX.md is regenerated after story creation. Registry/roadmap generated regions and kg-source shards remain untouched during PM Phase A; the reserved id/path/status stub exists and its exclusion is explicitly removed by the Architect in Phase B.

No role reports, runtime changes, feature evidence index, or assembly-plan file in the run folder are produced. Generic template sample gate results in the initial base-run scaffold are cleared; they are not evidence that feature G0 occurred.

## Dependency Evidence Audit (read-only, bounded)

For each direct delivered foundation, read its exact feature latest-run.json pointer and pointed manifest. All five manifests below have status `approved` and matching feature/run identities. This is approval-reference verification, not revalidation of archived feature packages; no validate-feature-evidence.py or repo-wide evidence audit is run.

| Dependency | Approved evidence reference (product-relative) | Scope / remaining qualification |
|---|---|---|
| F0001 | planning-mds/operations/evidence/runs/2026-09-12-855d2b93/evidence-manifest.json | Foundation and pilot consumers; current F0006 regression/compatibility audit pending implementation |
| F0002 | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/evidence-manifest.json | Principal, ownership, review/commit authorization; no new grants |
| F0003 | planning-mds/operations/evidence/runs/2026-10-03-57d14a51/evidence-manifest.json | Delivered PostgreSQL foundation; F0006 migrations not yet designed |
| F0004 | planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/evidence-manifest.json | Immutable content, text-origin storage and legacy fallback; broader qualification not assumed |
| F0005 | planning-mds/operations/evidence/runs/2026-10-25-4020923b/evidence-manifest.json | Approved rejection closeout; does not approve Graph activation; direct-baseline/v1 stay default |

Impacted/future consumers from raw requirements: F0007/F0009/F0010/F0015/F0016/F0017/F0018/F0022/F0026/F0065/F0066/F0052/F0053. KG lookup directly exposes F0065 depending on F0006. Their F0006 interface adoption and implementation evidence are audit pending; no missing future runtime is asserted delivered or made a circular prerequisite. Phase B completes canonical bindings and explicit consumer handoffs.

## Phase B Reconciliation Items

- Existing runtime uses MACHINE_EXTRACTION; master blueprint names DOCUMENT_INTERPRETATION. Preserve raw provenance and legacy readers when mapping; do not silently rewrite evidence.
- EX-SEM-005 shows case/spacing normalization beyond the ADR's short list. Architect records a deterministic normalization/source-mapping decision before approval.
- Later F0016 persists drop outcomes; F0006 must not claim full run lifecycle delivered.
- No pre-existing F0006 assembly plan exists to overwrite.

## Phase B Authored Sources and Generated Outputs

Architect source artifacts: feature-assembly-plan.md, worked-examples.md, contract-examples.json; planning-mds/architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md; schema trio assertion-record-v2 / interpretation-result-v2 / assertion-admission-result-v1; API commit 422/review compatibility documentation; data-model, glossary, blueprint §4.12, assembly index; feature README diagrams and finalized required role matrix.

KG authored sources: F0006 feature shard now removes coverage_excluded and maps S0001–S0005, delivered dependencies F0001–F0005 and approved architectural invariants; three capabilities and three storage/reference entity nodes; schema/ADR/endpoint nodes; assertion canonical source shard; f0006-planning bindings to existing design artifacts only. G4 compile generated canonical-nodes, feature-mappings, code-index and roadmap regions. No compiled projection or generated tracker region was hand-edited. Future runtime paths are proposed in the plan, not bound as delivered code.

G4 compile/drift PASS. G5 preapproval exit sequence PASS in declared order and paused at approve-phase-b; coverage-report was generated by the validator. Schema cases, product structural readiness and semantic examples PASS. API baseline comparison confirms the six convention warnings predate this change. Diff-impact shows no changed code symbols; its unresolved documentation paths/untracked-file limit are complemented by exact schema/local-link checks and authored KG mappings.

Previously deferred design choices are resolved in ADR-0075/assembly plan: explicit version dispatch, immutable extension and legacy-origin projection, normalization/source-range mapping, scope/transaction/auth callback, consumer guard lineage and staged migration/rollback. No unresolved product question is transferred silently into implementation. The required runtime proofs and current legacy pilot boundary remain explicit review points.

## Operator Phase B Approval and Final Refresh

Operator supplied approve-phase-b; recorded at 2026-11-01T21:19:51.701476+00:00. Approval metadata edits were made to authored planning files and KG shards before attestation. No compiled file was hand-edited. ADR-0065/0075 remain Proposed; no runtime, story completion or feature evidence approval is claimed. Final G5 automatically compiles projections/trackers, refreshes coverage and runs reproducibility/plain-KG/tracker checks before approve-plan.py publishes the A+B manifest last. See gate journal and manifest for the observed publication result; this file is not edited after the final refresh.
