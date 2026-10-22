# F0004 — Implementation handoff

**Position:** Implementation complete, G4 explicitly approved on 2026-10-21, all required G5 signoffs and G6/G7 checks passed. Feature run 2026-10-17-8a6cc79f contains the current proof and closeout; the planning instructions below are retained as design history.

## Read first

1. [PRD](PRD.md), [acceptance checklist](acceptance-criteria-checklist.md) and four stories in [README](README.md).
2. [Assembly plan](feature-assembly-plan.md): exact interfaces, publication transaction, error contracts, migration and proof matrix.
3. [ADR-0073](../../../architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md), which remains Proposed until runtime proof.
4. [Persistence design](persistence-design.sql), [worked examples](worked-examples.md) and [synthetic schema cases](contract-examples.json).
5. Product [SOLUTION-PATTERNS](../../../architecture/SOLUTION-PATTERNS.md), [AuthX assembly](../F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md) and [PostgreSQL ownership](../F0003-postgresql-persistence/feature-assembly-plan.md).

## Existing integration points

From the product root `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`:

| Boundary | Existing source |
|---|---|
| Strict manifest and stores | `engine/packages/brain-content/src/brain_content/{manifest,store,checkpoints}.py` |
| Native-to-bundle projection | `neuron/packages/brain-ingestion/src/brain_ingestion/bundle_writer.py` |
| Converter result handoff | `neuron/packages/brain-interpretation/src/brain_interpretation/parsed_content.py` |
| Pinned extraction adapter | `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_pipeline.py` |
| Worker composition and fenced delivery | `neuron/packages/brain-ingestion/src/brain_ingestion/{worker_cli,document_worker}.py`; `engine/apps/worker/src/brain_worker/document_delivery.py` |
| Generation fence | `engine/packages/brain-jobs/src/brain_jobs/queue.py` |
| Durable metadata and authorization | `engine/packages/brain-persistence/src/brain_persistence/{models,authx}.py` |
| Authorized public reads | `engine/apps/api/src/brain_api/routes/content.py` |

Read these before adding files; the shared verifier replaces duplicated validation, and the ready registrar extends the existing before-extraction registration. Preserve established signatures until all callers have version-aware adapters. The future files and exact method signatures are in the assembly plan.

## Planning checks

The following checks are executable now; `jsonschema`, `referencing` and PyYAML are present in the planning environment. They do not execute a parser, write runtime metadata or prove the migration:

```sh
python3 planning-mds/features/archive/F0004-content-artifact-model/validate-contract-examples.py
python3 scripts/validation/validate_plan_readiness.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --plan-scope feature --target F0004
python3 scripts/kg/validate.py --check-drift
python3 scripts/kg/validate.py --check-reproducible
```

All examples are synthetic development fixtures. Hashes in `contract-examples.json` are shape placeholders; trusted HUMAN authority, exact source bytes, DB ownership, date selection concurrency and publication recovery require separate tests. Keep these fixtures outside the frozen holdout.

## Build and proof order

Implement assembly steps 1–4 in sequence. **Start with the Step 1a per-item provenance spike** and record its PASS/FAIL exit decision before any v2 writer code. On FAIL, new sources stay on the v1 writer and S0002's v2 origin criteria return to the operator. Then build explicit legacy/v2 readers and record types. Next add the shared verifier and an additive Alembic revision after 0007. Reconcile legacy bytes before readiness backfill or writer activation. Legacy v1 rows stay readable throughout. A failed verification fails the read, and the operator-run integrity sweep quarantines the row with a repair record, its authorization decision committed in the same transaction (`decide` over `SyncAuthorityStore`). After v2 activation, a document with an `ORIGIN_UNAVAILABLE` item falls back to v1 with a recorded reason. Then implement append-only date storage and authorized consumers.

Use the product's pinned Python workspace and PostgreSQL 18 integration environment. Discover the exact workspace test commands from its current package configuration at implementation time; the assembly plan names the target suites and independent assertions. No runtime test, migration, backup or restore command was executed by this planning action.

Before acceptance, capture native/scanned PDF round-trips, both store adapters, legacy preservation, denied/revoked reads, stale lease and publication crash cases, concurrent date selection, controlled HUMAN verification, restart reuse with converter/OCR entry points forbidden, and isolated database-plus-byte restoration. Changed runtime coverage must reach 80%. All four stories require Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect signoff.

## Dependencies and limits

F0001/F0002/F0003 approved evidence references and impacted consumers are recorded in the run's [dependency audit](../../../operations/evidence/runs/2026-10-15-bbd8df01/artifact-trace.md). F0005 integration must preserve its proven candidate machinery; F0004 does not activate it for production. F0016/F0022 consume the new date/origin contracts later. The production human-decision and human-selection verifiers default to rejection until F0022 supplies them, so no document date is selected in production yet. The CONTENT/SOURCE_METADATA candidate producer is an open decision (BLUEPRINT §4.8).

No new UI, API write endpoint, grant, model engine, cloud store, time resolver or corpus migration executor is part of this plan. Existing C4 context/container diagrams still apply because no deployable boundary changes.

## Current implementation and operator use

Read the [feature evidence](../../../operations/evidence/runs/2026-10-17-8a6cc79f/README.md), [integrity runbook](../../../../docker/content-integrity-runbook.md), current worker content publication/access modules, shared verified store and document_dates service. Existing source identities and saved-native consumers are reused before conversion. V2 publication stays default false.

Application validation used the run-scoped Compose jobs with the locked Python workspaces; exact commands are in commands.log. PostgreSQL migration, recovery, authority, date concurrency, actual OCR/provenance and isolated restore all ran. Legacy content remains byte-preserved. The production source/human verifier ports still reject by default. Do not activate a writer or reconcile a shared corpus merely because this feature is archived.
