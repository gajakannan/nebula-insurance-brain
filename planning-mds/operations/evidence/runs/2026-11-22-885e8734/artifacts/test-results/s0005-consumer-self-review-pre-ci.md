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
| Native compatibility | Seven actual old-reader and candidate-reader cases passed with byte-identical result JSON: `native-baseline-results.json`, `native-candidate-results.json`, `native-differential-comparison.txt`. Naive timestamps, malformed timestamp refusal, exact large integers and disabled/unknown versions retain their behavior. |
| Runtime integration | `consumer-integration.txt` / `.xml`: 81 passed, zero skipped, including current FactSlot-answer and temporal-read regressions. |
| Atomicity and source access | `test_f0011_consumer_contracts.py`: result-guard rollback, answer/temporal refusal, serialized-commit rollback of versions/changes/outbox, domain-reason precedence and denied-source-before-output-guard proof all passed. |
| History rollout | Both original signed `stored-versions-{integration,dev}.json` passed before response-guard activation. Both `stored-versions-{integration,dev}-cutover.json` passed after tests and current writer inventory. Every snapshot selected/checked all zero actual rows, with zero mapping/guard failures and explicit QE/DevOps zero-row signatures. |
| Nonempty stored-history proof | Owned PostgreSQL fixtures exercised six legacy/temporal versions, closed history, both remainder kinds, a serializer format fault and database-enforced READ ONLY refusal. No fixture/history rewrite was used by either real-environment sweep. |
| Lint | `consumer-lint-final.txt`: all checks passed across 16 assigned consumer/runtime/API/test/probe files. |
| Coverage | `artifacts/coverage/consumer.coverage` and `consumer.xml` record the 81-case run. `consumer-cli.coverage` records both real final CLI sweeps using the common branch/relative-file configuration; QE combines these with the other feature evidence. |

PR-L3 is observed by
`test_pr_l3_read_audit_precedes_safe_http_failure_and_denied_source_precedes_guard`:
an authorized read audit is `succeeded` before the generic delivery-invariant 500;
a denied source returns 404 without evaluating that output guard. The Backend
does not accept or waive that audit meaning. Its required disposition belongs
to the Security Reviewer at G3 before implementation approval.

The final candidate digest is `845d925d0766c7d0b691a2ee37408e8a5389d01740c9faf439835479cf585002`;
bundle digest is `054119f11aa89c39f7687968424b9e40c63bbceadaaee145790f5908ab927959`.
Any later guard, serializer, bundle or stored-population change requires fresh
history reports. No schema assertion, grant, route, migration or AI behavior was
added by this consumer slice.
