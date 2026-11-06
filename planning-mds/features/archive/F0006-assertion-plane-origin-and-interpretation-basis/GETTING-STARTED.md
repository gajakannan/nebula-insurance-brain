# F0006 — Getting started

**State:** Done / Archived 2026-11-05; implementation run `2026-11-02-5a00b0ff` has operator G4 approval with the SEC-01 trusted-local-fixture mitigation and all required role signoffs.

Read [PRD.md](PRD.md), [personas.md](personas.md), the five story files, [acceptance-criteria-checklist.md](acceptance-criteria-checklist.md), [STATUS.md](STATUS.md), then the [assembly plan](feature-assembly-plan.md), [ADR-0075](../../../architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md) and [worked examples](worked-examples.md). The additive implementation has independent review and operator approval for the bounded local scope. Read the run PM closeout and Security report before using it.

The product root bound for this run is `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Framework commands run from `/home/gajap/uSandbox/repos/nebula/nebula-agents` and always receive that absolute root.

To resume this run, first execute from the framework:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-02-5a00b0ff
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature
```

Do not initialize a new run for this checkpoint. Implementation evidence is under `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/`. The original planning approval remains recorded independently in the 2026-11-01 planning runs.

## Implementation and local verification

Key code is in `engine/packages/brain-assertions/`, the strict DTO/dispatch/schema
additions in `brain-contracts`, and the persistence adapter plus migration 0011.
Existing security mutation, fact commit and review consumers enforce source READ and
eligibility before effects. There is no assertion HTTP endpoint or automatic v2 producer.

The run's `deployability-check.md` documents locked builds, immutable-image smoke,
schema packaging and guarded rollback. Run `artifacts/runtime/compose.yaml` from the
product root after starting the existing PostgreSQL dependency; use the run's
`artifacts/runtime/prepare_database.py` inside engine-validation for the dedicated
runtime database. Test commands and results are durable under the run, including
`artifacts/test-results/g3-sec04-regression.xml` and the QE-owned reports. Do not
point destructive test cleanup at the historical development database.

New F0006 integration fixtures require explicit BRAIN_MIGRATION_ADMIN_URL and use
owned temporary databases. They require neither a model nor conversion. Optional
existing OCR regression modules use separate processes and bounded numerical-library
thread counts; their model cache must be writable inside the container.

## Compatibility context

F0005 closed by rejecting Graph dense. Its final STATUS/ADR-0060 decision and accepted ADR-0074 govern current execution controls; earlier proof summaries do not establish activation. `direct-baseline` with the v1 writer remains default. F0006 must support legacy result readers and correction chains without fabricated provenance. The existing strict schema is `planning-mds/schemas/interpretation-result.schema.json`; The approved Phase B design supplies a compatible versioned addition.

Existing consumer locations and implemented changes are enumerated in the assembly plan: DocumentResultImporter, additive review correction, CanonicalCommitService and current fact/review routes. The new strict schemas are `assertion-record-v2`, `interpretation-result-v2` and `assertion-admission-result-v1` under `planning-mds/schemas/`. The legacy result schema is preserved. Sixteen synthetic shape/version cases in `contract-examples.json` distinguish expected validity from runtime behaviour.

Do not nest the existing read authorization facade inside a mutation: it commits its own unit of work. The assembly plan specifies an optional trusted source-read callback on the mutation facade, keeping source and commit decisions in one transaction. New v2 writes require guard-capable consumers to be deployed first; rollback retains the extension and guard once v2 rows exist. No new runtime config flag is added.

## Semantic examples

Reuse [EX-GL-001](../../../examples/neurosymbolic-gl/README.md) and [EX-SEM-001/005–007](../../../examples/statements-time-and-governance.md). They are synthetic teaching fixtures, outside the frozen holdout. A genuine quote with a misread value passes structural admission and still needs review. Keep all illustrative expectations separate from observed implementation evidence.
