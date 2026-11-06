# G0 Assembly Plan Validation — F0006

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Reviewer: Codex / Architect
- Review date: 2026-11-03T00:04:45+00:00
- Verdict: PASS
- Scope: assembly readiness only; no runtime implementation or final signoff is claimed.

## Source and approval baseline

The existing feature-local `feature-assembly-plan.md` is the primary implementation
specification. Its A+B approval (`2026-11-01-7d6d19ce`) and correction-basis/persistence
rework approval (`2026-11-01-512e9303`) remain intact. Five local story files carry
35 ACs (7/7/8/6/7). Read alongside the PRD, README diagrams, worked examples,
SOLUTION-PATTERNS, Proposed ADR-0065/0075, and the authored v2 candidate/result and
protected admission-result schemas. Tier-1/2 lookup routes context; raw artifacts
govern. The current API documents retained v2 correction restrictions and the
non-disclosing 422 `ASSERTION_INELIGIBLE` commit refusal.

## Assembly checks

| Check | Judgment and concrete handoff |
|---|---|
| Scope split | Backend owns domain, strict adapters, additive persistence, admission, authorized write/read and current-consumer enforcement. Frontend is out of scope. AI reviews shared DTO/legacy producer compatibility without adding a producer or model call. |
| Dependency order | Capture legacy identities/defaults first; strict contracts/domain then additive persistence, pure admission/eligibility, authorized writer, existing consumer adaptations, and combined PostgreSQL/current-entry-point proof. Guard-capable readers deploy before v2 writes. |
| Integration checkpoints | Exact packaged-schema equality and strict version rejection; real migration and ownership/append-only constraints; native PDF/DOCX/XLSX/CSV selectors; authorization plus atomic rollback/replay; correction and mixed-lineage consumer bypass tests; coverage against the contract floor. |
| Ownership | Architect owns semantics/contracts and this report; backend owns engine implementation; QE owns independently authored test expectations/reports/coverage; DevOps owns preflight/deployability; code/security reviewers own their separate verdict reports; PM owns final signoff/trackers/archive/publication. |
| Migration lineage | Static AST inspection confirms sole source head `0010`, allowing the planned `0011` addition. Evidence: `artifacts/test-results/g0-migration-lineage.json`. No migration has run at G0. |
| Signoff and progress | STATUS.md retains all five required roles (QE, Code Reviewer, Security Reviewer, DevOps, Architect). Story-role cells now use the contract vocabulary; all stories remain Not Started. No implementation signoff row was added. |
| KG handoff | Appended only the intended code-binding prediction to the existing plan. Existing planned semantic nodes are reused. G7 must reconcile as-built bindings, regenerate symbol/decision layers and validate drift; path-sensitive coverage is deferred to G8. |

## Contract constraints retained for implementation

- Missing version selects strict v1; only an exact integer 2 selects v2. Reject
  all other explicit versions, duplicate JSON keys, non-finite numbers and
  unknown properties; never retry a more permissive reader. Keep automatic
  importer v1-only and preserve the original v1 schema/DTO behavior.
- Independent kind/mode/origin/basis/confidence and source words round-trip.
  Open statements have no predicate/release and remain EXPLICIT. No canonical
  entities/facts are created by claim admission.
- Server evidence comes from authorized immutable F0004 content. Model offsets
  confer no authority. `f0006-grounding-v1` maps normalized characters to original
  ranges; repeated/noncontiguous matches never invent a precise span.
- Every applicable failure/signal survives in protected outcomes. F0016 owns
  durable drops, full run adoption and time-reference production/resolution.
- Name/reference effects are atomic per accepted item; document locks and the
  scoped unique name key backstop contention. Infrastructure/auth/audit failures
  roll back the entire mutation; exact hash replay returns the original effect.
- v2 integrity is deferred, owner-scoped and append-only, including v2 correction
  children with their own extension/evidence/hashes. v2 corrections inherit basis;
  v1 corrections retain their explicitly approved legacy EXPLICIT behavior.
- Kind/mood/described/unqualified restrictions compose. Mandatory repository
  guarding runs before commit registration/range changes; v2 mixed evidence or
  correction ancestry cannot fall back to the unregistered legacy pilot branch.
- Add trusted `additional_reads` to the existing mutation authorization facade;
  source READ decisions, audits and rechecks share its UoW. Never nest a read
  facade that commits the mutation. Source denial remains 404 ahead of 422.
- Keep `direct-baseline`, v1 content publication, grants and topology unchanged.
  Once v2 rows exist, rollback retains the extension and guard-capable readers;
  destructive downgrade must refuse. Proposed ADR status is not changed by G0.

## Gate execution

Run G0 through `agents/scripts/run-gate.py --stage G0` with the recorded absolute
product root and run ID. The journal and `lifecycle-gates.log` supply the executed
validator result; this report supplies the Architect's assembly judgment. G1 is
the next gate and remains the DevOps runtime preflight responsibility.

No open G0 finding or recommendation. This pass does not substitute for the
35-AC runtime proof, G3 reviews, G4 operator decision, G5 signoff or G7/G8 checks.

### Executed gate result — 2026-11-03T00:07:47+00:00

`python3 agents/scripts/run-gate.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature --feature F0006 --run-id 2026-11-02-5a00b0ff --stage G0`
exited 0 with stage status pass and completed operation validate-g0. Manifest is
now in-progress. The initial evidence-shape omissions and VF-G0-001 scan-staging
defect were repaired and the stage rerun; no waiver or earlier effective date was
used. See gate-state.json, lifecycle-gates.log and README.md for the audit trail.
