# F0006 Coverage Report

- Run: `2026-11-02-5a00b0ff`
- Owner/reviewer: Codex / Quality Engineer
- Review date: 2026-11-03T23:08:19+00:00
- Verdict: PASS
- Coverage waiver: none.

## Changed-Code Result

**1,170 of 1,266 changed executable lines covered: 92.4171%.** The raw summary
has 96 missed lines, 20 production Python files and no missing instrumentation.
Its direct comparison with `coverage_min_pct` from the active feature evidence
contract passes. This is statement/line coverage; no branch percentage is claimed.

## Reproduction and Denominator

Durable calculation: [artifacts/coverage/measure_changed_coverage.py](artifacts/coverage/measure_changed_coverage.py).
Input inventory: [artifacts/coverage/changed-production-lines.json](artifacts/coverage/changed-production-lines.json).
Raw container observations: [artifacts/coverage/engine-changed.json](artifacts/coverage/engine-changed.json) and
[artifacts/coverage/neuron-importer.json](artifacts/coverage/neuron-importer.json).
Result: [artifacts/coverage/changed-code-summary.json](artifacts/coverage/changed-code-summary.json).

The inventory records added/modified lines from the git HEAD diff plus new
production Python files and SHA-256 fingerprints each source. The script verifies
those hashes, intersects changed lines with measured executable statements,
unions observed execution across the two application runtimes, preserves all
per-file misses and reads the floor from `_contract.yaml`. Historical unrelated
module lines and test files are not represented as newly implemented feature
lines. All 20 production fingerprints still matched at QE review.

The refreshed engine input is backed by 306 passing cases in
[g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml),
including the page/bbox guard and metadata-only discovery repair. The 20-file
source inventory, engine coverage input and changed-code summary were refreshed
after the two persistence files changed; all current fingerprints match.
The current 1170/1266 result replaces the earlier 1137/1231 measurement.
The clean Neuron input is backed by 15 passing cases in
[g2-neuron-importer-isolated.xml](artifacts/test-results/g2-neuron-importer-isolated.xml); the summary was regenerated from that clean
lane after the broader OCR fixture runtime failure. Exact executed commands are
indexed in [artifacts/test-results/qe-executed-command-index.json](artifacts/test-results/qe-executed-command-index.json) and commands.log.

## Per-File Changed Executable Lines

| Production source | Executed / changed executable |
|---|---|
| `engine/apps/api/src/brain_api/errors.py` | 3 / 3 |
| `engine/apps/api/src/brain_api/routes/facts.py` | 8 / 8 |
| `engine/apps/api/src/brain_api/routes/reviews.py` | 6 / 6 |
| `engine/apps/worker/src/brain_worker/document_delivery.py` | 2 / 2 |
| `engine/migrations/versions/0011_f0006_assertion_semantics.py` | 27 / 27 |
| `engine/packages/brain-assertions/src/brain_assertions/__init__.py` | 0 / 0 |
| `engine/packages/brain-assertions/src/brain_assertions/admission.py` | 127 / 146 |
| `engine/packages/brain-assertions/src/brain_assertions/eligibility.py` | 46 / 46 |
| `engine/packages/brain-assertions/src/brain_assertions/normalization.py` | 100 / 100 |
| `engine/packages/brain-assertions/src/brain_assertions/ports.py` | 9 / 9 |
| `engine/packages/brain-assertions/src/brain_assertions/service.py` | 42 / 47 |
| `engine/packages/brain-contracts/src/brain_contracts/assertions.py` | 222 / 231 |
| `engine/packages/brain-contracts/src/brain_contracts/dispatch.py` | 48 / 52 |
| `engine/packages/brain-domain/src/brain_domain/assertions.py` | 85 / 85 |
| `engine/packages/brain-persistence/src/brain_persistence/assertion_models.py` | 50 / 50 |
| `engine/packages/brain-persistence/src/brain_persistence/assertions.py` | 346 / 404 |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | 4 / 4 |
| `engine/packages/brain-persistence/src/brain_persistence/repositories.py` | 30 / 30 |
| `engine/packages/brain-security/src/brain_security/execution.py` | 12 / 13 |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py` | 3 / 3 |

Exact missed line numbers remain in [changed-code-summary.json](artifacts/coverage/changed-code-summary.json). The denominator
includes the added migration/domain/ORM carriers and modified repositories,
authorization facade, temporal commit, HTTP adapters and worker delivery, as
well as the new assertion application and contract modules.

## Historical Assertion-Surface Metric

[artifacts/coverage/assertions.json](artifacts/coverage/assertions.json) /
[assertions.xml](artifacts/coverage/assertions.xml) retains the earlier
906/1,000-statement result (94 missed, 90.6%) from before the metadata-discovery
helper changed. It is historical evidence for the earlier source, not a current
measurement of `brain_persistence.assertions` or the current assertion surface.
It is excluded from the current floor claim. The source-fingerprinted
changed-code result above uses the clean 306-case engine input and current code.

## Limits and Disposition

No coverage waiver or lowered floor is used. Coverage supports the independent
35-AC behavior mapping; a percentage alone is not an acceptance proof. The
additional unchanged actual-OCR module runtime check passed all five cases
with explicit PostgreSQL configuration, as documented in test-execution-report.md.
It is supplemental compatibility evidence and is not used as a coverage substitute. F0006 conversion/producer activation and frozen-model evaluation
remain outside this bounded storage/admission/consumer feature.
