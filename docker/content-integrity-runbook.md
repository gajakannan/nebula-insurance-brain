# F0004 content integrity operations

This runbook accompanies revision 0008. Keep `content.v2_writer_enabled: false`
until the feature's consumer compatibility, migration, restart and isolated
restore checks pass. ADR-0073 remains Proposed during implementation.

Run from a locked neuron environment with the existing ingestion ServicePrincipal,
`BRAIN_WORKER_DATABASE_URL` and `BRAIN_WORKER_PRINCIPAL_ID` already configured.
The database URL must use `postgresql+psycopg`. The committed local configuration
selects the immutable filesystem content root; no storage-provider override or
new grant is introduced. The policy directory must match the active policy release.

After deploying the dual-version readers and applying the additive expansion,
inventory and backfill each tenant/knowledge base:

```sh
uv run --project neuron --locked brain-content-integrity-sweep \
  --policy-dir planning-mds/security/policies \
  --tenant "$TENANT_ID" --knowledge-base "$KNOWLEDGE_BASE_ID" --action backfill
```

Each artifact has its own transaction. Current ingest authority, verified bytes,
observed metadata, decision, mutation audit and state event commit together.
Backfill preserves bundle bytes and old IDs. `BLOCKED` leaves the row
`legacy_unverified` and records ambiguous metadata for DevOps; unavailable origin
or dates are never invented. `QUARANTINED` records a definitive integrity failure.
A successful process exit means the inventory completed; inspect its counts and
repair records before proceeding. Findings do not authorize writer activation.

Run the same command with `--action sweep` after failed content-read audits,
after a restore drill and before writer activation. Reads themselves only persist
their failed authorization decision; they never quarantine or create repair rows.
The sweep verifies every ready/legacy row and inventories orphan markers using
provisioned pre-record security metadata. Orphans have no ready row and cannot
be served through the API. Their owner is never inferred from a source hash.
Transient storage errors produce `CONTENT_UNAVAILABLE`, a failed decision and no
quarantine. Denial commits only its authorization audit.

DevOps owns repair-record triage. Restore the exact original bytes/indexes from
a verified backup through the governed restore procedure, then explicitly repair
one quarantined artifact:

```sh
uv run --project neuron --locked brain-content-integrity-sweep \
  --policy-dir planning-mds/security/policies \
  --tenant "$TENANT_ID" --knowledge-base "$KNOWLEDGE_BASE_ID" --action repair \
  --artifact "$ARTIFACT_ID" --repair-record "$REPAIR_RECORD_ID"
```

Repair requires current ingest authority and full identity/index verification.
It appends a resolving repair row, mutation audit and `AUTHORIZED_REPAIR` state
event; it never changes the original bundle or history. Orphan markers remain for
an authorized retry of the original fenced publication. Do not delete, reparse,
infer an owner, or promote an orphan through a direct database insert.

After all legacy inventory is reconciled and ready, quiesce ingestion, date and
operator writes for the uniqueness reconciliation window. This operation affects
the whole database and requires current ingest authority for **every artifact**,
including artifacts outside the scope arguments. A denial, changed inventory,
verification failure or unready row rolls back the entire operation.

```sh
uv run --project neuron --locked brain-content-integrity-sweep \
  --policy-dir planning-mds/security/policies \
  --tenant "$TENANT_ID" --knowledge-base "$KNOWLEDGE_BASE_ID" --action reconcile \
  --all-scopes --writers-quiesced
```

The transaction locks the artifact table, re-verifies the complete inventory and
drops only the catalog-discovered `UNIQUE(document_version_id)` constraint. Owner
keys, foreign keys and v2 recipe uniqueness remain. An empty inventory defers the
operation without DDL. Resume writers after the window. Do not set the v2 flag
until the recorded consumer and restore gate results permit it.

Never downgrade after v2, index, date, state or repair history exists. Revision
0008 refuses destructive downgrade; preserve original bundles, source archives,
run outputs and append-only history and use forward repair.

## Quiesced local backup and isolated restore

Stop ingestion, date and operator writers for the entire capture window. The
procedure verifies inventories before and after capture; that check supplements
the operator's quiescence and does not create a distributed snapshot.

```sh
BRAIN_WRITERS_QUIESCED=1 bash scripts/ops/backup.sh
bash scripts/ops/restore.sh /path/to/the/printed/backup-directory
```

The configured content root must contain all original bundles, retained run
outputs and publication intent receipts. The backup records revision, application
table hashes, every object hash, both dependency locks and all five packaged
contracts. The database role needs local dump access. Optional non-secret local
overrides are `BRAIN_CONTENT_ROOT`, `BRAIN_BACKUP_ROOT`,
`BRAIN_POSTGRES_CONTAINER`, `BRAIN_POSTGRES_DATABASE` and `BRAIN_OPS_DATABASE_URL`.
The default operator Python command is the frozen engine workspace; an already
locked runtime can set `BRAIN_OPS_PYTHON` to its Python executable.

Restore verifies required files and hashes before starting a uniquely named
throwaway database, safely extracts into an empty temporary directory, compares
the exact database/object inventories and resolves citations with the v1/v2
verifier. It checks normalized indexes, date ownership/correction/selection
lineage, authorization-audit identity and retained run/date pins. Missing required
bytes fail; unreferenced partial objects are reported and retained. No original
database, accepted source or artifact is changed, and restoration grants no
permission. The default target binds only a fresh loopback port. An application
validation job can set `BRAIN_RESTORE_NETWORK` to its existing Docker network;
the throwaway database then uses container DNS without a published port.
`BRAIN_RESTORE_IMAGE` selects the already qualified local Postgres image.

The drill removes only its unique container and temporary content directory.
Pass `--keep` as the second restore argument to retain those targets for operator
inspection. After a real recovery, run the current-authority integrity sweep
above before writer activation; the drill itself appends no production repair
or quarantine records.
