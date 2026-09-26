# Evaluation Strategy — Golden Corpus, Metrics, Regression, Release Gates

**Status:** Baseline index (extracted from the master blueprint on 2026-09-05); the quality-engineer role expands this into per-feature test plans.

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

## Docling-Graph integration gate (ADR-0060)

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

