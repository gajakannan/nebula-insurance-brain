import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
canonical = root / 'planning-mds/operations/evidence/runs/2026-11-14-3325803a'
review = root / 'planning-mds/operations/evidence/runs/2026-11-14-7cba50ff'
feature = root / 'planning-mds/features/archive/F0064-repository-instructions-and-planning-check-adoption'
baseline = '6acd80560c0bc486bf9a7b28041631f907c2e901'
out = {}

prd = (feature / 'PRD.md').read_text()
assert '**Status:** Done / Archived' in prd
assert '- [ ]' not in prd.split('## Acceptance Criteria Overview')[1].split('## UX')[0]
assert (feature / '../../../examples/personas/platform-engineer.md').resolve().is_file()
out['PM-01'] = 'PASS: archived status, checked overview, resolved persona reference'

shard = (root / 'planning-mds/kg-source/features/F0064.yaml').read_text()
correction = (canonical / 'post-closeout-corrections.md').read_text()
ci = (canonical / 'artifacts/test-results/s0004-ac4-ci-checks-pr50.txt').read_text()
assert 'verification PR #49, closeout PR #50' in shard
assert 'abe5045f785bf4aea4c6dfa09783cc145d2cf1b7' in ci
assert len([line for line in ci.splitlines() if '\tpass\t' in line]) == 7
assert 'PM-02' in correction and 'PR #50' in correction
out['PM-02'] = 'PASS: corrected final-head CI provenance and saved canonical raw check output'

state = json.loads((canonical / 'gate-state.json').read_text())
attested = []
for stage in state['stages'].values():
    for attestation in stage.get('attestations', []):
        for evidence in attestation.get('evidence', []):
            path = canonical / evidence['path']
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual == evidence['sha256'], evidence['path']
            attested.append({'path': evidence['path'], 'sha256': actual})
assert {'pm-closeout.md','signoff-ledger.md','kg-reconciliation.md'} <= {v['path'] for v in attested}
out['attested_files'] = attested

totals = json.loads((canonical / 'artifacts/coverage/combined-coverage.json').read_text())['totals']
statement = 100 * totals['covered_lines'] / totals['num_statements']
branch = 100 * totals['covered_branches'] / totals['num_branches']
combined = 100 * (totals['covered_lines'] + totals['covered_branches']) / (totals['num_statements'] + totals['num_branches'])
coverage = (canonical / 'coverage-report.md').read_text()
for value in [f'{statement:.2f}%', f'{branch:.2f}%', f'{combined:.2f}%']:
    assert value in coverage, value
assert '**88% branch coverage**' not in coverage
assert min(statement,branch,combined) > 80
out['QE-L1'] = dict(result='PASS', statement=statement, branch=branch, combined=combined)

assert 'This cannot be recovered and is not reconstructed here.' in correction
assert 'attempt-numbered' in correction
for relative in ['pm-closeout.md', 'signoff-ledger.md', 'kg-reconciliation.md',
                 'artifacts/gates/g0.txt', 'artifacts/gates/g1.txt', 'artifacts/gates/g5.txt']:
    old = subprocess.check_output(['git','show',baseline + ':' + str((canonical / relative).relative_to(root))], cwd=root)
    assert old == (canonical / relative).read_bytes(), relative
out['QE-L2'] = 'ADDRESSED: unrecoverable diagnostic loss disclosed; no historical output fabricated; attempt-numbered output convention documented'

timeline = (canonical / 'feature-action-execution.md').read_text()
assert '| G7 | Architect | PASS |' in timeline
assert '| G8 | Product Manager | APPROVED |' in timeline
out['additional_timeline_correction'] = 'PASS'

for name in ['f0064_review_exec.py','f0064_arch_audit.py','f0064_qe_raw_audit.py',
             'f0064_story_currency.py','f0064_log_bootstrap.py','f0064_finalize_review.py']:
    assert (review / 'artifacts/scripts' / name).is_file()
out['preserved_review_helpers'] = 6
assert subprocess.run(['git','diff','--quiet',baseline + '..HEAD','--',
    'engine','neuron','experience','scripts','.github','.nebula-project.yaml','pyproject.toml','uv.lock'],
    cwd=root).returncode == 0
out['runtime_and_tooling_source_unchanged'] = True
context = json.loads(Path('/tmp/f0064-followup-project-context.json').read_text())
assert context['product_root'] == str(root)
assert [(v['path'],v['sha256']) for v in context['instructions']] == [
 ('planning-mds/BLUEPRINT.md','9185d8b169f6e1ba4b4b65c26dda41c0af668e7ac5f149ae499713a19a586ef1'),
 ('docs/agent-instructions.md','a7645e80a39f2aca95b31f01b711353754630c1e62fd47812dba0fe5ed9aaae2')]
out['previously_read_product_instructions_unchanged'] = True
print(json.dumps(out,indent=2))
