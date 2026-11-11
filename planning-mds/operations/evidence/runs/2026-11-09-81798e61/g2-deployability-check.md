# Deployability Check — F0007 remediation

Role: DevOps / Codex primary coordinator. Date: 2026-11-10.

## Runtime / Deployment Config Changes

Production runtime/API package wiring and dependencies are unchanged. New follow-up migration0013 and CI inclusion of its/authorization regressions are deployment-bearing. Source/test/docs/KG changes are inventoried in artifacts/diffs/changed-files.txt; original final merged inventory includes both Neuron test adaptations in artifacts/diffs/original-final-changed-files.txt. No new production env variable, service, port, grant or producer.

## Migrations / Rollback

Single lineage0011→0012→0013. Shipped0012 byte-for-byte unchanged.0013 locks fact_slot, inventories malformed rows, refuses without repair, and installs strict TRUE shape check. Downgrade restores exact0012 guard with all rows unchanged; below0012 still refuses occupied identity/qualifier data. Sixteen new PostgreSQL migration cases prove direct NULL/legacy negatives, uniqueness, byte-identical pilot/valid rows across up/down/up and safe refusal for malformed0012 data. See migration-guard-green JUnit and final engine suite.

## Env / Config Contract

Application validation uses artifacts/runtime/compose.yaml with existing project images, read-only current source and a writable evidence mount. Only the validation runner exposes Docker CLI/socket for isolated backup drills and adds its existing host Docker group. Restore targets use the existing dependency network. No product Compose definition or shared service topology is modified. Image IDs for scanners are frozen in artifacts/scanner-image-ids.txt; no tag pull was required. Temporary audit tools install only under container/tmp.

## Build / Start / Smoke Results

Engine and Neuron containers start; engine import/PostgreSQL preflights pass. Full engine868pass, targeted combined319pass, affected Neuron27pass. A fresh owned database migrates to0013 before the API starts; its OpenAPI200 and ZAP113PASS/0WARN/FAIL prove startup/API smoke. API process is terminated and only its owned DB dropped. Static Ruff/mypy checks pass. Evidence paths are in the QE/security reports and commands.log.

## Existing Data Inventory

Read-only development inventory (artifacts/existing-data-inventory.txt) reports database0010, F0007 columns not adopted, no identity-v1 carriers to repair. The shared database remains0010; no migration/repair was applied. artifacts/runtime/inventory_existing.py supplies reproducible counts/limited IDs for adopted environments; non-production/custom contracts remain explicitly unverified rather than falsely clean. Any future identified corruption requires governed operator resolution before rollout.

## Runtime Warnings

Existing Alembic path_separator, synthetic test HMAC-key length and Docling/Pydantic deprecation warnings are disclosed. Initial missing Docker CLI and Neuron Alembic runner were runtime setup issues, fixed and rerun without application behavior changes. No open deployment blocker remains in this bounded local validation. No production rollout occurred.

## Result

PASS
