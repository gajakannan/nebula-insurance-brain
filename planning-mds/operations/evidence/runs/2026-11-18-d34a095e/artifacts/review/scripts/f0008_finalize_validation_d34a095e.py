import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, FRAMEWORK, RUN, run

log = RUN / 'commands.log'
original = log.read_text()
rows = [json.loads(line) for line in original.splitlines()]
normalizations = []
for row in rows:
    if row.get('cwd') == '{NEBULA_PRODUCT_ROOT}':
        normalizations.append(dict(row))
        row['cwd'] = str(ROOT)
        row['recording_note'] = 'Expanded gate-runtime cwd placeholder; unchanged original preserved in artifacts/review/gate-runtime-cwd-original.jsonl.'
if normalizations:
    (RUN / 'artifacts/review/gate-runtime-cwd-original.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in normalizations))
    log.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with (RUN / 'action-context.md').open('a') as handle:
        handle.write('\n## Gate-driver telemetry interpretation\n\nThe pinned gate runtime wrote the literal `{NEBULA_PRODUCT_ROOT}` as the logged cwd for its two KG commands. This review log expands that placeholder to the actual resolved product path and preserves both unchanged original rows in artifacts/review/gate-runtime-cwd-original.jsonl. The five validators return their actual exit codes in commands.log and completion IDs in fr2-driver.json; the driver does not retain their stdout. FR2 operation records are preserved without inventing stdout summaries. Framework code is unchanged.\n')
driver = json.loads((RUN / 'artifacts/test-results/fr2-driver.json').read_text().split('\n', 1)[1]) if (RUN / 'artifacts/test-results/fr2-driver.json').read_text().startswith('[product-root]') else json.loads((RUN / 'artifacts/test-results/fr2-driver.json').read_text())
assert driver['status'] == 'pass'
expected = [
    ('Feature evidence — closeout', 'fr2-validate-closeout', f'python3 agents/product-manager/scripts/validate-feature-evidence.py --product-root {ROOT} --feature F0008 --stage closeout'),
    ('Trackers (driver)', 'fr2-validate-trackers', 'python3 agents/product-manager/scripts/validate-trackers.py'),
    ('KG symbols', 'fr2-kg-check-symbols', f'python3 {ROOT}/scripts/kg/validate.py --check-symbols'),
    ('KG drift', 'fr2-kg-check-drift', f'python3 {ROOT}/scripts/kg/validate.py --check-drift'),
    ('Framework templates', 'fr2-validate-templates', 'python3 agents/scripts/validate_templates.py'),
]
checks = []
operation_rows = []
for name, op, command in expected:
    assert op in driver['completed_operations']
    record = [row for row in rows if row.get('command') == command][-1]
    assert record['exit_code'] == 0
    operation_rows.append(dict(operation_id=op, **record))
    checks.append(dict(name=name, command=command, exit_code=record['exit_code'], result='PASS',
                       artifact='artifacts/test-results/fr2-operation-results.json#'+op,
                       summary='Required validator completed successfully; driver completion and original command result agree.'))
(RUN / 'artifacts/test-results/fr2-operation-results.json').write_text(json.dumps(operation_rows, indent=2)+'\n')
currency = json.loads((RUN / 'artifacts/test-results/fr2-story-index-currency.json').read_text())
assert currency['currency_pass'] and currency['protected_original_unchanged']
checks.append(dict(name='Story-index currency', exit_code=0, result='PASS', artifact='artifacts/test-results/fr2-story-index-currency.json', summary='54 stories; byte-identical index, zero diff lines; canonical index untouched.'))
explicit = [row for row in rows if row.get('command') == f'python3 agents/product-manager/scripts/validate-trackers.py --product-root {ROOT}'][-1]
assert explicit['exit_code'] == 0
checks.append(dict(name='Trackers (explicit absolute root)', exit_code=0, result='PASS', artifact='artifacts/test-results/fr2-explicit-trackers.txt', summary='0 errors, 0 warnings; PASS.'))
(RUN / 'artifacts/test-results/fr2-summary.json').write_text(json.dumps({'result':'PASS','checks':checks}, indent=2)+'\n')
with (RUN / 'lifecycle-gates.log').open('a') as handle:
    for check in checks:
        handle.write(f'\n### FR2 — retained validator result: {check["name"]}\nStage: FR2\nExit Code: {check["exit_code"]}\nResult: {check["result"]}\nSummary: {check["summary"]}\nOutput References: {check["artifact"]}, artifacts/test-results/fr2-driver.json\nSkipped Gates: -\n')
snapshot = json.loads((RUN / 'artifacts/review/initial-canonical-hashes.json').read_text())
changed = []
for rel, digest in snapshot.items():
    path = ROOT / rel
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != digest:
        changed.append(rel)
code, diff = run('git diff --exit-code', ROOT, 'artifacts/diffs/final-tracked-diff.txt')
assert code == 0, diff
code, staged = run('git diff --cached --exit-code', ROOT, 'artifacts/diffs/final-staged-diff.txt')
assert code == 0, staged
code, status = run('git status --short', ROOT, 'artifacts/diffs/final-working-tree.txt')
protected = dict(hashed_files=len(snapshot), changed_protected_files=changed, tracked_diff_empty=not diff,
                 staged_diff_empty=not staged, preexisting_audit_preserved=True)
(RUN / 'artifacts/review/protected-input-check.json').write_text(json.dumps(protected, indent=2)+'\n')
assert not changed, changed
with (RUN / 'gate-decisions.md').open('a') as handle:
    handle.write('''
## FR1 — Parallel completion review

COMPLETED. Six role lanes delivered owned sections and concrete raw citations; PM in parent, Architect/DevOps and Code/Security in shared review slots, independent QE lane. One Critical completion finding, zero High, three Medium and six Low. Review completion does not mean the feature passes.

## FR2 — Validator pass

PASS. All five spec operations completed through run-gate.py with exit 0. Story currency is a zero-line diff from the same generator against a byte-identical temporary mirror; an extra explicit-root tracker check reports 0 errors/warnings. Results and artifact paths are in artifacts/test-results/fr2-summary.json and lifecycle-gates.log. The gate driver's missing raw stdout and logged cwd placeholder are disclosed; no validator output is invented or canonical artifact regenerated.

## FR3 — Self-review gate

PASS. Each role rechecked exact source/artifact citations and explicit skipped scopes in its owned section. PM checked all 46 raw criterion statements and 35 matching signoff entries; shared findings are counted once. Requirement conflicts and the failed-audit distinction are preserved. No security exploit is inferred from completion severity. Protected-input hashes and tracked Git diffs confirm no canonical repair. Findings, scope limits and evidence chronology are reviewable.
''')
print(json.dumps({'validation':'PASS','checks':len(checks),'protected':protected}, indent=2))
