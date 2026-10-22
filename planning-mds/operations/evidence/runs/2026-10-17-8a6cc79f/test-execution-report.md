# Test Execution Report — F0004 run 2026-10-17-8a6cc79f

Owner: Codex, Quality Engineer role. Refreshed after G3 corrections, 2026-10-20.

## Commands Executed

Exact commands, cwd, timestamps, exit codes and artifact bindings are in
commands.log. All final application tests/lint/type/build checks ran in the
locked application validation jobs under artifacts/runtime/compose.yaml.

- Engine: brain-content/security/jobs tests, API content tests and PostgreSQL
  migration/publication/date/operator tests → exit 0.
- Neuron: ingestion tests and integration suite, including actual converter
  spike/projection and existing worker/process/Graph comparisons → exit 0.
- Restore: actual v1/v2 database/content backup/restore plus negatives → exit 0.
- Durable table supplement: PostgreSQL table/cell/header/continuation indexes,
  exact retries, cross-owner FK denial and missing-link detection → exit 0.
- Changed-runtime coverage threshold, all changed-Python lint, 28 engine and
  12 neuron source module type checks → exit 0.
- Six authored schemas / 40 structured examples and deployed wheel's five
  packaged contracts with repository fallback disabled → exit 0.

## Pass/Fail Counts

| Lane | Total | Pass | Fail | Skip |
|---|---:|---:|---:|---:|
| Engine unit/security/API/PostgreSQL | 229 | 229 | 0 | 0 |
| Neuron unit/integration | 97 | 93 | 0 | 4 |
| Real isolated restore | 4 | 4 | 0 | 0 |


The durable table-index proof is included in the refreshed engine total; its
earlier separate pass is not counted again. Eight added PDF-signature cases
and one date concurrency case are included in the new totals.

Additional coverage-only reruns of two migration cases and one operator CLI
case reuse cases already counted in the engine lane, so are not added again.

## Skipped Tests And Rationale

All four skips are existing optional production-inference/tokenizer cases:
test_graph_live_inference (explicit opt-in), two test_parse_once_reinterpret
cases (local vLLM unreachable), and the pinned-Phi-tokenizer case in
test_vllm_graph_client (assets not cached). Their exact locations/reasons are in
g3-neuron-regression.txt. F0004 does not qualify a production model, tokenizer
or Graph activation. Actual Docling conversion/OCR, recorded Graph calls and
parser-free restart/reuse do execute; none of those required proofs is skipped.

Frontend browser/visual/accessibility tests are not in scope: no UI changed.
Performance qualification stays with F0005/F0026; no latency claim is made.

## Raw Test Artifact Paths

All paths below are under the artifacts/test-results directory:
- g3-engine-regression.txt
- g3-neuron-regression.txt
- g3-restore-regression.txt
- g3-date-read-regression.txt
- g3-sec-h1-tests.txt
- g3-all-changed-python-lint.txt
- g3-date-repository-types.txt and g3-sec-h1-types-corrected.txt
- g3-current-coverage-threshold.txt
- g2-restore-subprocess-coverage.txt
- g2-durable-table-index-tests.txt
- g2-migration-coverage.txt and g2-operator-cli-coverage.txt
- g2-final-changed-python-lint.txt
- g2-engine-types.txt, g2-final-engine-refinement-types.txt,
  g2-final-neuron-types.txt
- g2-structured-contract-examples.txt
- g2-wheel-schema-deployment-proof.txt
- g2-security-remediated-locked-build.txt, g2-remediated-runtime-start.txt,
  g2-remediated-runtime-health.txt

## Failed / Retried Command History

Historical failures are preserved. Runtime cache/socket/network failures stopped
dependent work and were repaired/rechecked. API retained-scope PermissionError
had been caught as OSError and returned 503; reordered handling now yields the
required sanitized 409, and all 18 content API cases pass. Old comparison fixtures
retained unsupported source.json/source.md; they now retain the committed
synthetic PDF without relaxing the contract. A downgrade query refactor
shadowed SQLAlchemy's table function; the alias fix passes the full engine
suite, safe downgrade and retained-history refusal. The added cross-owner
table-link test first hit an existing PK; the isolated fixture now removes its
links before testing the FK, then verifies missing-link rejection. No product
rule was weakened to make a test pass.

Independent G3 review reproduced an accepted gzip/PDF polyglot reaching archive
detection and a concurrent date read omitting its selected candidate. The
first-byte signature guard rejects before either parser in both provenance
modes; native/scanned and v2 conversion still pass. A version FOR SHARE lock
now spans candidate/selection reads through audit commit, with a deterministic
PostgreSQL interleaving test. Review also removed repeated whole-JSONL splitting.
Initial commands without the container working-directory override and a lint
fixture-format diagnostic are retained; corrected commands pass. The final
source tests, lint, types and coverage above supersede pre-correction results.

Dependency scanning prompted targeted PyJWT/pypdf/urllib3/multidict lock updates,
then locked rebuild and full final tests. All changes and remaining component
risk are for Security review. Scanner findings do not become test passes.

## AC Coverage Result

All 25 ACs are covered by the explicit mapping in test-plan.md and these final
lane artifacts. S0001: exact bytes, audit/fence/conflict/restart/two-profile reuse.
S0002: actual native/scanned/mixed producer observations; strict records, stored
transcript/description fixtures, Unicode/geometry/table constraints and durable
table/cell indexes. S0003: three date bases, undated defaults, human-only
selection/clear, append/CAS/history/rollback and exact June issue-date example.
S0004: current owner/grants, versioned readers/backfill/repair, actual isolated
restore and existing Graph/worker compatibility. Worked-example reproduction
commands remain synthetic development material outside the frozen holdout.

## Result

PASS
