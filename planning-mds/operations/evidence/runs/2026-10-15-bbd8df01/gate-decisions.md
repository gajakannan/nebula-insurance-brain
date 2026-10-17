# Gate Decisions — F0004 — plan run 2026-10-15-bbd8df01

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-10-16T01:07:41.849101+00:00 | PRD and four stories resolve requirements against existing scope; strict story validation exits 0. No open business question; Phase B design duties are explicit. | No | Proceed to G2 |
| G2 | PASS | Product Manager | 2026-10-16T01:07:56.059129+00:00 | Generated story index and BLUEPRINT links include four F0004 stories; tracker validator reports 0 errors/0 warnings. Dependencies audited by exact manifest references; Planned/Next preserved. | No | Present requirements at G3 |
| G3 | PASS | Operator; recorded by Product Manager | 2026-10-16T01:10:35.417590+00:00 | Explicit operator approval: “proceed with Phase B”; checkpoint approve-phase-a. | No | Attest and complete G3, then begin architecture |
| G4 | PASS | Architect | 2026-10-16T11:47:16.230769+00:00 | kg-source feature/node shards compiled; drift check exited 0 on the first attempt. No canonical conflict or repair cycle. | No | G5 exit validation |
| G5 validation | PASS | Architect | 2026-10-16T11:47:16.230769+00:00 | All seven required commands exited 0 in the specified order; drift and reproducibility passed. | No | Manual architecture review |
| G5 approval | PASS | Operator; recorded by Architect | 2026-10-16T12:16:31.667275+00:00 | Explicit user token: approve-phase-b, after all exit validation passed. Approval status synchronized and G4/G5 validations passed again. | No | Complete attestation and close plan |

Both Phase A and Phase B were explicitly approved by the operator. Template example pass rows were removed; they were not evidence for this run.

## Requirements Clarification Basis

- Follow the supplied Plan A+B contract; F0004 had only a reserved README, no completed plan to review independently.
- Accepted ADR-0040/0059 retain native six-file content, hash verification and manifest-last publication. Source/parse/run identities stay separate.
- Amended ADR-0058 supplies the bounded PDF/BoxSelector contract; deferred multi-format/W3C proofs are not introduced as requirements.
- BLUEPRINT §4.11 and the F0004 README authorize document-date provenance and text-origin storage/contract hooks. ADR-0060/0064/0065 stay Proposed; no new engine, calendar resolver, automated decider or review UI is authorized.
- Unknown dates/origins are not fabricated. Conflicting dates remain attributable; no new automatic precedence rule is invented.
- Physical schema, missing-anchor representation, service bindings and compatibility/error contracts are Phase B design obligations. No unanswered business question remains in the bounded draft.

## Ownership and Reconciliation

The operator's strict ownership overrides older PM guidance that permits feature-shard edits. PM leaves KG sources and generated projections untouched in Phase A. The existing reservation carries path, planned status, dependencies and governing ADRs; the architect must remove its pre-plan coverage exclusion and supply actual bindings at G4. No assembly plan exists to overwrite. ADR-0060's newer candidate evidence is distinguished from F0001's historical direct-client proof in the PRD.

## Approval Tokens

Phase A checkpoint token: `approve-phase-a`. Operator wording: **“proceed with Phase B”** (explicit authorization to advance after the Phase A review). Recorded by Product Manager at 2026-10-16T01:10:35.417590+00:00. This normalizes the operator’s affirmative instruction to the checkpoint identifier; it does not claim the operator typed that identifier. Phase B checkpoint token and exact operator wording: **`approve-phase-b`**. Recorded by Architect at 2026-10-16T12:16:31.667275+00:00, after the original seven G5 validators were green and the approval metadata revalidation passed.

## Phase A Verification Notes

Strict story validation initially identified audit criteria outside the AC lists for S0001/S0002. Explicit audit ACs were added; the recheck passed. The remaining nonblocking INVEST dependency advisory on S0001 reflects declared foundation/consumer dependencies; its own publication/readback outcome is testable without downstream production activation.

Story index regeneration found 31 total stories, including four new F0004 stories. Tracker validation passed with zero errors and zero warnings using --skip-feature-evidence. Local feature links and git diff --check also passed.

## Phase B Reconciliation and Judgment

- No previous F0004 assembly plan existed. ADR-0073 is Proposed and refines approved requirements without accepting the wider ADR-0060/0064/0065 scopes. Preserved accepted ADR-0040/0058-as-amended/0059 and F0002 authorization contracts.
- Retained strict v1 reads and historical identities. Corrected the published legacy schema's filename inventory to admit observed source.pdf. New metadata is versioned v2 rather than inserted into old bytes. Governed replacement is modeled; no corpus migration executor is delivered.
- Unified verifier design extends the actual sync/async stores and the existing before-extraction metadata registrar. Queue publish_transaction already takes its generation fence before callbacks; the plan follows job → authority → source/version → artifact lock order and closes preflight transactions first.
- Date provenance separates the semantic authorization decision UUID from audit_event.id. CONTENT references exact JSONL ordinal/hash so legacy repeated block IDs remain unambiguous. Trusted metadata/human verifiers own source authority; default absent adapters fail closed. No new public writes or permission grants.
- Only Architect-authored kg-source shards feed generated projections. Removed the F0004 reservation exclusion, mapped all four stories, added two capabilities and five entity definitions, and bound the proposed ADR/contracts. No future code path is claimed as as-built.
- Direct dependencies remain F0001/F0002/F0003; F0005 and downstream consumer evidence limits remain in artifact-trace.md. No repo-wide feature-evidence audit substituted for dependency review.

## Phase B Validation and Limits

G4 compiled and checked drift successfully. G5 completed validate-stories, generate-story-index, validate-trackers --skip-feature-evidence, KG coverage generation, drift, reproducibility and validate_templates, in that order, all exit 0. The runner reached its manual checkpoint after these successful commands; the operator subsequently supplied the explicit approval token recorded above. Severity profile none computes PASS; it does not waive architecture approval.

Supplemental structural readiness passed with no findings. Six schemas and 39 synthetic cases passed (18 accepted, 21 rejected). OpenAPI validation passed with six nonblocking generic warnings: three on public health errors, two requesting 403 on content routes (the product requires 404 non-disclosure), and one existing review-decision 201 suggestion. These do not justify changing the product's accepted authorization semantics. The first OpenAPI invocation lacked the explicit product-root flag and failed before validation; the corrected rooted invocation passed. Both outputs are retained.

Planning examples do not prove real byte hashes, per-item parser provenance, DB constraints/locking, trusted authority, migrations or restore behavior. Those are mandatory feature-action proofs with 80% changed-runtime coverage and all five reviewer roles. ADR-0073 remains Proposed until those proofs pass; Phase B approval authorizes the design for build, not runtime delivery or production activation.

Final package hygiene: 135 local links across 17 feature/run/ADR documents resolve; git diff --check exits 0. All authored changes remain under planning-mds. No runtime migration or implementation test was run.

## Approval Closeout

The operator supplied exact token `approve-phase-b`. Approval annotations only were updated; design and requirements were unchanged. Architect updated the F0004 source shard and regenerated through G4 (--force); drift passed. G5 was explicitly replayed with --force --from validate-stories, and all seven exit operations passed again before this approval record was finalized. The earlier non-force resume merely returned the existing pending checkpoint; it is not claimed as revalidation. Record this file as the G5 checkpoint evidence and finish the existing run. Implementation, runtime proof, role signoffs and production activation remain outside this plan action.
