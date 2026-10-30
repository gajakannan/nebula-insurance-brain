# Gate Decisions — F####-{slug} run {run-id}

> Required per §8. One row per gate evaluated. §17 stage matrix dictates which rows must be present at each validation stage.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G0   | PASS     | Architect | 2026-05-19T10:15:00-04:00 | Plan reconciles with PRD | No | - |
| G1   | PASS     | DevOps    | 2026-05-19T10:30:00-04:00 | Runtime preflight green | No | - |
| G2   | PASS     | QE        | 2026-05-19T11:00:00-04:00 | All AC covered, coverage ≥ target | No | - |
| G3   | PASS     | Code Reviewer | 2026-05-19T11:30:00-04:00 | No blocking findings | No | - |
| G5 | PASS     | PM        | 2026-05-19T12:00:00-04:00 | Signoff matrix complete | No | - |
| G6 | PASS     | PM        | 2026-05-19T12:15:00-04:00 | Candidate evidence validated | No | - |
| G8 | PASS     | PM        | 2026-05-19T12:30:00-04:00 | Closeout sealed | No | - |

Decisions: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`, `SKIP`. Blocking values: `Yes` / `No`.

## G1 — Clarification (PM, 2026-10-28)

Context: a fresh Phase A+B plan run re-approving F0065. The 2026-09-07 plan (`2026-09-07-38aed4ad`) completed G1–G5 with operator attestations but was never published as approved. It was retired by recorded manual retirement at operator direction (see that run's `gate-decisions.md`).

The PM re-reviewed the PRD, the six stories, the assessment contract and the assembly plan against decisions made since 2026-09-07. Requirements remain bounded and coherent. Story validation passes (one INVEST warning on S0006, accepted: worked examples depend on S0001–S0005 by design).

Operator clarification answers (2026-10-28):
1. **Explanations and lineage** are bound to the ADR-0071 answer-basis contract (S0003 record, S0005 panel).
2. **Coarse valid time** (ADR-0064) yields `UNKNOWN` with reason `valid_time_imprecise`; no endpoint is inferred (S0004).
3. **The guideline rule** stays fictional for v0.1. Real guideline authority and a domain steward are an F0026 release prerequisite.

Applied to the PRD, S0003, S0004, S0005 and `acceptance-criteria-checklist.md`. Unaffected by later decisions:
- ADR-0065 (admission happens upstream; F0065 reads accepted facts);
- ADR-0070 (applicability is per policy term and coverage);
- F0004/F0005 (F0065 has no ingestion-engine dependency).

Decision: PASS.

## G2 — Tracker sync (PM, 2026-10-28)

The story index was regenerated; story and tracker validation run with `--skip-feature-evidence`.

Dependency evidence audit: the direct prerequisites F0006–F0023 are Planned, so no dependency evidence exists yet (audit pending). The archived F0001–F0005 have approved evidence via their `latest-run.json` pointers. F0024–F0026 are downstream consumers.

Decision: PASS.

## G3 — Phase A approval (operator, 2026-10-29T22:08:35-04:00)

The operator approved Phase A ("Approve Phase A"): the PRD and six stories with the three G1 clarification additions. Approval token recorded here before checkpoint attestation.

## G4 — Ontology sync (Architect, 2026-10-29)

Phase B reconciliation (Architect role):

- **`assessment-contract.md`:**
  - a new `UNKNOWN` / `valid_time_imprecise` outcome row (ADR-0064 granularity; grade-`C` mentions);
  - a new "Answer basis (ADR-0071)" section. "Used in answer" covers the input fact versions, rule release, evidence and time basis. "Considered, not used" is listed with reason codes. The comparison makes no model call. The assessment is a semantic execution trace. Storage: inside the assessment record until the F0038 trace store exists.
- **`feature-assembly-plan.md`:** build steps 4–6 and the open decisions updated. Guideline authority is moved to an F0026 prerequisite; answer-basis storage and binding and the `valid_time_imprecise` mapping are added.
- **KG:** the F0065 feature shard gains `governed_by` `adr:0064` and `adr:0071`, plus a re-approval note.
- No change to accepted ADRs. ADR-0071's proof gates stay with F0036/F0038.

`run-gate G4`: kg-compile and kg-check-drift pass. Decision: PASS.

## G5 — Phase B approval (operator, 2026-10-29T22:10:16-04:00)

Exit validation was green: validate-stories, generate-story-index, validate-trackers, kg-write-coverage, kg-check-drift-exit, kg-check-reproducible and validate-templates.

The operator approved Phase B ("Approve Phase B"): the assessment contract and assembly plan with the ADR-0071 answer basis and ADR-0064 precision handling. Approval statuses were then set in STATUS, the PRD, the assembly plan and the F0065 shard. Approval token recorded here before attestation. The post-approval operations and `approve-plan` follow.
