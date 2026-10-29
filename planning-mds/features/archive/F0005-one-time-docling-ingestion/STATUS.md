# F0005 — One-time document ingestion — Status

**Overall Status:** Done — closed on the S0004-AC7 rejection branch (2026-10-28). Graph dense was qualified live on the synthetic corpus and rejected (5 PRD thresholds missed); `direct-baseline` with the v1 writer stays the committed default. The shipped execution controls are governed by the Accepted ADR-0074; ADR-0060 stays Proposed with failed gates recorded and a reopen deadline.\
**Last Updated:** 2026-10-28\
**Plan Run:** `2026-10-25-50fcf658` (Phase B, existing feature, approved 2026-10-25; follows `2026-10-23-9a04b327`)

## Current Feature Action Run

Feature-completion run `2026-10-25-4020923b` **closed 2026-10-28** (G0–G8). Gate history:
- G3 round 1 rejected the code (C1, H1). The rework passed G2/G3 round 2 with fresh independent reviews.
- At G4 the operator approved the rejection branch. N1, L5 and the Lows were fixed and verified by an independent delta review and the final live lanes; ADR-0074 was then Accepted.
- The post-decision check passed: the committed config processes an ordinary source on `direct-baseline` with a v1 bundle and no Graph call.

Evidence: `planning-mds/operations/evidence/runs/2026-10-25-4020923b/` (see `pm-closeout.md`).

## Planning Position

Plan run `2026-10-23-9a04b327` re-planned the remaining work against shipped F0002–F0004. Operator decisions at G1 (2026-10-23): local live qualification on the development host with gated activation; a synthetic qualification corpus with independent expectations and independent agent-role reviewers; F0005 enables the F0004 v2 writer as an activation step (new story S0005); F0016 owns document-date candidates. The PRD fixes the qualification thresholds. Phase A was approved with `approve-phase-a` and the preceding Phase B with `approve-phase-b` on 2026-10-23.

[Plan review `2026-10-24-0fbc1de1`](../../../operations/evidence/runs/2026-10-24-0fbc1de1/plan-review-report.md) found three high gaps. The operator requested plan-action repairs; run `2026-10-25-50fcf658` is Phase B for this existing feature. Its [assembly plan](feature-assembly-plan.md) addresses PM-1 with initial/rejection direct-baseline settings and isolated candidate configs, ARCH-1 with supervised conversion and a parent-owned 300-second outcome/publication fence, and BLD-1 with an enforced host singleton plus confirmed provider quiescence after uncertain requests. The new negative proof inventory covers restart/rejection, hung/late conversion, process-group cleanup, two-process refusal and in-flight SIGKILL/timeout recovery. Requirements, stories and thresholds are unchanged. The operator explicitly approved this revised Phase B design on 2026-10-25 with the response `approve`; gate and publication results are recorded in the current run. The approved design is ready for the feature action, starting with preflight. Historical plan/review evidence is preserved. Planning does not authorize implementation or change delivery priority.

## Synthetic development scope (2026-09-20 to 2026-09-22)

The authorized scope uses synthetic development fixtures. Architecture/article reconciliation, the pinned Graph integration, durable recovery, bounded transport, evidence mapping, and a reproducible recorded-response comparison are delivered. This is the completion boundary for the current development work. The production proof gates below remain release requirements, not prerequisites for completing this scope.

The comparison runs the direct baseline, Graph direct, and Graph dense over three synthetic cases. All nine retain the saved native JSON without conversion. Dense performs skeleton/fill requests across multiple chunks and passes the unique, ambiguous, and multi-region evidence expectations. The historical baseline chooses a first match for repeated values; Graph direct lacks usable item refs on these longer fixtures and remains unresolved. These are observed development limitations, not measured model quality. The worker's current direct default remains opt-in.

Multi-region text now requires continuous source coverage and preserves separate selectors through assertion import, review-item creation, and region selection in the Review Panel. Mixed or incomplete evidence remains unresolved. The mapper version is 2. Dense legacy-mode hints retain Nebula's schema-enforced transport and validation.

## Candidate runtime delivery — 2026-09-20

The candidate has been merged to main from `feature/docling-graph-delivery`, based on `a60350d`. It remains opt-in; it does not replace the accepted F0001 baseline or imply release acceptance.

- `CheckpointStore` verifies scope, inventory, source/native and bundle hashes. Manifest-last publication supports identical retries. Missing files in a published bundle or run are integrity failures, never cache misses that trigger re-parsing. Filesystem writes use private temporary files, fsync, and atomic publication.
- `DocumentJobQueue` and migration 0004 provide artifact leases, generations, heartbeats, scoped idempotency, cancellation, finite retries, event history, and a completion outbox. PostgreSQL fences use the current database clock after lock acquisition. Four PostgreSQL queue tests cover competing claims, expired-generation fencing, child-process exit/reclaim after checkpoint publication, and lease expiry during a row-lock wait. Five additional cases now prove worker/importer recovery at the boundaries described below; infrastructure and live-provider failure recovery remain open.
- `DocumentWorker` performs conversion/checkpoint publication, saved-JSON interpretation, fenced output publication, and recovery of a successful prior attempt. Jobs pin profile version and schema hash. Artifact metadata is registered before model extraction, so model failure leaves the content available to authorized engine readers. A real process-exit test recovers published output without a conversion or model call.
- `DocumentJobAuthorization` re-reads active principal status, unrevoked grants, and Casbin policy at sensitive boundaries; decisions are audited. Only the existing `ServicePrincipal` role receives the new `ingest` and `interpret` grants. The CLI is a trusted-operator interface, not an unauthenticated public upload endpoint.
- `DocumentResultImporter` atomically inserts source/artifact metadata, the interpretation run, assertions, evidence, review items, and an outbox acknowledgement. An injected review insertion failure rolls back the entire import; retry creates one set of rows. Unresolved evidence remains unresolved and enters provenance review. No canonical fact is accepted by this importer. Entity/relationship output is rejected until its downstream mapping exists.
- The shared DTO lives in `engine/packages/brain-contracts`; the old neuron import remains compatible. Parser, pipeline, model, template, limits, and run-owned provenance metadata remain distinct. Unique native text and table-cell locations are supported; ambiguous or normalized values are unresolved.
- `python -m brain_ingestion.worker_cli` provides opt-in submission, worker, and import-only commands. Both dependency locks resolve and both runtime environments sync offline.

**Verification:** the combined runtime suite passed **80 tests**, with **5 live tests skipped** (two PostgreSQL and three model-service checks). This is local compatibility evidence, not live extraction quality or PostgreSQL concurrency evidence. See [compatibility evidence](compatibility-evidence.md) and [run instructions](GETTING-STARTED.md).

**Remote CI:** [run 35589532922](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35589532922) passed all five jobs on `4712811`: engine **126 passed / 21 skipped**, neuron **63 passed / 9 skipped**, PostgreSQL queue proof **4 passed**, and PostgreSQL worker/importer recovery **5 passed**. The general suites skip unavailable live services; the dedicated database job supplies PostgreSQL and executes all nine database proof cases. All configured coverage, lint/type, frontend, planning, and framework gates passed, along with OIDC discovery and the seeded principals.

**Worker/importer recovery — 2026-09-21:** real child processes exit after bundle publication, extraction-result publication, job completion, midway through result import, and after import commits. Every case recovers with one conversion, one recorded model call, one assertion/evidence/review set, and one acknowledged completion. The importer rollback case leaves no partial assertion or run. These tests run real Graph stages and authorization with synthetic native content and recorded HTTP responses; they do not exercise a physical parser, live provider, or infrastructure failure.

**Earlier CI failure:** [run 35535414661](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35535414661) on `a64f0eb` passed all four database cases, then failed at OIDC application readiness. CI now bounds each HTTP request, allows 180 seconds for application readiness, and captures stack diagnostics on failure. The subsequent successful run `35552348580` observed one 404 followed by a 200; the earlier failure's cause remains unconfirmed because its logs were not retained.

**Remaining before activation:** qualify live-provider and deployment/storage failures; compare live Graph chunking with the direct baseline on independently expected, approved corpus cases; qualify serving-tokenizer parity, deployment concurrency, credentials/logs, retention/deletion, and property/relationship evidence including multi-region cases; record the required reviewer verdicts. The current worker supports fixed GL templates. Production compilation (F0015), full run lifecycle (F0016), relationship semantics and affected-content evolution (F0032) remain their planned feature scopes, not delivered by this candidate. Targeted requests explicitly fail rather than broadening to full-document extraction. ADR-0060 remains Proposed.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | Done |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | Done |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | Done |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | Done — evaluated and rejected (S0004-AC7) |
| [F0005-S0005](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) | Qualify text origin and enable v2 publication | Done |

## Recommendation Audit

| Recommendation | Planning state | Delivery / proof still required |
|---|---|---|
| New orchestration ADR | ADR-0060 Proposed; acceptance gates explicit | Complete all four proof gates and obtain actual reviewer verdicts |
| Existing ADR invariants | Dated links preserve ADR-0003/0004/0040/0055/0058/0059 and F0001 results; bounded artifact/reuse/evidence tests pass | Complete production qualification against those contracts |
| Consistent blueprints, C4, article | Proposed target distinguished from current runtime | Update actual runtime descriptions after activation |
| Artifact and run identity | F0004/F0016 specify separate parser/pipeline/recipe/profile metadata and run-owned provenance | Shared result DTO and candidate persistence implemented; full F0016 lifecycle remains planned |
| F0004/F0005 feature planning | Neutral F0005 title; four stories; F0004 dependency explicit; synthetic development scope delivered | Remaining production qualification and signoffs for S0001–S0004 |
| Profiles and interpretation | F0014/F0015/F0016 scope updated | Compiler and production run service implementation |
| Targeted evolution | F0032 now owns affected-content-only scheduling proof | Demonstrate bounded input, original refs, zero reparse |
| Review and release | F0022/F0026 cases specified; synthetic multi-region evidence survives import and Review Panel decisions | Live property/relationship evidence qualification and measured corpus results |
| Runtime, dependency lock, misleading adapter name | Candidate adapter, shared ParseResult, explicit direct baseline, pyproject/uv.lock pin, package/schema/input metadata implemented and tested | Candidate composition, metadata, scalar evidence and durable services implemented; full proof and activation pending |
| Full-document versus chunked extraction | Nine recorded-response runs compare the direct baseline, Graph direct, and Graph dense; schema, abstention, evidence, and zero-conversion expectations checked | Live quality/cost/latency/review measurements; synthetic token estimates and timing are not serving measurements |
| Local inference and operations | Bounded SDK client implemented; 23 offline tests cover budgets, cancellation, shared concurrency, errors, redacted diagnostics, and cached serving tokenizer | Live serving parity, deployment replica limits, credential/log and retention review, and operational qualification |
| Temporal and archive | v0.1 jobs / v0.3 Temporal retained; F0001 unchanged | No architecture replacement or reopened archive required |

## Proof Gates

- [ ] Exact-version native/scanned conversion, checkpoint, restart, and saved-JSON reuse.
- [ ] Insurer-critical property/relationship evidence, table and multi-region cases.
- [ ] Corpus comparison and timeout/partial/invalid-output/retry/restart cases.
- [ ] Local vLLM, secrets, concurrency, tenant access, and retention.
- [ ] Activation prerequisite added 2026-09-25 (validate finding A-4). Before S0004 activates the candidate pipeline, published blocks carry `text_origin` (`STATED`, `OCR`, `TRANSCRIBED`, `DESCRIBED`) and the producing engine, and the evidence mapping locates quotes on the server under the ADR-0065 admission contract. The alternative is a recorded deferral of both to F0004/F0016 with rationale. F0004 delivered the text-origin storage and fallback; plan run `2026-10-23-9a04b327` assigns the live qualification and switch to S0005. See [ADR-0065](../../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) and [validate run 2026-09-25-463eecdd](../../../operations/evidence/runs/2026-09-25-463eecdd/architect-validation-report.md).

## Required Role Matrix

| Role | Required | Rationale |
|---|---|---|
| Quality Engineer | Yes | Baseline feature signoff; independently reviews corpus results and story acceptance evidence. |
| Code Reviewer | Yes | Baseline feature signoff; independently reviews the implementation and decision branches. |
| Security Reviewer | Yes | Reviews authorization, provider egress, credentials, logs, tenant access, and retention boundaries. |
| DevOps | Yes | Reviews runtime preflight, host singleton, provider recovery, subprocess cleanup, and migration/restore/serving evidence. |
| Architect | Yes | Reviews the approved checkpoint/deadline design, architecture invariants, and G7 knowledge-graph reconciliation. |

Every story requires all five roles above. Named reviewers and runtime verdicts remain pending. The separate QA/Architect/Security qualification verdicts and operator decision gate activation; they do not replace the per-story signoff set.

## Story x Role Progress

| Story | Backend | Frontend | AI | QA | DevOps | Code Review | Security | Overall |
|---|---|---|---|---|---|---|---|---|
| F0005-S0001 | done | not-in-scope | done | done | done | PASS | PASS | done |
| F0005-S0002 | done | not-in-scope | done | done | done | PASS | PASS | done |
| F0005-S0003 | done | not-in-scope | done | done | done | PASS | PASS | done |
| F0005-S0004 | done | not-in-scope | done | done | done | PASS | PASS | done |
| F0005-S0005 | done | not-in-scope | done | done | done | PASS | PASS | done |

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0005-S0001 | Quality Engineer | Claude (Quality Engineer role) | PASS | `test-execution-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0001 | Code Reviewer | Independent code-review session (G3 round 2) + delta review | APPROVED | `code-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0001 | Security Reviewer | Independent security session (G3 round 2) + delta review | PASS | `security-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0001 | DevOps | Claude (DevOps role) | PASS | `deployability-check.md` | 2026-10-28 | G5 signoff |
| F0005-S0001 | Architect | Independent Architect session (G3 round 2) | PASS | `architect-qualification-verdict.md` | 2026-10-28 | G5 signoff |
| F0005-S0002 | Quality Engineer | Claude (Quality Engineer role) | PASS | `test-execution-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0002 | Code Reviewer | Independent code-review session (G3 round 2) + delta review | APPROVED | `code-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0002 | Security Reviewer | Independent security session (G3 round 2) + delta review | PASS | `security-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0002 | DevOps | Claude (DevOps role) | PASS | `deployability-check.md` | 2026-10-28 | G5 signoff |
| F0005-S0002 | Architect | Independent Architect session (G3 round 2) | PASS | `architect-qualification-verdict.md` | 2026-10-28 | G5 signoff |
| F0005-S0003 | Quality Engineer | Claude (Quality Engineer role) | PASS | `test-execution-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0003 | Code Reviewer | Independent code-review session (G3 round 2) + delta review | APPROVED | `code-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0003 | Security Reviewer | Independent security session (G3 round 2) + delta review | PASS | `security-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0003 | DevOps | Claude (DevOps role) | PASS | `deployability-check.md` | 2026-10-28 | G5 signoff |
| F0005-S0003 | Architect | Independent Architect session (G3 round 2) | PASS | `architect-qualification-verdict.md` | 2026-10-28 | G5 signoff |
| F0005-S0004 | Quality Engineer | Claude (Quality Engineer role) | PASS | `test-execution-report.md` | 2026-10-28 | G5 signoff; evaluated and rejected (S0004-AC7) |
| F0005-S0004 | Code Reviewer | Independent code-review session (G3 round 2) + delta review | APPROVED | `code-review-report.md` | 2026-10-28 | G5 signoff; evaluated and rejected (S0004-AC7) |
| F0005-S0004 | Security Reviewer | Independent security session (G3 round 2) + delta review | PASS | `security-review-report.md` | 2026-10-28 | G5 signoff; evaluated and rejected (S0004-AC7) |
| F0005-S0004 | DevOps | Claude (DevOps role) | PASS | `deployability-check.md` | 2026-10-28 | G5 signoff; evaluated and rejected (S0004-AC7) |
| F0005-S0004 | Architect | Independent Architect session (G3 round 2) | PASS | `architect-qualification-verdict.md` | 2026-10-28 | G5 signoff; evaluated and rejected (S0004-AC7) |
| F0005-S0005 | Quality Engineer | Claude (Quality Engineer role) | PASS | `test-execution-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0005 | Code Reviewer | Independent code-review session (G3 round 2) + delta review | APPROVED | `code-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0005 | Security Reviewer | Independent security session (G3 round 2) + delta review | PASS | `security-review-report.md` | 2026-10-28 | G5 signoff |
| F0005-S0005 | DevOps | Claude (DevOps role) | PASS | `deployability-check.md` | 2026-10-28 | G5 signoff |
| F0005-S0005 | Architect | Independent Architect session (G3 round 2) | PASS | `architect-qualification-verdict.md` | 2026-10-28 | G5 signoff |

Current signoff (G5, 2026-10-28) per `signoff-ledger.md`. Every role verdict carries recommendations, which are accepted in `pm-closeout.md`. Earlier review verdicts are in the history table below.

## Review Verdict History

| Story | Review | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0005-S0001 | Code Review | Independent code-review session | FAIL | `code-review-report-round1.md` | 2026-10-26 | C1: OCR page count / v1 OCR engine not recorded (S0001-AC2) |
| F0005-S0002 | Code Review | Independent code-review session | PASS | `code-review-report-round1.md` | 2026-10-26 | M1–M4 recommended |
| F0005-S0003 | Code Review | Independent code-review session | PASS | `code-review-report-round1.md` | 2026-10-26 | H1 must be fixed before any Graph-dense re-measurement |
| F0005-S0004 | Code Review | Independent code-review session | PASS | `code-review-report-round1.md` | 2026-10-26 | code scope; AC4/AC7 pending operator |
| F0005-S0005 | Code Review | Independent code-review session | PASS | `code-review-report-round1.md` | 2026-10-26 | |
| F0005-S0001 | Security | Independent security session | PASS | `security-review-report-round1.md` | 2026-10-26 | PASS WITH RECOMMENDATIONS; SEC-F5-M1 before any activation or real documents |
| F0005-S0002 | Security | Independent security session | PASS | `security-review-report-round1.md` | 2026-10-26 | PASS WITH RECOMMENDATIONS; SEC-F5-M1 before any activation or real documents |
| F0005-S0003 | Security | Independent security session | PASS | `security-review-report-round1.md` | 2026-10-26 | PASS WITH RECOMMENDATIONS; SEC-F5-M1 before any activation or real documents |
| F0005-S0004 | Security | Independent security session | PASS | `security-review-report-round1.md` | 2026-10-26 | PASS WITH RECOMMENDATIONS; SEC-F5-M1 before any activation or real documents |
| F0005-S0005 | Security | Independent security session | PASS | `security-review-report-round1.md` | 2026-10-26 | PASS WITH RECOMMENDATIONS; SEC-F5-M1 before any activation or real documents |
| F0005-S0004 | QA qualification (AC4) | Independent QA session | PASS WITH RECOMMENDATIONS | `qa-qualification-verdict-round1.md` | 2026-10-26 | Thresholds recomputed; rejection is the only permitted outcome; S0003-AC4/AC3 not proven; kill lane stale |
| F0005-S0004 | Architect qualification (AC4) | Independent Architect session | PASS WITH RECOMMENDATIONS | `architect-qualification-verdict-round1.md` | 2026-10-26 | Recommends ADR-0060 stays Proposed with failed gates and a reopen deadline; new ADR for shipped controls |
| F0005-S0004 | Security qualification (AC4) | Independent security session | PASS WITH RECOMMENDATIONS | `security-review-report-round1.md` | 2026-10-26 | Supports the operator decision |
| F0005-S0001 | Code Review (round 2) | Independent code-review session | PASS | `code-review-report.md` | 2026-10-28 | C1 closed |
| F0005-S0002 | Code Review (round 2) | Independent code-review session | PASS | `code-review-report.md` | 2026-10-28 | N1 (two-fault reconvert) recommended |
| F0005-S0003 | Code Review (round 2) | Independent code-review session | PASS | `code-review-report.md` | 2026-10-28 | H1 closed |
| F0005-S0004 | Code Review (round 2) | Independent code-review session | PASS | `code-review-report.md` | 2026-10-28 | code scope; AC4/AC7 pending operator |
| F0005-S0005 | Code Review (round 2) | Independent code-review session | PASS | `code-review-report.md` | 2026-10-28 |  |
| F0005-S0001 | Security (round 2) | Independent security session | PASS | `security-review-report.md` | 2026-10-28 | PASS WITH RECOMMENDATIONS; L4/L5 and M1 before activation |
| F0005-S0002 | Security (round 2) | Independent security session | PASS | `security-review-report.md` | 2026-10-28 | PASS WITH RECOMMENDATIONS; L4/L5 and M1 before activation |
| F0005-S0003 | Security (round 2) | Independent security session | PASS | `security-review-report.md` | 2026-10-28 | PASS WITH RECOMMENDATIONS; L4/L5 and M1 before activation |
| F0005-S0004 | Security (round 2) | Independent security session | PASS | `security-review-report.md` | 2026-10-28 | PASS WITH RECOMMENDATIONS; L4/L5 and M1 before activation |
| F0005-S0005 | Security (round 2) | Independent security session | PASS | `security-review-report.md` | 2026-10-28 | PASS WITH RECOMMENDATIONS; L4/L5 and M1 before activation |
| F0005-S0004 | QA qualification (AC4, round 2) | Independent QA session | PASS WITH RECOMMENDATIONS | `qa-qualification-verdict.md` | 2026-10-28 | 5 thresholds missed; rejection only |
| F0005-S0004 | Architect qualification (AC4, round 2) | Independent Architect session | PASS WITH RECOMMENDATIONS | `architect-qualification-verdict.md` | 2026-10-28 | ADR-0074 ready; ADR-0060 Proposed |
| F0005-S0004 | Security qualification (AC4, round 2) | Independent security session | PASS WITH RECOMMENDATIONS | `security-review-report.md` | 2026-10-28 | Supports the rejection decision |

Round 1 (2026-10-26): Code Review REJECTED (C1, H1), which led to the round-2 rework. Round 2 (2026-10-28): all verdicts pass. A post-G4 delta review (`delta-review-report.md`) APPROVED WITH RECOMMENDATIONS.
