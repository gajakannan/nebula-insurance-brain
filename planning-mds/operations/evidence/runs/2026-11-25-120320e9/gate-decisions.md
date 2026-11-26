# Gate Decisions — F0012 plan 2026-11-25-120320e9

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Action plan, PHASE=A+B, FEATURE_MODE=new, contract 2026-07-11, severity profile none.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-11-26T00:45:58+00:00 | Eight scope questions answered by the operator (D1–D8); seven stories/46 testable ACs; remaining items are PM assumptions A1–A5 or explicit Phase B technical decisions | No | Operator reviews A1–A5 at G3 |
| G2 | PASS | Product Manager | 2026-11-26T00:45:58+00:00 | STORY-INDEX regenerated (73 stories); strict story validation (7/7, zero warnings) and validate-trackers --skip-feature-evidence (0 errors, 0 warnings) pass; dependency audit recorded in artifact-trace.md | No | Architect completes KG source bindings at G4 |

## G1 operator clarification decisions (2026-11-25)

The operator answered eight questions in the current conversation, each with the recommended option.

| ID | Question | Decision |
|---|---|---|
| D1 | Delivery depth | YAML modules, deterministic offline compile/validate to a hashed release manifest, immutable module/release records in PostgreSQL with audited activation, PredicateContractRegistry served from the installed release |
| D2 | ADR-0070 module boundary | F0012: §22 base classes plus Party/Organization/Person, location, employment, organization hierarchy, Account, designated parent, ownership interest, role assignment. F0013: Policy, PolicyTerm, Submission, Program and policy/program-to-account links |
| D3 | Supported semantics | Inference: subClassOf, subPropertyOf, inverseOf. Validation-only: domain, range, disjoint, min/maxCardinality with execution context. symmetric/transitive rejected as unsupported |
| D4 | Namespace | `urn:nebula:ont:<dotted-id>`; `urn:nebula:tenant:<tenant_id>:ont:<dotted-id>` reserved for tenant extensions |
| D5 | Tenant extensions | Rules and rejection only; no install path |
| D6 | temporal_kind | Declared on every property; ETERNAL/EVENT activated for registered predicates over ADR-0078 D10 shapes, no DDL |
| D7 | Impact gate | Full predecessor-to-candidate report plus gated activation; no-producer populations reported as unexamined |
| D8 | Authoring shape | `parents:` (0..n) canonical; singular `parent:` rejected with a migration hint |

## Requirements reconciliation

1. Master blueprint §20 `parents:` vs §82 `parent:`: resolved by D8 (S0001 AC2). The §82 example remains illustrative; no authored module exists to migrate.
2. ADR-0070 proof gate 2 lists Cedar Bridge cases that need policy terms. Under D2, F0012 proves EX-PC-001/011/015/017 (account-scoped rows)/021; EX-PC-016/018/019/020 move to F0013 (PRD A4). ADR-0070 stays Proposed.
3. ADR-0070 says "F0012/F0017 must enforce" the tenant-wide one-current-account invariant at canonical admission. PRD A2 assigns declaration to F0012 and runtime admission enforcement to F0017/F0018; the operator confirms or amends at G3.
4. The ontology handoff suggested FEATURE_MODE=existing for the reserved folder; the operator prompt selected new. Only README.md existed; its dated amendments are preserved and extended.
5. ADR-0045 remains Proposed; F0012 owns its identity/locks, inference-change, constraint-change, split/rollback and scope evidence cases (S0007 AC1). The missing-limit case stays with F0013/F0065.

## Dependency audit

See artifact-trace.md: F0011 (direct) and F0002/F0007/F0008 (kernel carry-ins) approved manifests read; downstream consumer integration evidence is audit pending. No repo-wide feature-evidence validation.

## Pending checkpoint (superseded by the approval below)

G3 required the operator's explicit approval of the PRD, personas, seven stories/46 ACs and assumptions A1–A5. Suggested token: `approve-phase-a`. After the response: record the exact token/actor/time here, make Phase A approval-status edits, attest `approve-phase-a` as product-manager, and rerun G3. Do not attest before the response.

## G3 explicit Phase A approval

- Stage: G3
- Checkpoint: approve-phase-a
- Approval token: `approve-phase-a`
- Actor: user (operator)
- Recorded at: 2026-11-26T00:56:21+00:00
- Scope: F0012 Phase A requirements — PRD, personas, seven stories / 46 ACs, G1 decisions D1–D8 and PM assumptions A1–A5 as written (A2: F0012 declares the account invariants; F0017/F0018 enforce at admission). Run 2026-11-25-120320e9.
- Decision: APPROVED. Phase A approval-status edits (PRD, STATUS, README, BLUEPRINT §3.3) were made before attestation. Architecture proceeds in this A+B run; the manifest stays draft until G5 publication.

## Architecture gates and reconciliation

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G3 | PASS | Operator / Product Manager | 2026-11-26T01:05:10+00:00 | Exact user token approve-phase-a recorded and attested; approve-plan Phase A operation passed in the A+B run | No | Manifest stays draft until G5 |
| G4 | PASS | Architect | 2026-11-26T01:05:10+00:00 | kg-source shards (F0012 feature shard, adr:0081, three schemas, two capabilities, three entity notes) compiled; validate --check-drift passed on the first attempt through run-gate.py | No | Ordered G5 exit validation and explicit Phase B review |

Phase B reconciliation:

1. ADR-0070 lists `PartyRoleTypeCode` as the external reference. nebula-insurance-data-contracts today defines NAMED_INSURED, BROKER_OF_RECORD and ADDITIONAL_INSURED only; FIRST/ADDITIONAL_NAMED_INSURED and other codes are proposed in the cross-repo plan. The foundation design records each code as `existing`, `proposed` or `unmapped`, which satisfies S0003 AC3 without claiming proposed codes exist.
2. ADR-0081 D5 introduces the `ontology_release` resource and a new `OntologySteward` role. This is the one new authorization surface; Phase B review should confirm or replace it. Policy rows and policy_rule KG nodes are added by the feature run together (drift check), not by this plan.
3. No earlier assembly plan existed; nothing was overwritten. FEATURE_MODE=new is consistent.
4. `migration-design.sql` could not be machine-parsed at plan: pglast is not installed locally and fetching it was denied by the session permission policy. The feature run's real migration on PostgreSQL 18 is the proof; G0 re-reviews the DDL.
5. All three design schemas pass Draft 2020-12 `check_schema`; `foundation-module-design.yaml` validates against the authoring schema with zero errors (53 terms, 15 unique predicates, 7 constraints, every property projected or omitted).

## G5 pre-approval exit validation — PASS

The gate journal records these operations in order, each exit 0: validate-stories, generate-story-index, validate-trackers (skip-feature-evidence), kg-write-coverage, kg-check-drift-exit, kg-check-reproducible, validate-templates (`artifacts/gate-g5-exit-validation.log`).

## G5 explicit Phase B architecture approval

- Stage: G5
- Checkpoint: approve-phase-b
- Approval token: `approve-phase-b`
- Actor: user (operator)
- Recorded at: 2026-11-26T01:08:48+00:00
- Decision: APPROVED for the Phase B architecture of F0012, run 2026-11-25-120320e9.
- Scope: seven-step assembly plan; ADR-0081 including the new `ontology_release` resource and `OntologySteward` role; foundation module design; migration 0017 design; three design schemas; KG bindings; all 46 approved ACs.
- Prerequisite: all seven ordered pre-approval G5 operations exited 0.
- Formal ADR status: ADR-0045, ADR-0070 and ADR-0081 remain Proposed; this token approves the plan, not runtime proof or ADR acceptance.
- Approval-status edits (PRD, STATUS, README, assembly plan, ADR-0081 plan-approval line, BLUEPRINT §3.3/§4.19, F0012 kg-source note) were made before attestation. G5 is rerun for post-approval compile, coverage, reproducibility, plain validation, tracker validation and approve-plan.py publication last. No planning edit follows.
