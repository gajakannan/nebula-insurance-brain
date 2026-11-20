from pathlib import Path
import collections
import json
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
CAN = ROOT/'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0'
def artifact_summary():
    out = {}
    for name in ('g1-baseline-regression.xml','g2-full-engine-regression.xml','g3-full-engine-regression.xml'):
        path = CAN/'artifacts/test-results'/name
        tree = ET.parse(path)
        suites = list(tree.iter('testsuite'))
        cases = list(tree.iter('testcase'))
        by_class = collections.Counter(c.attrib['classname'] for c in cases)
        failures = [c.attrib for c in cases if any(c.find(k) is not None for k in ('failure','error','skipped'))]
        temporal = {k:v for k,v in sorted(by_class.items()) if ('temporal' in k and ('test_bounds' in k or 'test_contract_examples' in k or 'test_temporal_' in k))}
        out[name] = {'suites':[s.attrib for s in suites], 'actual_testcases':len(cases), 'nonpassing': failures, 'f0008_cases_by_class':temporal, 'f0008_total':sum(temporal.values())}
    cov = json.loads((CAN/'artifacts/coverage/g3-engine-coverage.json').read_text())
    out['coverage_meta']=cov['meta']
    out['coverage_totals']=cov['totals']
    diff = subprocess.run(['git','diff','-U0','2badb9ad2756f38ee9a1d84930787a3df989a245..339c9209385290247c01d1eea97a7c2c8b47fada','--','engine'],cwd=ROOT,text=True,capture_output=True,check=True).stdout
    changed = {}
    current = None
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            current=line[6:]
            changed.setdefault(current,set())
        match=re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@',line)
        if match and current:
            start,count=int(match[1]),int(match[2] or 1)
            changed[current].update(range(start,start+count))
    covfiles={}
    for name, data in cov['files'].items():
        path=Path(name)
        rel=str(path.relative_to(ROOT)) if path.is_absolute() else 'engine/'+name
        covfiles[rel]=data
    rows=[]
    hit=total=0
    for name,lines in sorted(changed.items()):
        if '/src/' not in name or not name.endswith('.py'):
            continue
        data=covfiles.get(name)
        if data is None:
            rows.append({'path':name,'measured':False})
            continue
        executed,missing=set(data['executed_lines']),set(data['missing_lines'])
        covered,executable=len(lines & executed), len(lines & (executed|missing))
        hit+=covered; total+=executable
        rows.append({'path':name,'covered':covered,'executable':executable,'missing':sorted(lines&missing)})
    out['changed_coverage']={'rows':rows,'covered':hit,'executable':total,'pct':round(hit/total*100,6)}
    logs=[]
    for linenum,line in enumerate((CAN/'commands.log').read_text().splitlines(),1):
        try: d=json.loads(line)
        except ValueError: continue
        cmd=d.get('command','')
        if d.get('exit_code') != 0 or any(s in cmd for s in ('g3-full-engine','g2-full-engine','g1-baseline','test_temporal_concurrency','ruff check','mypy')):
            logs.append({'line':linenum,**d})
    out['selected_command_history']=logs
    print(json.dumps(out,indent=2))

artifact_summary()
