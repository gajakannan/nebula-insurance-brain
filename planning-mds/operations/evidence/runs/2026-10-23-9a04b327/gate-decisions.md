# Gate Decisions — F0005 — plan run 2026-10-23-9a04b327

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Operator; recorded by Product Manager | 2026-10-23T23:44:40Z | Four open requirement decisions answered by the operator (scope, corpus/reviewers, v2 writer, date-candidate owner). PRD and five stories updated; strict story validation passes with no warnings. Thresholds are proposed defaults for G3 approval. | No | G2 |
| G2 | PASS | Product Manager | 2026-10-23T23:44:40Z | Story index regenerated (32 stories, S0005 added); validate-trackers --skip-feature-evidence 0 errors/0 warnings; BLUEPRINT §3.3 links resolve. Dependency evidence audit recorded in artifact-trace.md. | No | Present Phase A at G3 |
| G3 | PASS | Operator; recorded by Product Manager | 2026-10-23T23:50:13Z | Explicit operator approval token `approve-phase-a` after review of PRD, five stories, checklist and the nine proposed thresholds (thresholds approved as written). | No | Attest and complete G3; begin Phase B |
| G4 | PASS | Architect | 2026-10-23T23:54:17Z | F0005 feature shard updated (S0005 mapping, F0002/F0003 dependencies, ADR-0065/0073, versioned-content-contracts, manifest v2 schema); compile and drift check exited 0 on the first attempt. No new canonical node; no repair cycle. | No | G5 exit validation |
| G5 validation | PASS | Architect | 2026-10-23T23:54:17Z | All seven exit operations exited 0 in order (validate-stories, generate-story-index, validate-trackers, coverage report, drift, reproducibility, validate_templates). Product plan-readiness check for F0005 passed with no findings; git diff --check clean. | No | Operator architecture review |
| G5 approval | PASS | Operator; recorded by Architect | 2026-10-24T00:14:24Z | Explicit operator token `approve-phase-b` after all seven exit operations passed. Approval-status edits only; design and requirements unchanged. | No | Attest, re-run G5 post-approval operations, publish plan approval |

Template example rows were removed; they were not evidence for this run.

## Requirements Clarification Basis

F0005 had planning artifacts from 2026-09-15 to 2026-09-25 and a delivered synthetic development scope, but no plan run. Those artifacts predate F0002–F0004 delivery. FEATURE_MODE=existing: artifacts are updated in place; STATUS story provenance remains append-only (no rows existed).

Operator decisions (2026-10-23, AskUserQuestion at G1):

1. **Scope:** local qualification plus gated activation — live Phi-4-mini on vLLM on the development host GPU (RTX 5070, 12 GB), live failure injection, direct-versus-Graph comparison with thresholds; on full pass, accept ADR-0060 and make Graph the local default. Production host stays F0026.
2. **Corpus and reviewers:** synthetic GL documents with expectations authored independently of extraction output, outside the frozen holdout; QA/Architect/Security verdicts by independent agent roles; operator acceptance. No licensed real documents.
3. **v2 writer:** F0005 qualifies text origin and exact OCR asset provenance, then enables `content.v2_writer_enabled` as an activation step (new story S0005). Satisfies the 2026-09-25 A-4 activation prerequisite and F0004's closeout handoff.
4. **Date candidates:** F0016 owns CONTENT and SOURCE_METADATA candidates; F0005 produces none. Recorded in BLUEPRINT §4.8 and the F0016 README.

Proposed by the Product Manager for operator approval at G3 (not invented as business rules; labelled as defaults in the PRD): corpus minimum (12 documents: 6 native, 4 scanned, 2 mixed) and the nine qualification thresholds.

## Ownership and Reconciliation

The product manager did not edit kg-source shards or generated KG projections in Phase A. The F0005 shard needs S0005's story mapping and refreshed rationale/notes; the architect adds them at G4. ADR-0060 status is unchanged. The existing assembly plan is reconciled (not silently overwritten) in Phase B, with the reconciliation recorded here.

## Phase B Reconciliation and Judgment

- **Existing assembly plan reconciled, not overwritten.** The 2026-09-15 draft's first three steps are delivered as synthetic scope. Its open-decisions table is closed: the pin and seam by S0001, DTOs and publication by F0004, corpus/reviewers/thresholds by the operator. The new plan carries an item-by-item reconciliation table.
- **As-built facts the plan corrects for:**
  - The worker already runs Graph with the `direct` contract; the old "direct client" is only a test/benchmark baseline. Activation therefore means a pinned `extraction.pipeline` setting (`graph-direct` | `graph-dense` | `direct-baseline`) written into the job JSON payload, with a direct-baseline worker path built as the rollback.
  - `document_job_event` has no failure reason, so an expand-only migration 0009 adds a constrained nullable `reason`.
  - The v2 manifest already has `execution.model_artifact_digests` and the per-item `ProducerIdentity.model/model_version`, both written empty today. S0005 fills them, with no schema change.
- **No new endpoint, schema, role, permission or Casbin rule.** Existing ServicePrincipal `ingest`/`interpret` grants cover all qualification jobs.
- **ADR-0060 stays Proposed.** It now records the acceptance procedure and the acceptance scope (local Compose runtime only; F0026 retains production host and frozen-corpus acceptance). ADR-0073 stays Proposed. No new ADR: pipeline selection and reason codes are feature-local design inside ADR-0060's and F0003's existing decisions.
- **Reviewer independence:** a corpus-author QE session is separate from the independent QA, Architect and Security review sessions; expectations come from generator input data, not extraction output.
- **PRD/architecture conflict check:** none. The design satisfies all 33 ACs without changing the approved PRD.
- **Dependency audit:** approved F0001–F0004 manifests and pending downstream audits are in artifact-trace.md.

## Approval Tokens

Phase A checkpoint token: `approve-phase-a`, selected verbatim by the operator in response to the Phase A approval question; recorded by Product Manager at 2026-10-23T23:50:13Z. The approval covers the qualification thresholds and corpus minimum as written in the PRD.

Phase B checkpoint token: `approve-phase-b`, selected verbatim by the operator in response to the Phase B approval question after G5 exit validation was green; recorded by Architect at 2026-10-24T00:14:24Z. Approval-status edits made afterward: PRD, STATUS, README, assembly plan status lines, F0005 shard rationale, BLUEPRINT §4.8 item 4 and §6. Phase B approval authorizes the design for the feature action; it is not runtime delivery, ADR acceptance or activation.
