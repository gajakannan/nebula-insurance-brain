# F0011 S0005 — Consumer implementation self-review

Role: Backend Developer
Reviewer: Codex / Backend Developer
Date: 2026-11-22
Verdict: PASS (backend self-review)

Existing content/assertion loaders now delegate to the installed bundle while
retaining their native decoders, selectors and safe error classes. The content
planning-directory fallback is removed. FactSlot keys/results, canonical answers
and newly constructed temporal carriers are checked after existing domain,
ownership and evidence guards. Legacy pilot values/remainders retain their path.

POST serializes and checks its response inside the existing mutation operation,
before the outer transaction commits. GET checks output after all exact source
READ checks. Internal invariant failures return generic `contract_invariant_failed`
500 responses without input values or schema pointers. Application creation eagerly
loads both the complete installed bundle and its OpenAPI snapshot. The route
parity test enumerates FastAPI's actual lazy include contexts, including mounted
prefixes and the catch-all file route.

| Proof | Observed result / evidence |
|---|---|
| Resource adoption | G0 reconciled 21 resources and 68 existing/planned consumer/test mappings; `scripts/contracts/sources.yaml` retains the selectors/profiles/dispositions. |
| Native compatibility | Seven actual old-reader and candidate-reader cases passed again with byte-identical result JSON: `native-baseline-ci-results.json`, `native-candidate-ci-results.json`, `native-differential-ci-comparison.txt`. Naive timestamps, malformed timestamp refusal, exact large integers and disabled/unknown versions retain their behavior. |
| Runtime integration | `consumer-integration-ci.txt` / `.xml`: 81 passed, zero skipped in 44.00s, including current FactSlot-answer and temporal-read regressions. The earlier run remains historical evidence. |
| Atomicity and source access | `test_f0011_consumer_contracts.py`: result-guard rollback, answer/temporal refusal, serialized-commit rollback of versions/changes/outbox, domain-reason precedence and denied-source-before-output-guard proof all passed. |
| History rollout | Both original signed `stored-versions-{integration,dev}.json` passed before response-guard activation. Both `stored-versions-{integration,dev}-cutover-ci.json` passed after the repeated tests and fresh writer inventory. Earlier cutover reports are preserved. Every snapshot selected/checked all zero actual rows, with zero mapping/guard failures and explicit QE/DevOps zero-row signatures. |
| Nonempty stored-history proof | Owned PostgreSQL fixtures exercised six legacy/temporal versions, closed history, both remainder kinds, a serializer format fault and database-enforced READ ONLY refusal. No fixture/history rewrite was used by either real-environment sweep. |
| Lint | `consumer-lint-final.txt` preserves the earlier passing 16-file consumer check. The root owns the current static-check refresh after its typing/format corrections. |
| Coverage | `artifacts/coverage/consumer-ci.coverage` and `consumer-ci.xml` record the repeated 81-case run. `consumer-cli-ci.coverage` records both current real CLI sweeps using the common branch/relative-file configuration; QE combines the current source's coverage files. Earlier coverage remains historical. |

PR-L3 is observed by
`test_pr_l3_read_audit_precedes_safe_http_failure_and_denied_source_precedes_guard`:
an authorized read audit is `succeeded` before the generic delivery-invariant 500;
a denied source returns 404 without evaluating that output guard. The Backend
does not accept or waive that audit meaning. Its required disposition belongs
to the Security Reviewer at G3 before implementation approval.

Following static typing/format corrections, the bounded verification was repeated
without production source edits or findings. The fresh target client inventory
was READ ONLY with zero clients on both targets at 2026-11-23T00:06:51.146855+00:00;
see `artifacts/runtime/cutover-client-inventory-ci.json`. The final snapshots
completed at 00:07:21 and 00:07:23 UTC. The earlier self-review is preserved in
`s0005-consumer-self-review-pre-ci.md`.

The final candidate digest is `633d65c9de5ce9251c4bf974cc414479f78edee0f7e48c445869e49589beec22`;
bundle digest is `054119f11aa89c39f7687968424b9e40c63bbceadaaee145790f5908ab927959`.
Any later guard, serializer, bundle or stored-population change requires fresh
history reports. No schema assertion, grant, route, migration or AI behavior was
added by this consumer slice.
