# Evaluation Strategy — Golden Corpus, Metrics, Regression, Release Gates

**Status:** Baseline index (extracted from the master blueprint on 2026-09-05); the quality-engineer role expands this into per-feature test plans.

**Retrieval amendment:** 2026-11-06; the protocol below is a planning input, with thresholds and feature approvals still pending.

This document points at the authoritative sections of `../architecture/master-blueprint.md` and records the rules that every test plan inherits.

## Golden Corpus (section 96)

- Start with 20 to 30 labeled insurance documents across the listed categories; concentrate initial labeling on GL policy packages and endorsements per section 115.1.
- The Nebula Review Panel is the primary labeling and correction environment (ADR-0057); ground-truth creation and production correction produce the same records. The export (source identity, evidence locators, expected assertions, relationships, canonical result, reviewer metadata) is what becomes version-controlled fixtures under `golden-corpus/`.
- Separate development and tuning examples from a frozen holdout. Split by related account, policy package, and template family so near-duplicate renewals or endorsements do not leak across sets.
- Production corrections enter a governed candidate benchmark pool; they never silently alter the holdout or expected answers.
- Add a small property and casualty loss-run contrast set to test schema extensibility; do not treat it as certification of those lines of business.

## Evaluation metrics (section 97)

Report sample sizes and uncertainty for every measured metric; never a single aggregate accuracy score that hides financially material mistakes. The metric list in section 97 spans classification, entity and fact precision and recall, qualifier, relationship, interpretation-basis, provenance, evidence-region, temporal, entity-resolution, conflict, reinterpretation-delta, citation, learning-candidate, review-agreement, review round-trip, and evidence-anchor resolution accuracy.

## Regression suites (section 98)

Section 98 enumerates the required regression cases. The framework `test` action and each feature's `test-plan.md` cite the cases they cover by name; ontology, temporal, review, evidence-anchoring, and authorization-leakage cases are mandatory once the corresponding feature ships.

## Release gates (section 115.2)

| Gate | Evidence required before release |
| --- | --- |
| Extraction reuse | Reinterpretation canary adds a field with zero physical conversion or OCR calls |
| Typed fact correctness | Critical accepted facts include value, unit or currency, qualifier, policy scope, and source support |
| Evidence fidelity | All displayed citations resolve to the correct immutable source and declared precision |
| Temporal integrity | Retroactive, interval-split, concurrent-commit, and recorded-time cases pass |
| Review integrity | Duplicate and stale review cases preserve lineage and cannot bypass approval policy |
| Authorization | No unauthorized content in the isolation, revocation, graph, vector, export, and chat suite |
| Ingestion recovery | Retry and crash cases recover without duplicate accepted effects |
| Unknown and conflict handling | Missing package, missing value, explicit negative, and source-conflict cases produce distinct outcomes |
| Learning containment | Repetition adds no independent evidence; unsupported candidates do not auto-promote |
| Projection recovery | Rebuild and lag scenarios preserve accurate canonical reads and authorized retrieval |
| Restore | A timed restore recovers evidence, identity, history, and access and deletion policies |
| Measured quality | Field precision and recall, severe-error rate, abstention, review workload, latency, and cost meet agreed targets on the frozen slice |

These are proposed pilot gates. Numeric targets require baseline measurement and named owners (sections 114.2, 117.1).

## AuthX carryover test matrix (section 121.2)

The required carryover tests for identity verification, policy parity, parent and classification conjunction, scope resolution, session behavior, and Neuron ownership predicates are listed in section 121.2 and are mandatory for F0002, F0018, F0021, F0022, and F0026.

## Framework evidence contract

Every feature run records `test-plan.md`, `test-execution-report.md`, and `coverage-report.md` under `operations/evidence/runs/{RUN_ID}/`. The coverage floor and the four required security scan classes come from the framework action policy, not from this document.

## v0.1 bounded neurosymbolic assessment (F0065)

F0024 must run actual neural interpretation through evidence review/canonical acceptance and the bounded rule; a mocked model or hand-authored expected assessment alone is insufficient. F0025 checks the exact temporal coordinates after correction and late endorsement. F0026 maps [EX-GL-001 CASE-01–19](../examples/neurosymbolic-gl/cases.md) to observed runtime evidence, including decimal boundaries, unsupported rules, absent/unaccepted inputs, conflicts, basis/currency mismatch, idempotency, concurrency, changed rule releases, and derived-result revocation.

Report model extraction correctness and severe errors separately from deterministic rule correctness, abstention, review workload, end-to-end result accuracy, latency, and cost. Expected outcomes are authored independently of the evaluator. Quality thresholds, sample sizes, corpus licensing, and named reviewers must be settled before the v0.1 release gate.

Worked examples are development/documentation fixtures and remain outside the frozen holdout. Require definition/example/boundary/contract/story links for new concepts, local schema/reference validation for structured examples, and actual runnable reproduction instructions when the corresponding runtime ships. A structural example check supplies no measured model performance or runtime proof.

## Docling-Graph integration gate (ADR-0060, Rejected 2026-11-08)

> **Rejected 2026-11-08.** The operator rejected [ADR-0060](../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) after Graph dense failed F0005 live qualification. The v0.1 pipeline is Docling conversion plus the direct-baseline extraction client (ADR-0055) under the ADR-0074 controls. The text below is kept as history; master blueprint section 126 lists what survives.

F0005 must exercise the real pinned upstream package and local model. F0001's direct-client proof is the historical comparison, not evidence that the new pipeline passes. F0026 carries these checks into release qualification:

- Convert native and scanned fixtures; publish native JSON and the normalized bundle before semantic extraction. Force model failure and worker restart after publication, then recover without conversion/OCR. Also cover failure before publication and incomplete-bundle cleanup.
- Interpret each saved artifact under two profiles; instrument actual converter/OCR entry points to fail if invoked. Check artifact hashes and selected-block scope. Do not rely solely on adapter-reported zero counters.
- Resolve property and relationship evidence independently of node identity. Exercise repeated values, Unicode offsets, chunk/block boundaries, table references, geometry conversion, coarse/document grounding, and synthetic/merged nodes.
- Enforce schema/prompt/input/output budgets before every upstream model call. Record complete/partial/failed outcomes, retries, tokens, latency, and cost without logging protected content.
- Exercise duplicate jobs, expired leases, cancellation, unauthorized artifacts/run outputs, and idempotent canonical effects. Prove that extraction graph exports cannot bypass review or write canonical/AGE state.
- Compare against independently labeled expectations on the frozen slice. Record extraction errors, evidence precision, unresolved rate, and review burden separately; do not infer improvement from fewer lines of adapter code.

Persist the exact upstream revision/package digest, dependency lock, model configuration, and observed results in the dependency matrix/evidence run. Activation requires the conversion checkpoint and reuse gates in [ADR-0060](../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md).

Additional ADR-0060 acceptance cases: limit amount, currency, basis, effective date, table headers, and multi-region support; invalid extraction after successful conversion; partial-conversion quality/warnings; secrets redaction; bounded concurrency including internal fan-out; and retention/deletion of source-bearing provenance. Compare Graph's chunked path with the current full-document, one-request-per-profile adapter. F0032 must separately prove affected-content-only scheduling; a successful whole-document rerun is insufficient.

## Statements, time, and governance measurements (ADR-0063 to ADR-0069)

- **Measure noise before claiming an improvement.** Any extraction or alignment comparison reports at least two runs per configuration and the judge model's own variance on repeated judgement. The judge is calibrated against a hand-labelled set, and its agreement is stated. A difference smaller than the combined spread is not an improvement.
- **Do not use F1 against a gold set known to omit true facts.** Report judged precision and gold recall separately (ADR-0063).
- **Open statements (ADR-0063):** not-stated rate (target ≤ 2%) and misworded rate on the narrative slice; tokens per document. **Typed assertions per profile:** judged precision and recall against the template route on the same documents before `OPEN` activation.
- **Time (ADR-0064):** normalization accuracy per shape and resolution grade (proposed starting thresholds 95% absolute, 85% anchored); valid-time correctness on the endorsement timeline; grade-C and unknown-end handling.
- **Admission (ADR-0065):** drop rates by reason, `BLOCK_UNINTERPRETED` and truncation counts, and described-evidence review items. Fabricated-quote fixtures are refused and misread-value fixtures reach review (EX-SEM-005b).
- **Names and identity (ADR-0066, ADR-0067):** pairwise precision and recall of same-entity decisions in both arrival orders, with the difference reported; wrong merges and missed merges separately. Before enabling any automation: agreement with human decisions, share decided automatically, revert rate.
- **Regression cases (section 98):** fiscal and 52/53-week periods; time-zone and time-of-day conventions; "as of inception"; subjectivities and quote-versus-bound; chart-description contradictions; named-insured change by endorsement; basis changes through the class hierarchy; external-action crash windows.

## Governed retrieval and spectral experiment evaluation

Owners: Quality Engineer and PM for corpus/acceptance planning (D4), AI Engineer for ranking/model/numerical comparisons, Security for non-influence review. [Design](../architecture/governed-evidence-retrieval-design.md), [handoff §9](../architecture/nebula-spectral-graph-intelligence-handoff.md#9-test-plan-and-benchmark-specification), Proposed [ADR-0076](../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) and [EX-RET-001–006](../examples/governed-evidence-retrieval.md) are the inputs. These are future feature acceptance criteria, not results of this documentation change.

### Corpus and timing

Build an executable runner and versioned synthetic fixtures before baseline implementation measurements; spectral work must not precede them. F0035 Phase A confirms the proposed 120-question distribution: 30 single-evidence, 30 cross-document coverage/endorsement/exclusion, 20 temporal/conflicting-amendment, 20 authorized claim/location/exposure traversal, 10 missing-evidence and 10 adversarial access cases. These are fixture categories, not additional persona or insurance-rule commitments. Use independent adjudicated gold evidence sets, bindings, answer/citation spans, admissibility and temporal truth; include paired source/canonical and broader-grant/narrower-root questions.

Split tuning, validation and frozen holdout by account/document families, keeping related versions and paraphrases together. Documentation examples stay outside the holdout. Version corpus, split, adapter, model/tokenizer, input snapshots, profiles and implementation revisions. Synthetic adapter runs prove interfaces; only actual adapter measurements support quality claims. Pin immutable upstream references when evaluating a research technique; quoted upstream results are not a Nebula reproduction.

### Baseline and conditional ablations

| Comparison | Retrieval / selection | When required |
|---|---|---|
| A | Hybrid, no expansion, top-k under the same token cap | F0035/F0036 baseline |
| B | Hybrid, no expansion, budget-aware selection | F0035/F0036 baseline |
| C | Hybrid plus bounded expansion, budget-aware selection | F0035/F0036 baseline |
| D | C plus stochastic PPR | Only if the optional comparator is implemented |
| E | C plus spectral proximity | F0068, if pursued |
| F | C plus spectral coordinates and heat | F0068, if pursued |
| G | C plus PPR/spectral ensemble, optional heat | F0068, if pursued and PPR exists |
| Additional | Heat-only and spectral-without-expansion | F0068, if those modes are pursued; no-expansion is benchmark-only |

For component ablations hold the eligible corpus, split, tokenizer/budget, seed ranking/count and selector settings fixed as appropriate; scoring-only comparisons also fix the candidate graph. Separately run a strong end-to-end hybrid comparator with the same candidate cap and enough retrieval depth to fill the evidence budget. Do not limit hybrid to 20 seeds while expansion considers 200 candidates. Report candidate counts, selected tokens and budget utilization; give alternatives comparable tuning effort and include an available F0061 reranker without making it a prerequisite. Mark absent modes unavailable. Expansion/selector gains cannot be credited to spectral computation.

### Measurements and proposed gates

Report Recall@5/10, complete-gold-evidence-set and bridge recall, precision, MRR/nDCG, redundancy/diversity and budget-weighted recall; grounded correctness, citation faithfulness, abstention, conflict/supersession handling and locator precision; p50/p95/p99 latency, build time, memory/index size, fallback rates and per-tenant costs. Counts/financial answers must use the typed authorized query path. Provide sample sizes, paired bootstrap confidence intervals and breakdowns by query type.

Map handoff RG0–RG5 into feature acceptance criteria; these labels are not new framework gates. RG0 requires reviewed contracts/threat model; RG1 baseline primitives and applicable numerical/PPR proofs; RG2 held-out quality with single-hop regression protection; RG3 all permission/time/evidence/answer-basis invariants; RG4 documented latency/index budgets and safe fallback; RG5 separate baseline versus experimental promotion decisions. After baseline measurement and before held-out scoring, pre-register exact no-regression tolerances, minimum worthwhile gains and operating-cost limits with the feature owner. No numeric gain target is approved here.

Required governance cases cover unauthorized intermediaries and dependencies, cross-tenant identity collisions, root narrowing, current revocation with historical queries, source/canonical differences, future-state topology influence, counts/facets, trace/cache/timing channels, incompatible projections, final reauthorization, exact serialized budgets (including a 4,096-token profile), unresolved evidence and selected-versus-used attribution. RET-35-03 requires identical visible IDs, paths, score components, counts and context when unauthorized inputs change but admissible inputs do not. Governance invariants are hard requirements.

F0068 adds line/star/clique/bridge, empty/small/isolated/disconnected graphs, repeated eigenvalues and sign/rotation-invariant subspace tests; sparse scale/memory, residual/orthogonality and deterministic node mapping; correct zero-subspace heat versus exact small-matrix exponentials; no cross-component diffusion; atomic publication/recovery and rollback compatibility. PPR, if present, proves stochastic mass, restart, sink handling and convergence. Spectral promotion requires incremental benefit over strong hybrid/C and available D/reranker baselines, permission-safe shadow evidence, opt-in approval and rollback. Default activation is separate. Baseline can close while F0068 is deferred.

