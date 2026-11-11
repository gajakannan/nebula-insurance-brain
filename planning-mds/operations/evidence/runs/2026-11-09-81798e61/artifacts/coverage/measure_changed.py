import json
from pathlib import Path
import re
import subprocess

root=Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
run=root/'planning-mds/operations/evidence/runs/2026-11-09-81798e61'
raw=json.loads((run/'artifacts/coverage/engine-full-final.json').read_text())
records=[]
for path,cov in raw['files'].items():
    path='engine/'+path.split('/engine/',1)[1] if '/engine/' in path else path
    if not path.startswith('engine/') or '/src/' not in path:continue
    diff=subprocess.check_output(['git','diff','--no-ext-diff','--unified=0','fa8fc1d','--',path],cwd=root,text=True)
    lines=set()
    for start,count in re.findall(r'^@@ .* \+(\d+)(?:,(\d+))? @@',diff,re.M):
        lines.update(range(int(start),int(start)+int(count or 1)))
    executable=set(cov['executed_lines'])|set(cov['missing_lines'])
    changed=lines&executable
    if not changed:continue
    covered=changed&set(cov['executed_lines'])
    records.append(dict(file=path,changed_executable=len(changed),covered=len(covered),missing=sorted(changed-covered)))
total=sum(x['changed_executable'] for x in records)
covered=sum(x['covered'] for x in records)
summary=dict(base='fa8fc1d',source='artifacts/coverage/engine-full-final.json',files=records,changed_executable_lines=total,covered=covered,percent=100*covered/total,excluded='Migration behavior is proven by real PostgreSQL tests; source line coverage measures application src/ only.')
(run/'artifacts/coverage/changed-code-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
assert summary['percent']>=80
