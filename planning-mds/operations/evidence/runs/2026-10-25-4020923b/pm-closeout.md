# PM Closeout — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

Recorded by Claude in the Product Manager role, 2026-10-28, after the operator's G4 approval to close F0005 on the S0004-AC7 rejection branch.

Result: APPROVED WITH RECOMMENDATIONS

## Final Story Status

| Story | Status | Basis |
|---|---|---|
| F0005-S0001 Pin and process source documents | Done | AC1–AC6; S0001-AC2 met in round 2 (observed OCR page count and engine on every bundle) |
| F0005-S0002 Persist artifacts and recover jobs | Done | Live provider, storage, kill, competing-worker, revocation and cancellation lanes pass on final code |
| F0005-S0003 Reinterpret saved JSON and map evidence | Done | AC3 asserted live on 8 completed runs; AC4 proven deterministically |
| F0005-S0004 Evaluate and activate the proven pipeline | Done: evaluated and **rejected** | Graph dense missed 5 PRD thresholds (`report.json`, `void: false`); QA, Architect and Security verdicts recorded; operator rejection at G4; AC7 verified by `artifacts/test-results/post-decision-check.log`. AC5/AC6 activation branch not reachable, by design. |
| F0005-S0005 Qualify text origin and enable v2 publication | Done | AC1–AC4 met (11/13 documents fall back to v1, reported); AC5 not reachable because S0004 was rejected, so the v2 writer stays disabled |

## Archive Decision

Archive. F0005 is complete on its PRD-defined rejection branch, and every gate G0–G7 passed (G3 after a rework round). The feature folder moves to `planning-mds/features/archive/F0005-one-time-docling-ingestion`, and the feature shard becomes `archived-done`.

No activation happened and none is pending:
- the committed config stays `direct-baseline` with the v2 writer off;
- ADR-0060 stays Proposed, with failed gates and a reopen deadline (Rejected if no re-plan is approved by the start of F0014/F0015 planning);
- ADR-0074 is Accepted.

Nothing is committed to git; commit and push wait for the operator.

## Deferred Follow-ups

**Activation preconditions** (block any future Graph activation or non-synthetic documents):
- SEC-F5-M1 converter OS isolation;
- the Docling ≥ 2.132 / pillow ≥ 13 requalification;
- the SEC-F5-L4 residual (executable allowlist, minimal restart environment).

**Engineering follow-ups:**
- Queue-race orphan-source sweep (ADR-0074 known limitation). Owner: Backend; target F0026.
- ADR-0073 proof gate: an F0004 restore drill with OCR-bearing v1/v2 bundles before ADR-0073 acceptance. Owner: QE/DevOps.
- Pre-existing failures outside F0005, identical on clean HEAD. Owner: Backend; logged for triage.
  - 11 engine authx tests: `reconcile_authx.py` versus the F0004 ORM column.
  - `test_content_worker_v2[False]`: Docling merges fixture lines on this host.
- Pre-existing F0004 SEC-L2 response headers. Owner: Security; target F0026.

**Qualification process improvements**, for any re-plan (QA G3 findings):
- commit the corpus with its generation command;
- write `commands.log` at execution time;
- retain predicted values in the report;
- add a table-aware baseline;
- define the OCR-count semantics in the AC.

**Decision follow-up:** ADR-0060's reopen deadline is F0014/F0015 planning. Owner: Operator/PM.

## Recommendation Acceptances

All four G3 round-2 verdicts and the post-G4 delta review pass with recommendations; no Critical or High recommendation is open. Each recommendation from the Code Review and Security reports is accepted below with its disposition.

- Accepted: N1: enforce the two-launch limit before each conversion starts (`content_workflow.py:186`, `document_worker.py:241-250`) so two reason-less crashes cannot trigger a third conversion, and add a worker test — Fulfilled in this run: launch budget checked before each conversion (document_worker._start_conversion); verified by the delta review and live fault lanes.
- Accepted: L-N1: catch pypdf `PdfReadError`/`PdfStreamError` in `_count_pages_needing_ocr` and guard the `PdfReader` page count so damaged pages yield `partial`, not `conversion_failed` — Fulfilled: PyPdfError caught; unreadable structure degrades to a pdf_structure_unreadable warning (test_docling_adapter).
- Accepted: L-N2: convert any token-counter exception into a recorded `InferenceRejected("invalid_token_estimate")` (`vllm_graph_client.py:302`) — Fulfilled: token-counter failures are recorded token_count_failed rejections (test_vllm_graph_client).
- Accepted: L-N3: treat a stale or uncleared in-flight marker as a guard fault that stops the worker (`worker_guard.py:325-327`, `document_worker.py:68`) — Fulfilled: uncleared or leftover markers mark the guard uncertain and stop the worker (test_worker_guard).
- Accepted: L-N4: classify `usage_exceeds_reservation` as provider misconfiguration that stops the worker instead of a terminal per-job budget failure — Fulfilled: usage_exceeds_reservation stops the worker without failing the job (test_document_worker_reasons).
- Accepted: Round-1 L3/L5/L6 remain: add `boot_id` to the conversion launch receipts, add an orphan-source sweep for the queue-bound race, and tag key decisions with `# WHY:` — L3 fulfilled (boot_id in receipts, fail-closed when unreadable); L6 fulfilled (WHY tags, decisions regenerated at G7); L5 orphan-source sweep deferred as an ADR-0074 known limitation; owner: Backend; follow-up: F0026 job-admission hardening.
- Accepted: SEC-F5-M1: run the converter child with OS-level isolation: a separate unprivileged UID or container, no access to HOME, the control directory or the content store, no network, forced HF_HUB_OFFLINE, and a memory cap (RLIMIT_AS or cgroup) — Deferred as an activation precondition recorded in ADR-0074; owner: DevOps + Security; follow-up: before any Graph activation or non-synthetic document.
- Accepted: Dependency requalification: upgrade Docling to 2.132.0 or later (clears the 15 docling/docling-slim records and lifts the pillow<13 cap), take pillow 13.0.0 or later (clears 38 records), then repeat the S0001/S0005 provenance and qualification comparison with the new measured pins — Deferred as an activation precondition (Docling >= 2.132 / pillow >= 13 with full requalification); owner: AI Engineer + QE; follow-up: next qualification plan.
- Accepted: SEC-F5-L4: bind the provider record to an operator-owned allowlist of the resolved executable (/proc/pid/exe and the vllm entry-point realpath), check listening-socket ownership at record time, restart with an explicit minimal environment, and create the provider log with mode 0600 — Partly fulfilled (listener ownership at record, before signal and before credential on restart; log 0600); residual executable allowlist and minimal restart environment deferred as activation preconditions in ADR-0074; owner: DevOps; follow-up: before activation.
- Accepted: SEC-F5-L5: on any wait_ready failure in quiesce_and_restart (provider_restart_unauthenticated, provider_restart_not_ready), terminate and confirm the restarted process group before re-raising, and add a test through quiesce_and_restart — Fulfilled: refused restarts stop their process group and keep the refusal code (test_worker_guard; delta review verified).
- Accepted: SEC-F5-L6: upgrade transitive litellm to 1.100.4 or later (GHSA-7hp6-4w63-5g45, proxy-only and not reachable here) and re-run the offline suite — Fulfilled: litellm locked at 1.100.4 (artifacts/security/g2r3 dependency scan clean for litellm).
- Accepted: Pre-existing F0004 SEC-L2: add X-Content-Type-Options: nosniff and Cross-Origin-Resource-Policy headers to the engine API — Deferred (pre-existing, outside F0005 scope); owner: Security; follow-up: F0026 security baseline.

- QA and Architect qualification recommendations: the threshold, corpus and process findings are carried in Deferred Follow-ups. The ADR text fixes are fulfilled (ADR-0073 §6, ADR-0060 consistency and hashes, ADR-0074). G7 reconciliation is fulfilled (`kg-reconciliation.md`).
- Delta review D-1 to D-5: fulfilled in this run. D-1's regression (a hidden `model_timeout`) was caught live and fixed; the three fault lanes were re-run and pass.

- Accepted: F0005-S0001-Quality Engineer — QE recommendations accepted: test-assertion tightening fulfilled; qualification process improvements and the OCR-bearing restore drill carried in Deferred Follow-ups with named owners; source report and full verdict preserved.
- Accepted: F0005-S0001-Code Reviewer — Code Reviewer recommendations accepted: N1 and the Lows fulfilled and verified by the delta review; the orphan-source sweep deferred (ADR-0074 known limitation, owner Backend, F0026); source report and full verdict preserved.
- Accepted: F0005-S0001-Security Reviewer — Security recommendations accepted: L5 and L6 fulfilled and L4 partly fulfilled; SEC-F5-M1, the Docling/pillow requalification and the L4 residual retained as activation preconditions (owners DevOps/Security/AI); F0004 SEC-L2 deferred to F0026; source report and full verdict preserved.
- Accepted: F0005-S0001-DevOps — DevOps recommendations accepted: quiescence restarts use only the recorded command; the restart-environment and converter-isolation activation preconditions are owned by DevOps; source report and full verdict preserved.
- Accepted: F0005-S0001-Architect — Architect recommendations accepted: ADR-0074 accepted, ADR-0060/0073 text fixes and G7 reconciliation fulfilled; the ADR-0073 restore-drill proof gate and the ADR-0060 reopen deadline carried with owners; source report and full verdict preserved.
- Accepted: F0005-S0002-Quality Engineer — QE recommendations accepted: test-assertion tightening fulfilled; qualification process improvements and the OCR-bearing restore drill carried in Deferred Follow-ups with named owners; source report and full verdict preserved.
- Accepted: F0005-S0002-Code Reviewer — Code Reviewer recommendations accepted: N1 and the Lows fulfilled and verified by the delta review; the orphan-source sweep deferred (ADR-0074 known limitation, owner Backend, F0026); source report and full verdict preserved.
- Accepted: F0005-S0002-Security Reviewer — Security recommendations accepted: L5 and L6 fulfilled and L4 partly fulfilled; SEC-F5-M1, the Docling/pillow requalification and the L4 residual retained as activation preconditions (owners DevOps/Security/AI); F0004 SEC-L2 deferred to F0026; source report and full verdict preserved.
- Accepted: F0005-S0002-DevOps — DevOps recommendations accepted: quiescence restarts use only the recorded command; the restart-environment and converter-isolation activation preconditions are owned by DevOps; source report and full verdict preserved.
- Accepted: F0005-S0002-Architect — Architect recommendations accepted: ADR-0074 accepted, ADR-0060/0073 text fixes and G7 reconciliation fulfilled; the ADR-0073 restore-drill proof gate and the ADR-0060 reopen deadline carried with owners; source report and full verdict preserved.
- Accepted: F0005-S0003-Quality Engineer — QE recommendations accepted: test-assertion tightening fulfilled; qualification process improvements and the OCR-bearing restore drill carried in Deferred Follow-ups with named owners; source report and full verdict preserved.
- Accepted: F0005-S0003-Code Reviewer — Code Reviewer recommendations accepted: N1 and the Lows fulfilled and verified by the delta review; the orphan-source sweep deferred (ADR-0074 known limitation, owner Backend, F0026); source report and full verdict preserved.
- Accepted: F0005-S0003-Security Reviewer — Security recommendations accepted: L5 and L6 fulfilled and L4 partly fulfilled; SEC-F5-M1, the Docling/pillow requalification and the L4 residual retained as activation preconditions (owners DevOps/Security/AI); F0004 SEC-L2 deferred to F0026; source report and full verdict preserved.
- Accepted: F0005-S0003-DevOps — DevOps recommendations accepted: quiescence restarts use only the recorded command; the restart-environment and converter-isolation activation preconditions are owned by DevOps; source report and full verdict preserved.
- Accepted: F0005-S0003-Architect — Architect recommendations accepted: ADR-0074 accepted, ADR-0060/0073 text fixes and G7 reconciliation fulfilled; the ADR-0073 restore-drill proof gate and the ADR-0060 reopen deadline carried with owners; source report and full verdict preserved.
- Accepted: F0005-S0004-Quality Engineer — QE recommendations accepted: test-assertion tightening fulfilled; qualification process improvements and the OCR-bearing restore drill carried in Deferred Follow-ups with named owners; source report and full verdict preserved.
- Accepted: F0005-S0004-Code Reviewer — Code Reviewer recommendations accepted: N1 and the Lows fulfilled and verified by the delta review; the orphan-source sweep deferred (ADR-0074 known limitation, owner Backend, F0026); source report and full verdict preserved.
- Accepted: F0005-S0004-Security Reviewer — Security recommendations accepted: L5 and L6 fulfilled and L4 partly fulfilled; SEC-F5-M1, the Docling/pillow requalification and the L4 residual retained as activation preconditions (owners DevOps/Security/AI); F0004 SEC-L2 deferred to F0026; source report and full verdict preserved.
- Accepted: F0005-S0004-DevOps — DevOps recommendations accepted: quiescence restarts use only the recorded command; the restart-environment and converter-isolation activation preconditions are owned by DevOps; source report and full verdict preserved.
- Accepted: F0005-S0004-Architect — Architect recommendations accepted: ADR-0074 accepted, ADR-0060/0073 text fixes and G7 reconciliation fulfilled; the ADR-0073 restore-drill proof gate and the ADR-0060 reopen deadline carried with owners; source report and full verdict preserved.
- Accepted: F0005-S0005-Quality Engineer — QE recommendations accepted: test-assertion tightening fulfilled; qualification process improvements and the OCR-bearing restore drill carried in Deferred Follow-ups with named owners; source report and full verdict preserved.
- Accepted: F0005-S0005-Code Reviewer — Code Reviewer recommendations accepted: N1 and the Lows fulfilled and verified by the delta review; the orphan-source sweep deferred (ADR-0074 known limitation, owner Backend, F0026); source report and full verdict preserved.
- Accepted: F0005-S0005-Security Reviewer — Security recommendations accepted: L5 and L6 fulfilled and L4 partly fulfilled; SEC-F5-M1, the Docling/pillow requalification and the L4 residual retained as activation preconditions (owners DevOps/Security/AI); F0004 SEC-L2 deferred to F0026; source report and full verdict preserved.
- Accepted: F0005-S0005-DevOps — DevOps recommendations accepted: quiescence restarts use only the recorded command; the restart-environment and converter-isolation activation preconditions are owned by DevOps; source report and full verdict preserved.
- Accepted: F0005-S0005-Architect — Architect recommendations accepted: ADR-0074 accepted, ADR-0060/0073 text fixes and G7 reconciliation fulfilled; the ADR-0073 restore-drill proof gate and the ADR-0060 reopen deadline carried with owners; source report and full verdict preserved.

**Disclosure:** at closeout, the PM's wording request for the SEC-F5-M1 recommendation (" — " to ": ", needed for this acceptance matching) was handled by the round-1 Security session rather than the round-2 author. The change is punctuation only; the verdict and content are unchanged.

## Tracker Updates

- `planning-mds/features/F0005-one-time-docling-ingestion/STATUS.md` (archived path after the move):
  - Overall Status Done (rejection branch);
  - stories Done;
  - Story × Role matrix all done/PASS;
  - current signoff and review history recorded.
- `planning-mds/kg-source/features/F0005.yaml`:
  - `status: archived-done`, archive `path`, `registry_section: Archived`, `roadmap_section: Completed`;
  - `governed_by` += `adr:0074`;
  - notes replaced with the closeout state.
- REGISTRY/ROADMAP tracker regions are regenerated by `compile.py`.
- BLUEPRINT and C4 are unchanged (nothing activated).
- SOLUTION-PATTERNS and DEPENDENCY-MATRIX were updated at G7.

## Validator Results

See `gate-decisions.md` (G0–G8) and `lifecycle-gates.log`. Closeout runs `run-gate.py --stage G8`:
- compile;
- the prior-manifest patch;
- `latest-run.json`, written by the gate after final validation;
- coverage report;
- drift;
- telemetry;
- `validate-feature-evidence --stage closeout`;
- `validate-trackers`;
- `validate.py`.

Results are recorded in the G8 row.
