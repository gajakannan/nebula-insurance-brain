import hashlib
import json
import sys
sys.path.insert(0,'/tmp')
from f0008_review2_exec_b21ec2de import ROOT,FRAMEWORK,RUN,run

names={
 'fr2-validate-closeout':'Feature evidence — closeout',
 'fr2-validate-trackers':'Trackers',
 'fr2-kg-check-symbols':'KG symbols',
 'fr2-kg-check-drift':'KG drift',
 'fr2-validate-templates':'Framework templates',
}
checks=[]
for op,name in names.items():
    meta=json.loads((RUN/f'artifacts/validators/{op}.result.json').read_text())
    assert meta['exit_code']==0 and meta['ok'],meta
    out=(RUN/f'artifacts/validators/{op}.stdout.txt').read_text()
    err=(RUN/f'artifacts/validators/{op}.stderr.txt').read_text()
    checks.append(dict(name=name,exit_code=meta['exit_code'],result='PASS',
      artifact=f'artifacts/validators/{op}.stdout.txt',stderr=f'artifacts/validators/{op}.stderr.txt',
      metadata=f'artifacts/validators/{op}.result.json',summary='; '.join((out or err).strip().splitlines()[-4:])))
currency=json.loads((RUN/'artifacts/test-results/fr2-story-index-currency.json').read_text())
assert currency['currency_pass'] and currency['protected_original_unchanged']
checks.append(dict(name='Story-index currency',exit_code=0,result='PASS',artifact='artifacts/test-results/fr2-story-index-currency.json',summary='54 stories; byte-identical output; zero diff lines; canonical index untouched.'))
code,framework=run('git rev-parse HEAD',FRAMEWORK,'artifacts/review/fr2-framework-head-after.txt')
before=(RUN/'artifacts/review/fr2-framework-head.txt').read_text().strip()
assert framework.strip()==before,'Framework changed during validation'
code,head=run('git rev-parse HEAD',ROOT,'artifacts/diffs/final-head.txt')
if not head.startswith('3290d17'):
    code,equivalence=run('git diff --exit-code 3290d17750b62d70b9130ac9010d096a584eead5 HEAD',ROOT,'artifacts/diffs/merge-tree-equivalence.diff')
    assert code==0 and not equivalence,'Product content changed during review'
    code,trees=run("git rev-parse '3290d17750b62d70b9130ac9010d096a584eead5^{tree}' 'HEAD^{tree}'",ROOT,'artifacts/diffs/merge-tree-hashes.txt')
    assert code==0 and len(set(trees.splitlines()))==1,'Merge tree mismatch'
    (RUN/'artifacts/diffs/merge-tree-equivalence.json').write_text(json.dumps(dict(audited_commit='3290d17750b62d70b9130ac9010d096a584eead5',current_commit=head.strip(),tree=trees.splitlines()[0],tracked_trees_identical=True),indent=2)+'\n')
initial=json.loads((RUN/'artifacts/review/protected-input-hashes.json').read_text())
changed=[rel for rel,digest in initial.items() if not (ROOT/rel).is_file() or hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=digest]
assert not changed,changed
code,diff=run('git diff --exit-code',ROOT,'artifacts/diffs/final-tracked-diff.txt')
assert code==0 and not diff
code,staged=run('git diff --cached --exit-code',ROOT,'artifacts/diffs/final-staged-diff.txt')
assert code==0 and not staged
code,status=run('git status --short',ROOT,'artifacts/diffs/final-working-tree.txt')
protected=dict(files_checked=len(initial),changed_files=changed,tracked_diff_empty=True,staged_diff_empty=True,head=head.strip())
(RUN/'artifacts/review/protected-input-check.json').write_text(json.dumps(protected,indent=2)+'\n')
data=dict(result='PASS',framework_head=framework.strip(),checks=checks)
(RUN/'artifacts/test-results/fr2-summary.json').write_text(json.dumps(data,indent=2)+'\n')
with (RUN/'lifecycle-gates.log').open('a') as h:
    for item in checks:
        h.write(f'\n### FR2 — retained summary: {item["name"]}\nStage: FR2\nExit Code: {item["exit_code"]}\nResult: PASS\nSummary: {item["summary"]}\nOutput References: {item["artifact"]}\nSkipped Gates: -\n')
with (RUN/'gate-decisions.md').open('a') as h:
    h.write('''
## FR1 — Parallel completion review

COMPLETED. Six role-owned sections checked previous remediation against raw current source/evidence and sought additional pending work. Counts: Critical0, High1, Medium0, Low4. The High is Security-owned, source-supported and not runtime-reproduced. No code/evidence repair performed.

## FR2 — Validator pass

PASS. Five required spec operations ran through the unchanged gate driver with supported runtime stream capture. Actual stdout/stderr/result artifacts and exit0 are retained for each. Story-index currency is byte-identical on a temporary mirror; canonical index untouched. Exact framework revision and protected canonical-file hashes are recorded in fr2-summary.json and protected-input-check.json.

## FR3 — Self-review

PASS. Each lane checked raw citations and justified skipped layers. Prior response/audit fixes are closed on evidence; new predecessor-metadata source authorization is counted once in Security. Missing live proof is explicit: automated cybersecurity safeguards stopped the proposed runtime verification and it was not retried. Existing test/scanner success is not substituted for that missing negative. No accepted High mitigation or target date is fabricated. All protected canonical hashes match and tracked/staged diffs are empty.
''')
print(json.dumps(dict(validation='PASS',checks=len(checks),framework=framework.strip(),protected=protected),indent=2))
