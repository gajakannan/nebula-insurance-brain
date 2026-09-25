# Gate decisions — F0002 plan 2026-09-25-3c64470a

## Recorded clarification decisions

| ID | Decision | Decider | Recorded at | Source |
|---|---|---|---|---|
| D1 | Product is nebula-insurance-brain; pass explicit absolute root | User | 2026-09-25T04:12:01.507859+00:00 | “it is nebula-insurance-brain” |
| D2 | Tenant-scoped entity identity, explicit KB access; references do not grant access | User | 2026-09-25T04:12:01.507859+00:00 | “Tenant-scoped identity; explicit KB access” |
| D3 | Reuse TenantMember, Reviewer, ServicePrincipal pilot roles; no new business-role grants | User | 2026-09-25T04:12:01.507859+00:00 | “Reuse the existing pilot roles” |

Timestamps are recording times, not inferred user-message timestamps. These are clarification decisions, not Phase A/B approval tokens.

## Gate evaluations

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-09-25T04:13:27.774068+00:00 | User resolved entity/KB identity and pilot roles; six stories have explicit outcomes and boundaries; run-gate G1 exit 0 | No | Architecture choices remain for Phase B |
| G2 | PASS | Product Manager | 2026-09-25T04:13:27.774068+00:00 | Story index regenerated; strict story validation exit 0; tracker validation exit 0 with zero errors/warnings; run-gate G2 exit 0 | No | Two INVEST dependency advisories reviewed as intentional sequencing |
| G3 | APPROVED | User; recorded by Product Manager | 2026-09-25T04:25:47.305919+00:00 | Explicit token `approve-phase-a` received for the reviewed Phase A package | No | Proceed to Architect Phase B after attestation |
| G4 | PASS | Architect | 2026-09-25T04:47:54.838177+00:00 | Authored shards compiled; kg-check-drift exited 0 on first attempt | No | Ontology aligned with assembly plan |
| G5 automated exit validation | PASS | Architect | 2026-09-25T04:47:54.838177+00:00 | Stories, story index, trackers, coverage, drift, reproducibility and templates all exited 0 in declared order | No | Manual approval received; see G5 approval below |

## Manual approvals

- approve-phase-a: APPROVED — explicit user token `approve-phase-a`; recorded 2026-09-25T04:25:47.305919+00:00; approver: user in this conversation.
- approve-phase-b: APPROVED — explicit user token `approve-phase-b`; recorded 2026-09-25T11:47:17.823159+00:00; approver: user in this conversation. All seven G5 exit operations passed again after approval metadata and KG regeneration, before this attestation.

## Reconciliation for Phase B

Master blueprint 116.1 calls review-to-commit wiring F0002 integration; roadmap/feature ownership gives full canonical commit to F0018 and review workflow to F0022. Phase A bounds F0002 to common authorization contracts and existing-consumer proof, retaining an independent commit check and no automatic annotation-to-truth promotion. Architect reconciliation recorded 2026-09-25: ADR-0062 and the assembly plan implement exactly that approved boundary. F0018 owns full review-to-canonical orchestration, F0022 owns review UI; F0002 integrates and proves existing authorization/audit consumers independently. PRD requirements and story ACs are unchanged; only approval metadata and architecture traceability were added.

## Dependency audit

F0001 latest-run points to 2026-09-12-855d2b93, whose manifest has status approved. Raw ADR-0049 and ADR-0050 bound the proof relied upon; broader security matrix remains open. Full dependency evidence revalidation is audit pending for implementation. F0065 is an explicit KG consumer; other impacted consumers are identified from raw blueprint scope in the PRD.

## Phase B design decisions

ADR-0061 chooses explicit registry/composite ownership migration and preserves principal/resource IDs; ADR-0062 chooses complete-grant evaluation, shared sync/async evaluation and durable read/deny/write audit. Both remain Proposed: architecture design approved by user on 2026-09-25; stated runtime proof remains pending. F0005 worker is an impacted existing consumer; its production activation is outside F0002 and audit pending.

G3 was completed with the explicit user token. Its original attested gate-decisions bytes are preserved in phase-a-gate-decisions-snapshot.md; later entries in this live ledger concern subsequent gates only. Approved Phase A artifacts were fingerprinted before metadata/architecture appendices; six story files remain unchanged.

## Additional planning validation

- Product plan-readiness: PASS, no findings.
- Semantic examples: PASS (educational schema/references, not runtime behavior).
- AuthX contract examples: PASS, 12 cases including expected invalid shapes.
- OpenAPI: PASS with five advisories: health lacks 400/401/403 by design, existing review batch receipt uses 200 rather than suggested 201, and protected file route uses non-disclosing 404 rather than 403. No warning changes the current public contract.
- Diff impact: no changed source symbols; documentation/schema paths are not symbol-indexed. Targeted blast inspection includes F0001 shared authorization nodes; F0005 worker and F0065 are independently recorded consumers. This is not a claim of zero semantic impact.
- Six approved story hashes match; feature Markdown file links pass; no F0002 feature evidence package was created.

No runtime, migration or security execution is claimed. Proposed ADRs remain Proposed; full dependency evidence revalidation and runtime signoff belong to the feature action.

## G5 approval and plan closeout

| Gate | Decision | Decider | Recorded at | Evidence |
|---|---|---|---|---|
| G5 | APPROVED | User; recorded by Architect | 2026-09-25T11:47:17.823159+00:00 | Exact user token `approve-phase-b`; seven ordered automated exit checks passed after final metadata/KG sync |

Plan A+B is approved for implementation handoff. All six stories remain Not Started. ADR-0061/0062 retain Proposed status until their runtime acceptance conditions are proven. The base-run manifest will be finalized after run-gate completes G5; no feature evidence package or runtime signoff is claimed.
