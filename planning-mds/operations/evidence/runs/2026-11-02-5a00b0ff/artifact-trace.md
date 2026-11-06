# Artifact Trace

## Artifacts Read

| Artifact | Source / purpose | State |
|---|---|---|
| `planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/feature-assembly-plan.md` | Operator-approved Phase B design, including 2026-11-01 correction rework | Read; G0 validation pending |
| `planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/F0006-S0001..S0005` | Five raw stories and 35 ACs | Read; implementation not started |
| `planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis/STATUS.md` | Required signoff roles and story progress | Read; unchanged |
| `evidence-manifest.json` | Contract-stamped run identity and planned scope | Draft; gate results empty |
| `artifacts/test-results/runtime-*` | Executed runtime discovery commands and environment checks | Failure evidence; no tests |
| `artifacts/test-results/session-setup-audit.json` | Commands before run log initialization, plus rejected capture invocation | Backfilled via append-command-log.py |

No implementation, approval, signoff, KG reconciliation, closeout or feature index publication is claimed.


## Artifacts Created Or Updated

- Feature assembly plan: appended intended G7 code-binding prediction without
  changing the approved design or canonical semantics.
- STATUS.md: contract progress-cell vocabulary and reaffirmed required roles;
  every story remains Not Started and no implementation signoff was added.
- g0-assembly-plan-validation.md: Architect assembly readiness report.
- Base run headings, G0 decision row and diff inventory repaired for validation.

## Generated Evidence

Final superseding proof: [g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml)
records306 engine passes, including157 feature cases; the 25-case source-authority
focus overlaps that suite. Two independent basis probes are in
[g3-basis-boundary.xml](artifacts/test-results/g3-basis-boundary.xml).
Current changed-code coverage is1170/1266 (92.4171%), and source hashes match both
latest immutable images. Latest secrets/SAST raw reports are stamped230114;
[api-scan-sec04.json](artifacts/security/dast/api-scan-sec04.json) is the current
anonymous DAST result. All earlier runs below remain historical evidence.

G2 additions: `artifacts/test-results/g2-full-changed-code.xml` (290 unique engine
cases), `g2-neuron-importer-isolated.xml` (15 importer cases),
`g2-neuron-recovery.xml` (five SQLite passes with initial PG skips), and
`g2-neuron-postgres-second.xml` (five configured PG passes). Earlier subset runs
are retained and are not added to the unique test count.

`artifacts/coverage/{engine-changed.json,neuron-importer.json,changed-production-lines.json,changed-code-summary.json}`
retain raw coverage, exact diff denominator and per-file misses. The durable
`measure_changed_coverage.py` reproduces the union and enforces the contract floor.
`artifacts/runtime/{deployment-verification.json,engine-immutable.json,neuron-immutable.json}`
record live migration/defaults and image source/schema checks.

Scanner artifacts are under `artifacts/security/`: engine/Neuron dependency JSON,
redacted secrets SARIF, Semgrep SARIF, ZAP OpenAPI JSON/HTML, and hashed source
snapshot. SAST excludes tests; a subsequent ownership-test-only formatting change
does not alter any scanned production line.

- `artifacts/test-results/g0-migration-lineage.json`: AST-read source revision
  declarations confirm sole migration head 0010; no migration execution.
- `artifacts/test-results/g0-validator-diagnostic.json`: initial G0 failure detail.
- `artifacts/diffs/changed-files.txt`: git changed/untracked paths at G0.
- `gate-state.json`, commands.log and lifecycle-gates.log: actual G0 attempts.

## External Or Global Evidence References

None substitutes for feature-level role evidence. Approved planning runs
2026-11-01-7d6d19ce and 2026-11-01-512e9303 supply the approval history already
recorded in the raw feature assembly plan. Runtime implementation remains unproven.

## Omissions And Waivers

No waiver is taken. Security scans are pending QE execution after implementation,
not omitted or described as completed. Later role artifacts land at their gates.
VF-G0-001 is repaired without waiver: seven application-container staging regressions passed (artifacts/test-results/framework-security-scan-staging.xml), followed by a passing G0 rerun. G2+ scan enforcement remains in place.
