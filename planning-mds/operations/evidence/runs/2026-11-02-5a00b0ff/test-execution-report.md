# F0006 Test Execution Report

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Reviewer: Codex / Quality Engineer
- Review date: 2026-11-03T23:08:19+00:00
- Verdict: PASS
- Scope: the approved F0006 five stories and 35 ACs, including current-consumer compatibility.

## Acceptance Assessment

All **35 ACs** have mapped observed proof in `test-plan.md`. Initial independent
review identified missing two-source competition, positive ENTITY/time retention,
operative-policy versus embedded-condition, composite owner-FK and restricted SQL
role cases. Targeted tests now pass in the final engine execution. No blocking
QE finding remains within this feature scope, and no waiver is taken.

## Final Executed Layers

| Artifact | Observed result | Scope |
|---|---|---|
| [artifacts/test-results/g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml) | **306 passed**, zero failures/errors/skips; 75.057 s | Final engine assertion unit/admission/normalization/eligibility/PG/current-consumer tests, ownership matrix, review/security/API/persistence/temporal regressions and real PG commit/concurrency |
| [artifacts/test-results/g3-sec04-focused.xml](artifacts/test-results/g3-sec04-focused.xml) | **25 passed**, zero failures/errors/skips; 18.329 s | Nine actual-SQL metadata-only discovery/denied-payload/corrupt-lineage cases plus existing consumers; overlaps final 306 |
| [artifacts/test-results/g3-evidence-tamper-final.xml](artifacts/test-results/g3-evidence-tamper-final.xml) | **17 passed**, zero failures/errors/skips; 15.152 s | Focused PostgreSQL migration suite: four page/bbox INSERT-tamper rejections, three honest/null positives and existing integrity/rollback cases; overlaps final 306 |
| [artifacts/test-results/g2-neuron-importer-isolated.xml](artifacts/test-results/g2-neuron-importer-isolated.xml) | **15 passed**, zero failures/errors/skips; 21.884 s | Current v1 delivery/importer atomicity/replay, selector and worker restart compatibility |
| [artifacts/test-results/g2-neuron-postgres-second.xml](artifacts/test-results/g2-neuron-postgres-second.xml) | **5 passed**, zero failures/errors/skips; 91.904 s | PostgreSQL process recovery at bundle/run/completion/import/imported crash points |
| [artifacts/test-results/g2-neuron-recovery.xml](artifacts/test-results/g2-neuron-recovery.xml) | **5 SQLite cases passed**; the first attempt skipped its PostgreSQL variants | SQLite process recovery at the same five crash points; explicit PG proof is supplied by the separate successful rerun above |
| [artifacts/test-results/g2-existing-content-worker-postgres.xml](artifacts/test-results/g2-existing-content-worker-postgres.xml) | **5 passed**, zero failures/errors/skips; 25.380 s | Unchanged actual-OCR worker publication/import, profile reuse, concurrent restrictions, missing-producer and corrupt-marker compatibility with explicit PostgreSQL and bounded threads |
| [artifacts/test-results/framework-security-scan-staging.xml](artifacts/test-results/framework-security-scan-staging.xml) | **7 passed** | Framework G0/G1 pending-scan regression and G2+ enforcement |
| [artifacts/test-results/framework-artifact-markdown.xml](artifacts/test-results/framework-artifact-markdown.xml) | **45 passed**, zero failures/errors/skips; 9.384 s | Framework parser and evidence-validator regressions, including 11 new Markdown/plain-path, missing-file and traversal cases; separate from product test counts |

Earlier [g2-complete-assertions.xml](artifacts/test-results/g2-complete-assertions.xml) (141), `g2-regression-final.xml` (126),
`g2-review-regression.xml` (22) and `g2-ownership-first.xml` (15) are retained
diagnostic/focused evidence. They overlap the final 306 and are **not** added to
that count. The prior 290/297 engine results are retained history and replaced
by the clean 306-case run, including 157 feature cases. Its focused 17 migration
and 25 discovery/consumer cases are not added again.
The two process-recovery executions together prove all five crash
points on SQLite and PostgreSQL; skipped cases are not described as passing.

## Runtime, Commands and Isolation

All application validation ran in `engine-validation` or `neuron-validation`
using [artifacts/runtime/compose.yaml](artifacts/runtime/compose.yaml), with healthy application containers.
`commands.log` records exact argv, cwd, exit codes and durable output references;
[artifacts/test-results/qe-executed-command-index.json](artifacts/test-results/qe-executed-command-index.json) extracts the final
container commands used for this verdict. No host-only application test result
substitutes for that evidence.

New PostgreSQL tests create fresh `f0006_qe_*` databases and override shared
integration cleanup. Direct SQL cases assert exact tenant/KB composite FK
failures, zero retained effects and append-only enforcement under a restricted
NOLOGIN SQL role whose grants are confined to its throwaway database. Historical
`brain` is neither truncated nor downgraded by this harness. The occupied-v2
downgrade test proves refusal while retaining semantic/evidence rows.

## Coverage

[artifacts/coverage/changed-code-summary.json](artifacts/coverage/changed-code-summary.json) records **1,170 / 1,266 changed
executable lines covered (92.4171%)**, no missing instrumentation across 20
production Python files, and a passing comparison with the active contract's
`coverage_min_pct`. `coverage-report.md` describes the source-hashed denominator
and raw engine/Neuron inputs. The earlier assertion-only 90.6% artifact is historical and predates the
metadata-discovery helper change; it is not current coverage or used for the floor.

## Failure Triage and Additional Check Status

Security review SEC-04/A-IMPL-02 found pre-READ discovery materialized full ORM
claim/review payloads while selecting source authority keys. The repair uses
minimal-column metadata queries in every discovery callback and checks current
source proof/READ audit before the full canonical eligibility resolver. Nine
PostgreSQL tests observe actual SELECT projections, including denied internal
read, unproved direct commit, review/correction lineage and missing/cyclic/
overlong chains. The focused 25 and full 306 runs above are clean; no payload
selection or canonical effects occur in the negative cases. Existing legacy
pilot behavior and migration-backed structural ownership remain explicit.
This closes the Medium finding without a new policy or waiver. The unchanged
Neuron lanes below were not rerun for this SQL-only repair.

Initial feature failures were repaired and their successful replacements are
the named final artifacts. Architect review identified A-IMPL-01: the deferred
v2 evidence INSERT guard omitted page/bbox mirror equality. Four tamper tests
exposed the missing rejections in the
[red run](artifacts/test-results/g3-evidence-tamper-red.xml); that run also had
two positive-fixture failures. The repaired guard rejected all four tamper cases,
but the [intermediate run](artifacts/test-results/g3-evidence-tamper-green.xml)
and [first full rerun](artifacts/test-results/g3-carrier-regression.xml) still
had those two fixture failures: the supposed regionless fixture retained PDF
source-location metadata. The corrected CSV/TRANSCRIBED regionless fixture now
passes with SQL-null and JSON-null bbox variants. The repaired focused 17 and then-clean 297 runs are retained proof; the final 306
replacement also passes these cases; mismatched coordinates retain zero effects. This resolves
A-IMPL-01 without a waiver or semantic-contract change.

The initial broad Neuron collection had 15 passes and
five real-OCR fixture setup errors due to cache ownership. Parent orchestration
restored the container cache and reran without application edits. A combined
retry then waited in native OCR initialization and its owned process was
terminated (143). The required importer lane was isolated and passed all 15
cases, yielding the clean `neuron-importer.json` coverage input.

An intermediate isolated actual-OCR attempt completed model warmup but
skipped all five cases because `BRAIN_TEST_POSTGRES_URL` was unset; its
[JUnit history](artifacts/test-results/g2-existing-content-worker-isolated.xml)
is retained. The final unchanged `test_content_worker_v2.py` rerun supplied
explicit PostgreSQL configuration and bounded threads: all **five cases passed**
without failures, errors or skips. Its
[raw command output](artifacts/test-results/command-output/g2-existing-content-worker-postgres.log)
and final JUnit above resolve this additional compatibility check. The earlier
setup errors, termination (143) and skipped attempt remain audit history.
These supplemental results do not claim conversion-producer activation or
change the F0006 AC scope.

Evidence refreshed by Codex / Quality Engineer at 2026-11-03T23:08:19+00:00. Product and
framework counts are reported separately; earlier overlapping suites are not
added to the final engine count.

## Fixture and Scope Limits

Synthetic retained-source fixtures are independently authored development
examples outside the frozen holdout. Non-PDF cases retain DOCX/XLSX/CSV original
assets and explicit native locators alongside a synthetic PDF rendition required
by the current bundle contract. The admission fixtures perform no physical
conversion/OCR/model call; they do not establish parser quality, live extraction
activation or production qualification. A trusted fixture time resolver proves
scoped reference retention without implementing F0016's future time store.

UI/component/accessibility/visual tests are out of scope because F0006 adds no
UI. Security scan exploitability/verdicts, deployability, G3 reviews and the G4
operator decision remain their owning roles' responsibilities. This report is
QE evidence, not operator approval, release qualification or PM closeout.
