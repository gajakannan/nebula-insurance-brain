# Feature Security Review Report

Feature: F0005 — One-time Docling ingestion (run `2026-10-25-4020923b` , gate G3 round 2)

Reviewer: Security Reviewer (fresh independent session; not an author of the code, the round-2 rework or its evidence). Date: 2026-10-28.
Product: `nebula-insurance-brain` , branch `feature/f0005-live-qualification` , uncommitted worktree. Reviewed `git diff` plus untracked files.
Scope: local Docker Compose and development host only (ADR-0060 acceptance scope: trusted operator CLI, synthetic hash-pinned corpus, dedicated loopback vLLM). This review does not qualify production, non-synthetic documents or any activation.
Round-1 report: `security-review-report-round1.md` (retained unchanged).

Result: PASS WITH RECOMMENDATIONS

## Summary
- Assessment: PASS WITH RECOMMENDATIONS
- Findings: Critical 0, High 0, Medium 1, Low 3. The Medium is the carried SEC-F5-M1, deliberately left open by the operator and recorded as an activation precondition in ADR-0074 §1. The three Lows are new this round (SEC-F5-L4, SEC-F5-L5, SEC-F5-L6). Pre-existing F0004 SEC-L2 (ZAP header warnings) is noted and not counted.
- Round-1 closure: L2 closed, L3 closed, pypdf upgrade closed. L1 partially closed: write-time, use-time and pre-signal validation and the unauthenticated-restart refusal are in place and tested, but the executable is not bound and two of the five round-1 remediation items were not done (residual tracked as SEC-F5-L4). M1 open by operator decision.
- New code reviewed: OCR bundle fields, rejection records and call phases, migration 0010, the fault proxy busy mode, and the guard-infrastructure stop. None carries source text or secrets. Migration 0010 SQL is safe. The fault proxy cannot be reached from the production composition.

## Findings

### Critical
- None.

### High
- None.

### Medium

**SEC-F5-M1 (carried, open by operator decision): the converter child has environment isolation only**
- Status: unchanged from round 1. `conversion_process.py` still passes `HOME` in `_CHILD_ENV` and spawns the child as the same UID with no rlimits.
- ADR-0074 §1 "Known limit" records it as required before any activation or non-synthetic document. That matches the round-1 target, so it does not block this closeout on the rejection/non-activation branch.
- Round 2 changes the dependency side of the exposure:
  - pypdf is now 6.21.2, which clears all 11 pypdf records, including the DoS that was reachable in the child.
  - Pillow went from 37 to 38 records (3 new PYSEC ids, 2 re-aliased away). Docling and docling-slim still carry 15 between them.
- Not exploitable in the current synthetic, trusted-operator scope.
- Owner: AI Engineer + DevOps. Target: activation precondition.

### Low

**SEC-F5-L4 (new; residual of SEC-F5-L1): the provider-record check does not bind the executable, and part of the round-1 remediation is not done**
- Location:
  - `neuron/packages/brain-ingestion/src/brain_ingestion/worker_guard.py:390` . `program` is accepted when either `argv[0]` or `argv[1]` has basename `vllm`.
  - `neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py:118-128` . The restart has no `env=`, and the log is opened with the default umask.
- What, with my scratchpad probe (`g3r/probe_l1_l2.py` , sentinel values only):
  - The probe ran `ProviderRecord.validate` against loopback `:8000` and accepted all of these:
    - `["/tmp/evil", "vllm", "serve", …]`
    - `["/bin/sh", "/tmp/x/vllm", "serve", …]`
    - `["/tmp/x/vllm", "serve", …]`
  - So the check stops operator error (a wrong PID, a `bash -c` wrapper, another port or host, a credential flag) but does not stop a tampered record from naming an arbitrary program. `quiesce` would `Popen` that program with the supervisor's full environment, which after `source ~/.brain-secrets` includes `BRAIN_INFERENCE_API_KEY` .
  - Not done from the round-1 L1 list:
    - listening-socket ownership is not checked; host and port are checked from argv only;
    - the restart environment is not minimal;
    - the provider log is not `0600`. On the live host `<key>.provider.log` is still `-rw-r--r--` , mitigated by the `0700` directory.
- Exploit scenario: only the same UID (or root) can write the `0700` control directory. Such an attacker can already read `~/.brain-secrets` , so the gain is the persistence foothold through `quiesce` already described under M1. Severity stays Low.
- Remediation, any of:
  - pin the resolved executable (`/proc/<pid>/exe` and the realpath of the `vllm` entry point) to an operator-owned allowlist outside the control directory, and re-check it at use;
  - check that the recorded PID owns the listening socket at record time;
  - restart with an explicit minimal environment (`PATH`, `HOME`, `VLLM_API_KEY`, the HF and CUDA variables);
  - open the log `O_CREAT|O_NOFOLLOW` with mode `0600` .
- Owner: DevOps. Target: before activation, together with M1.

**SEC-F5-L5 (new): a refused or failed restart leaves the restarted provider running**
- Location: `provider_supervisor.py:120-138` . `wait_ready` raises `provider_restart_unauthenticated` or `provider_restart_not_ready`, and nothing terminates `process`.
- What: the new refusal check is correct and tested (`test_a_restart_that_accepts_unauthenticated_requests_is_never_ready`). But on refusal the server that accepts unauthenticated requests stays up on `127.0.0.1:8000` as an orphan holding the GPU.
  - The marker stays dirty, so workers correctly refuse to claim.
  - Any local process can still use the unauthenticated model until an operator intervenes.
  - The next `quiesce` sees the old (dead) record, finds an empty group, and its restart then collides on the port.
  - The test only exercises `wait_ready` directly, so the orphan path is untested.
- Exploit scenario: a loopback-only, unauthenticated model on a single-user development host. The impact is GPU use and model access by local processes. No data or credential is exposed.
- Remediation:
  - on any `wait_ready` failure, `terminate_group(process.pid, …)` and confirm the group is gone before re-raising;
  - add a test through `quiesce_and_restart` .
- Owner: DevOps. Target: before activation.

**SEC-F5-L6 (new advisory): litellm 1.100.0 GHSA-7hp6-4w63-5g45 (proxy privilege escalation to RCE)**
- What:
  - litellm is a transitive dependency of docling-graph in `neuron/uv.lock` . No first-party module imports it.
  - The advisory is in the litellm **proxy server** (the `internal_user` to `proxy_admin` token forgery).
  - The proxy cannot start in this environment: `fastapi` and `uvicorn` are not installed in the neuron venv.
  - The `litellm` and `litellm-proxy` console scripts exist but nothing runs them, and no compose service or worker path does.
  - The inference client is the first-party `VllmGraphClient` (OpenAI SDK over httpx).
- Exploit scenario: none reachable here.
- Remediation: upgrade litellm to 1.100.4 or later. It is a patch-level change outside the measured Docling, OCR and model pins. Re-run the offline suite.
- Owner: AI Engineer. Target: follow-up, next lock refresh, and in any case before activation.

### Pre-existing items, not counted as new
- ZAP `X-Content-Type-Options` [10021] and `Cross-Origin-Resource-Policy` [90004] warnings on `/health` and `/openapi.json` . These are F0004 SEC-L2; F0005 changes no `engine/apps` path.
- aiohttp 8, filelock 3, certifi 1, setuptools 1. Same records and the same not-material reasoning as round 1:
  - aiohttp: no aiohttp server in the worker;
  - filelock: no Windows or SQLite read-write-lock use;
  - certifi: CA trust for model-download egress only;
  - setuptools: Windows wheel install only.

### Informational (no action required)
- Call records store `phase` = `response_schema_name` unfiltered (`vllm_graph_client.py` `_request`), while rejection records filter it to `[A-Za-z0-9_-]{1,64}` .
  - On every path in use the value is a fixed identifier: Graph's `direct_extraction`/`dense_skeleton`/`dense_fill`/`dense_reconcile`/`dense_root_identity`/`alias_reconcile` names, or `profile.template.__name__` .
  - Graph's `templategen` path, which derives a name from context, is not used.
  - Neither list is persisted in run manifests: `graph_interpretation.py` persists only `model_revision`, `endpoint_hash` and `limits`. Apply the same filter to the call record for consistency at the next change.
- Migration 0010 drops and re-creates the CHECK, so it validates the full table under an ACCESS EXCLUSIVE lock. That is an operational note only; the table is small locally.
- OCR asset digests are an identity check made after RapidOCR loads the `.pth` files. They are not a load-time integrity gate. This is unchanged behavior and is covered by M1's isolation requirement.

## Round-1 Finding Closure

| Round-1 item | Round-2 status | Verification |
|---|---|---|
| SEC-F5-M1 converter OS isolation | **Open — accepted as activation precondition** | Code unchanged (same UID, `HOME` passed, no rlimits). ADR-0074 §1 "Known limit" records the precondition, and so does the G4 operator decision in `gate-decisions.md` . |
| SEC-F5-L1 provider-record trust | **Partially closed** (residual → SEC-F5-L4; new related gap SEC-F5-L5) | Closed parts: `ProviderRecord.validate` requires the same endpoint, `pid == pgid`, `serve`, `--host`/`--port` equal to the guarded endpoint, and no `--api-key`/`--api-key=`. It runs at write time (`capture`, `record_provider`) and at use time (`load_provider`, used by `worker_cli.processing_worker` and `quiesce`). Before any signal, `confirm_stopped` requires `is_live()` (start ticks, live `getpgid` and the argv to match), otherwise it raises `provider_ownership_unconfirmed` and signals nothing. `wait_ready` refuses a server that answers an unauthenticated `/v1/models` with anything but 401. Tests: `test_tampered_or_mistaken_provider_records_are_refused` (5 cases, write and use), `test_quiescence_fails_closed_when_pid_was_reused`, `test_a_restart_that_accepts_unauthenticated_requests_is_never_ready`. Live record: `pid == pgid`, argv `…/brain-vllm/bin/python …/brain-vllm/bin/vllm serve`, no credential flag. Open parts: executable not bound, no socket-ownership check, inherited environment, log `0644` . |
| SEC-F5-L2 API key in repr | **Closed** | `LiveSettings.api_key: str = field(repr=False)` at `neuron/benchmarks/f0005_qualification.py:237` . A probe with a sentinel value shows `repr()` excludes it. Credential-pattern search of the run folder (Bearer, `api_key=`, `--api-key`, API-key assignment literals) finds no values. The production clients take the key as a constructor argument and store it only inside the OpenAI SDK or a header. |
| SEC-F5-L3 `--pipelines` into DDL | **Closed** | `--pipelines` has `choices=sorted(EXTRACTION_PIPELINES)` (`:722`), and `isolated()` re-checks `pipeline not in EXTRACTION_PIPELINES` before building the schema name (`:151`). The schema name is `f0005_qual_<closed value>_<uuid hex>` . The manifest SAST summary wording is corrected. |
| Dependency: pypdf ≥ 6.21.2 | **Closed** | `neuron/uv.lock` pypdf 6.19.0 → 6.21.2. The round-2 scan shows pypdf at 6.21.2 with 0 records (11 cleared). |
| Dependency: Docling ≥ 2.132 / pillow ≥ 13 requalification | **Open — activation precondition** | Still docling 2.126.0 and pillow 12.3.0, which changing would alter the measured pins. Carried in Recommendations. |
| F0004 SEC-L2 headers (pre-existing) | **Open — F0026 baseline** | Same two ZAP warnings. |

## Scan Verdicts

All four classes ran and resolve to round-2 artifacts; no waiver is needed. I did not re-run any scanner (no `g3r` artifacts). I triaged the raw round-2 outputs directly.

| Class | Ran | Raw result | Security verdict | Artifact(s) |
|---|---|---|---|---|
| dependency | yes (pip-audit in the rebuilt locked validation containers) | engine: 68 packages, 0 records. neuron: 181 packages, 67 records — pillow 38, docling 8, docling-slim 7, aiohttp 8, filelock 3, litellm 1, certifi 1, setuptools 1. Compared with round 1: pypdf 11 cleared, litellm GHSA-7hp6-4w63-5g45 new, pillow +3 PYSEC ids / −2 old ids. | **Accepted for the local synthetic scope only.** Pillow and Docling records fall under SEC-F5-M1 and the Docling requalification (activation precondition). litellm is not reachable: proxy only, fastapi and uvicorn absent (SEC-F5-L6, follow-up). aiohttp, filelock, certifi and setuptools are not material, as in round 1. | `artifacts/security/g2r/dependency-neuron.json` `artifacts/security/g2r/dependency-engine.json` (log `artifacts/security/g2r/dependency-scan.log` ; wrapper `artifacts/runtime/g2r-dependency-scan.sh` ) |
| secrets | yes (gitleaks dir mode, redacted; engine, neuron, scripts, config, docker, run folder) | 0 in engine, neuron, scripts, config and docker. 2 `generic-api-key` in the run folder. | **PASS — both are false positives.** Both are `tokenizer_revision` (the public Hugging Face commit SHA) in `artifacts/qualification/report.json` and `artifacts/qualification/diagnostic-dense-subset-NOT-MEASURED.json` , the same as round 1. Independent checks: credential-pattern grep of the run folder is clean. The live `provider.log` (421 KB) has 0 hits for api_key, Authorization, Bearer, request or prompt markers or fixture field names. The live provider record has no credential flag. The neuron validation container's environment holds no BRAIN_INFERENCE or VLLM variable names. | `artifacts/security/g2r/secrets-2026-10-25-4020923b.json` `artifacts/security/g2r/secrets-engine.json` `artifacts/security/g2r/secrets-neuron.json` `artifacts/security/g2r/secrets-scripts.json` `artifacts/security/g2r/secrets-config.json` `artifacts/security/g2r/secrets-docker.json` (log `artifacts/security/g2r/secrets-scan.log` ; wrapper `artifacts/runtime/g2r-secrets-scan.sh` ) |
| sast | yes (semgrep p/python + p/security-audit, 630 files) | 4 SARIF results, all `avoid-sqlalchemy-text`: `0005_tenancy_authx_expand.py:79` (suppressed in source), `0010_f0005_job_event_reason_expand.py:74` , and `neuron/benchmarks/f0005_qualification.py:156` and `:217` . The log reports 3 blocking. | **PASS — all are false positives after manual review.** 0010:74 builds its `IN (…)` list only from the module constant `ADDED` (four literals), and `_constrain` builds its CHECK only from the frozen `PREVIOUS`/`ADDED` tuples. No runtime input reaches either. The benchmark DDL now takes only a closed `EXTRACTION_PIPELINES` value plus a uuid hex (L3 closed). 0005 is unchanged from F0004. | `artifacts/security/g2r/sast.sarif` (log `artifacts/security/g2r/sast-scan.log` ; wrapper `artifacts/runtime/g2r-sast-scan.sh` ) |
| dast | yes (ZAP API scan of the rebuilt `engine-validation`) | 0 FAIL, 117 PASS, 2 WARN (10021, 90004) on `/health` and `/openapi.json` . Informational only otherwise. | **PASS WITH RECOMMENDATIONS (pre-existing F0004 SEC-L2).** The API is non-HTML JSON on a local container with no published ports, and the engine API diff is empty. The F0005 surface (worker CLI, host guard, converter child, supervisor) is outside DAST reach and is covered by manual review and the offline and live lanes. | `artifacts/security/g2r/dast.json` `artifacts/security/g2r/dast.md` (also `artifacts/security/g2r/dast.html` and `artifacts/security/g2r/dast-scan.log` ; wrapper `artifacts/runtime/g2r-dast-scan.sh` ) |

## Focus-Area Review (round-2 changes)

| Area | Verdict | Basis |
|---|---|---|
| L1 record validation (write / use / pre-signal) and unauthenticated-restart refusal | Holds for operator error; residual L4/L5 | See the closure table. In `confirm_stopped`, a dead leader with surviving members is signalled only if the pgid has no new leader. Linux does not reuse a pgid while members live, so that holds. |
| L2 repr exclusion | Closed | `field(repr=False)` . A field with no default after another field with no default is valid dataclass ordering. The probe confirms it. |
| L3 pipeline validation before DDL | Closed | argparse `choices` plus an in-function check before `CREATE SCHEMA`/`DROP SCHEMA` . |
| OCR bundle fields (ADR-0073 §6) | Holds — no source text, no host paths | `OcrObservation` holds sorted int page numbers and an engine identity. The identity is the RapidOCR class path, the package version, `rapidocr:det=<file name>,…` (`path.name` only, no directory) and a SHA-256 over the pinned digest strings. An unpinned asset or a different engine gives `engine: null`, never a guess. Both v1 and v2 schemas use `additionalProperties: false`, and integer and string type constraints, on the new member. Child-supplied values are subject to M1 like every other child output. |
| Rejection records and call phases | Holds | Rejection record = `{phase (regex-filtered), outcome (InferenceRejected.code — internal constant or GuardError.code), failure_class (enum)}`. SDK exceptions are reduced to codes (`from None`). Diagnostics are not persisted to manifests. The job event receives only an enumerated `FailureReason` (validated in `queue._fail`/`_event` and by the DB CHECK). See the Informational item on the call-record `phase`. |
| Migration 0010 SQL | Holds | Expand-only. All SQL text is built from frozen module literals. Upgrade and downgrade pin `search_path` . The downgrade refuses offline `--sql` mode and refuses when any expanded reason exists. Re-creating the narrowed CHECK would itself fail on a concurrent insert, so the downgrade is fail-safe. Tests: `test_expansion_admits_new_reasons_only_after_0010` (4 reasons, including refusal of the downgrade), `test_expansion_downgrade_without_new_reasons_restores_the_0009_constraint` , `test_queue_reasons_match_the_frozen_migration_enumeration` . |
| Fault-proxy busy mode | Test-only; not reachable from production composition | `neuron/tests/support/fault_proxy.py` binds `127.0.0.1` and forwards only `authorization` and `content-type`. It records no bodies or headers. The busy body is a fixed prompt with `max_tokens` 3800 and `ignore_eos` (it fits in `max_model_len` 4096, so the resource use is bounded). Imported only by tests. `transport_url` is a keyword argument that `worker_cli.main()` never sets. Neither `docker/` nor `engine/apps` references the proxy or the benchmark. The validation image copies `neuron/` , so the file is present, but compose uses an idle `Event().wait()` command and no entry point reaches it. |
| Worker stop on guard-infrastructure faults | Holds — fail closed | A dispatch-guard failure sends nothing (`InferenceRejected(code)` before `create`). `guard_fault` turns `inflight_marker_not_durable` into `WorkerStopped`. The job is left to lease reclaim instead of being failed. `run_one` refuses to claim when the guard is not held or the outcome is uncertain. The CLI prints only the code (exit 3). |
| Credential handling, authorization re-check, tenant scoping, audit | Holds (unchanged from round 1) | Re-verified by the offline suites below. |

## Independent Verification Performed (offline only)
- neuron:
  - `test_worker_guard.py` , `test_conversion_process.py` , `test_document_worker_reasons.py` , `test_ocr_asset_provenance.py` , `test_ocr_quality.py` ;
  - integration: `test_pipeline_selection.py` , `test_interpretation_rejections.py` , `test_vllm_graph_client.py` ;
  - result: **158 passed, 1 skipped**.
- engine, against PostgreSQL via the scratchpad `pg.env` : `test_job_event_reason_migration.py` , `brain-jobs/test_queue.py` , `test_postgres.py` and `brain-content/test_config.py` gave **52 passed**.
- Probes in the scratchpad (`g3r/probe_l1_l2.py` , sentinel values, no real credential): the record-validation bypass shapes (L4), and the `LiveSettings` repr (L2 closed).
- Read-only host and container checks:
  - control directory `0700` and owner `gajap` ;
  - provider record shape;
  - provider log mode and its credential, prompt and request-marker scan;
  - environment variable names only in the neuron validation container;
  - Dockerfile and compose entry points.
- Not run, per instructions: live lanes, the benchmark, `provider_supervisor quiesce` . I did not re-run any scanner.

## Control Checks
- [x] Authorization coverage complete: re-checked per attempt, at publication and at interpretation; revocation is terminal and audited (unchanged).
- [x] Input validation enforced: PDF magic guard; closed pipeline and reason vocabularies; the benchmark DDL is now closed (L3); the OCR fields are schema-constrained. Parser residual risk stays under M1.
- [x] No secrets in code: the gitleaks hits are false positives; L2 is closed.
- [x] Auditability requirements met: enumerated reasons now cover pre-dispatch rejections (0010), with no source text.

## Per-Story Security Verdicts

| Story | Verdict | Evidence / conditions |
|---|---|---|
| F0005-S0001 Pin and process source documents | **PASS** | Supervised child unchanged. The new empty-page and damaged-page handling only lowers status. Condition: SEC-F5-M1 before non-synthetic input. |
| F0005-S0002 Persist artifacts and recover jobs | **PASS** | 0010 is expand-only with a refusing downgrade. Durable `conversion_started` counting. The guard-infrastructure fault stops the worker and leaves the job for reclaim. Enumerated reasons. |
| F0005-S0003 Reinterpret saved JSON and map evidence | **PASS** | Rejection records are code-only. Any rejection fails the attempt. The dispatch guard sends nothing without a durable marker. Loopback-only endpoint unchanged. |
| F0005-S0004 Evaluate and activate proven pipeline | **PASS** | Committed `config/local.yaml` stays `extraction.pipeline: direct-baseline`, `v2_writer_enabled: false`. No environment selection. L3 is closed. The fault proxy and benchmark are test-only. No activation is performed. |
| F0005-S0005 Qualify text origin and enable v2 publication | **PASS** | The OCR engine identity is pinned by digest. Unpinned means `null` and `ORIGIN_UNAVAILABLE`, never guessed. No paths or source text are in the identity. The v2 writer stays disabled. |

## S0004-AC4 Qualification Verdict (Security)

**Security supports recording the operator's rejection/non-activation decision. Nothing in the security evidence blocks recording acceptance or rejection at G4.**

- 0 Critical and 0 High. All four scan classes are backed by round-2 artifacts:
  - `artifacts/security/g2r/dependency-neuron.json` `artifacts/security/g2r/dependency-engine.json`
  - `artifacts/security/g2r/secrets-2026-10-25-4020923b.json`
  - `artifacts/security/g2r/sast.sarif`
  - `artifacts/security/g2r/dast.json` `artifacts/security/g2r/dast.md`
- Round-1 L2 and L3 are closed, and pypdf is upgraded. L1's core protections (validation at write, use and before signal; refusal of unauthenticated restarts) are implemented and tested.
- Supporting live evidence (not re-run by me): `artifacts/test-results/g2r-live-provider-storage-auth-faults.log` `artifacts/test-results/g2r-live-kill-points-and-competing-workers.log` `artifacts/test-results/g2r-live-timeout-faults.log` `artifacts/test-results/g2r-live-production-deadline.log`
- **Activation conditions, not transferable from this scope.** Before any pipeline is activated, or this worker processes a non-synthetic or externally supplied document, the following must be closed:
  - SEC-F5-M1 (OS-level converter isolation and a memory cap);
  - the Docling ≥ 2.132 / pillow ≥ 13 requalification;
  - SEC-F5-L4 and SEC-F5-L5.
- The present dependency acceptance is limited to the ADR-0060 local, trusted-operator, synthetic-corpus scope.

## Recommendation

APPROVE (PASS WITH RECOMMENDATIONS). There is no Critical or High finding; the carried Medium is an accepted activation precondition.

## Recommendations

- [medium] SEC-F5-M1: run the converter child with OS-level isolation: a separate unprivileged UID or container, no access to HOME, the control directory or the content store, no network, forced HF_HUB_OFFLINE, and a memory cap (RLIMIT_AS or cgroup) — owner: AI Engineer + DevOps; follow-up: activation precondition per ADR-0074 §1, before any activation or any non-synthetic document
- [medium] Dependency requalification: upgrade Docling to 2.132.0 or later (clears the 15 docling/docling-slim records and lifts the pillow<13 cap), take pillow 13.0.0 or later (clears 38 records), then repeat the S0001/S0005 provenance and qualification comparison with the new measured pins — owner: AI Engineer + DevOps; follow-up: activation precondition, before any activation or any non-synthetic document
- [low] SEC-F5-L4: bind the provider record to an operator-owned allowlist of the resolved executable (/proc/pid/exe and the vllm entry-point realpath), check listening-socket ownership at record time, restart with an explicit minimal environment, and create the provider log with mode 0600 — owner: DevOps; follow-up: before activation, together with SEC-F5-M1
- [low] SEC-F5-L5: on any wait_ready failure in quiesce_and_restart (provider_restart_unauthenticated, provider_restart_not_ready), terminate and confirm the restarted process group before re-raising, and add a test through quiesce_and_restart — owner: DevOps; follow-up: before activation
- [low] SEC-F5-L6: upgrade transitive litellm to 1.100.4 or later (GHSA-7hp6-4w63-5g45, proxy-only and not reachable here) and re-run the offline suite — owner: AI Engineer; follow-up: next neuron lock refresh, at the latest before activation
- [low] Pre-existing F0004 SEC-L2: add X-Content-Type-Options: nosniff and Cross-Origin-Resource-Policy headers to the engine API — owner: Backend; follow-up: F0026 security baseline
