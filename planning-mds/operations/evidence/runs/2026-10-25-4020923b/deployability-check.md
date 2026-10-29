# Deployability Check — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

> DevOps-owned. Scope: the local Docker Compose runtime only, per the 2026-10-23 operator scope decision. No production deployment is claimed.
>
> **Round 2 (2026-10-27):** images rebuilt with the pypdf 6.21.2 lock and migration 0010; smoke re-run (`artifacts/runtime/logs/g2r-*.log`). Round-1 results are kept below where unchanged.

## Round 3 (2026-10-28, final)

- `neuron/uv.lock`: litellm 1.100.0 → 1.100.4 (SEC-F5-L6; released 2026-09-29).
- New dependency-free module `brain_extraction/pins.py` holds the Docling-Graph pin.
- Images rebuilt (`artifacts/runtime/logs/g2r3-build.log`). Smoke checks pass (`artifacts/runtime/logs/g2r3-smoke.log`): both containers healthy, head `0010`, committed config `direct-baseline`/100/v2 off.
- Scans re-run under `artifacts/security/g2r3/`. Post-decision check: `artifacts/test-results/post-decision-check.log`.
- **New operator-visible codes:**
  - `provider_listener_unowned` and `provider_restart_cleanup_unconfirmed` (supervisor);
  - `conversion_budget_exhausted` (recorded as `conversion_failed`);
  - the `pdf_structure_unreadable` warning.
  The runbook already covers quiescence; these fail closed.

## Runtime / Deployment Config Changes

| Change | Path | Effect |
|---|---|---|
| `extraction.pipeline: direct-baseline` (new, required, no environment override) | `config/local.yaml` | New submissions pin the baseline. Isolated qualification configs select Graph engines without touching the committed file. |
| `jobs.max_queue_depth: 100` (new, positive int, default 100) | `config/local.yaml` | Submissions beyond 100 unfinished jobs exit with code 4 (`queue_depth_exceeded`). |
| `content.v2_writer_enabled: false` (unchanged) | `config/local.yaml` | v2 publication stays off pending S0004 acceptance. |
| Host inference guard control directory | `/tmp/nebula-brain-inference-<uid>/` (runtime, not committed) | One worker per canonical endpoint; lock, in-flight marker, provider record, quiescence receipts. |
| Provider supervisor CLI (new) | `python -m brain_ingestion.provider_supervisor record\|quiesce\|status` | DevOps records the dedicated vLLM process group at preflight and confirms quiescence after uncertain requests. |
| `BRAIN_ENABLE_GRAPH_CANDIDATE` gate removed | `worker_cli.py` | Engine choice comes only from committed or isolated config. |
| Runbook | `docker/local-inference-runbook.md` | Guard, quiescence and recovery procedure. |
| Package data | `neuron/packages/brain-ingestion/pyproject.toml` | Ships `ocr_asset_pins.json` in the wheel. |
| pypdf 6.19.0 → 6.21.2, floor `pypdf>=6.21.2` (round 2) | `neuron/uv.lock`, `neuron/packages/brain-ingestion/pyproject.toml` | Clears 11 pypdf advisories on the untrusted-PDF path. No other locked package changed. |
| Provider record validation and unauthenticated-restart check (round 2) | `worker_guard.py`, `provider_supervisor.py`, runbook | `record`/`quiesce` refuse non-`vllm serve`, wrong host/port or argv-credential records (`provider_record_invalid`), and a restart that accepts unauthenticated requests (`provider_restart_unauthenticated`). |

No Dockerfile, Compose file, port or image-pin change in the product. `engine/uv.lock` is unchanged from HEAD.

## Migrations / Rollback

- `0009_f0005_job_event_reason` adds a nullable `document_job_event.reason VARCHAR(64)` with CHECK `ck_document_job_event_reason` over the 13 frozen reasons. Historical rows stay NULL.
- Downgrade refuses while any reason is recorded (no silent data loss); without reasons it drops cleanly, and re-upgrade is idempotent.
- `0010_f0005_job_event_reason_expand` (round 2) widens the same CHECK constraint with four reasons. Its downgrade refuses while any of them is recorded; without them it restores the 0009 constraint. Tested in `test_job_event_reason_migration.py` (9 passed).
- A backup and isolated restore preserve the column and rows.
- Evidence: `engine/tests/integration/test_job_event_reason_migration.py`, 4/4 passed in `artifacts/test-results/g2-engine-full.xml`, plus the containerized `alembic heads` = `0009 (head)` in `artifacts/runtime/logs/smoke.log`.
- Extraction rollback is a committed config change (`extraction.pipeline`). Jobs keep their pinned pipeline; legacy jobs keep `graph-direct`. Proven by the live decision branches (11/11).

## Env / Config Contract

No new environment variables. Existing: `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_API_KEY` (from `~/.brain-secrets`, mode 0600, never logged), `BRAIN_INFERENCE_MODEL`, `BRAIN_INFERENCE_MODEL_REVISION`, `BRAIN_WORKER_DATABASE_URL`, `BRAIN_LOCAL_CONFIG_PATH` (isolated-config facility only). `GETTING-STARTED.md` and the runbook are updated.

## Manifest Boolean Cross-Check

| Boolean | Value | Basis |
|---|---|---|
| `runtime_bearing` | true | engine/neuron source changes |
| `deployment_config_changed` | true | `config/local.yaml`; migration 0009 (`**/migrations/**`, `**/config/**`) |
| `security_sensitive_scope` | true | inference credential handling, host lock/control directory, authorization revocation, tenant-scoped bundles/runs |
| `frontend_in_scope` | false | no UI or endpoint |

## Build / Start / Smoke Results

Harness: `artifacts/runtime/` (`Dockerfile`, `compose.yaml`, `smoke.sh`), adapted from F0004's validation harness. Images are built from the working tree with `uv sync --locked`.

- **Round 2:** `artifacts/runtime/logs/g2r-build.log` (both images rebuild, `build exit=0`) and `artifacts/runtime/logs/g2r-smoke.log` (both containers healthy; pins; deadline 300.0; OCR pins load; committed config `direct-baseline`/100/v2 off; both CLIs start; `alembic heads` = `0010`; `/health` ok).
- Round 1: `artifacts/runtime/logs/build.log`: both images build (`build exit=0`).
- `artifacts/runtime/logs/smoke.log`:
  - engine and neuron containers healthy;
  - Docling 2.126.0, Docling-Graph 1.9.1 and RapidOCR 3.9.2 resolve;
  - F0005 modules import, the conversion deadline is 300.0 s and the OCR pins load;
  - committed config resolves to `direct-baseline` / depth 100 / v2 writer false;
  - worker and provider-supervisor CLIs start;
  - `alembic heads` = `0009`;
  - engine `/health` reports `ok`.
- Live host runtime (GPU, vLLM 0.25.1, PostgreSQL 18) is exercised end to end by the live suites in `test-execution-report.md`, including provider quiescence/restart (43–85 s) with restart receipts.

## Runtime Warnings

- Quiescence restarts the shared development vLLM. It uses only the recorded argv, and restart receipts are in the control directory.
- **Round 2 dependency scan** (`artifacts/security/g2r/dependency-neuron.json`): pypdf cleared. Remaining: pillow 38, docling/docling-slim 15, aiohttp 8, filelock 3, litellm 1 (published after round 1), certifi 1, setuptools 1. These are for G3 Security judgment.
- Round 1: `neuron/uv.lock` carried 76 published advisories (pillow, pypdf, aiohttp, filelock, certifi, setuptools, plus the 15 Docling advisories already reviewed at F0004 G3). None was introduced by F0005: the lock is unchanged, and the new ones were published after F0004's scan. Changing the lock would invalidate the measured pins; this needs G3 Security judgment and an operator decision. See `artifacts/security/dependency-neuron.json`.
- Two pre-existing ZAP passive-header warnings on `/health` and `/openapi.json` (unchanged from F0002).
- The validation containers `brain-f0005-4020923b-*` remain up for G3 reviewers and will be stopped at closeout.

## Result

PASS WITH RECOMMENDATIONS
