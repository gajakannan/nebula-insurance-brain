from pathlib import Path
import collections, json, re, subprocess
import xml.etree.ElementTree as ET
ROOT=Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
CAN=ROOT/'planning-mds/operations/evidence/runs/2026-11-18-bce4909b'
coverage=json.loads((CAN/'artifacts/coverage/engine-coverage.json').read_text())
tree=ET.parse(CAN/'artifacts/test-results/full-engine-regression.xml')
cases=list(tree.iter('testcase'))
byclass=collections.Counter(c.attrib['classname'] for c in cases)
expected=('test_s0002_ac7_commit_response_returns_temporal_metadata',
          'test_runtime_commit_response_validates_for_v1_and_legacy',
          'test_fr_arch_l2_split_lineage_cannot_cross_slots',
          'test_0015_preflight_refuses_cross_slot_lineage_and_cycles_cleanly',
          'test_s0004_ac1_racing_commits_leave_one_answer_per_coordinate',
          'test_legacy_slot_reads_keep_pilot_behaviour')
out={'suites':[s.attrib for s in tree.iter('testsuite')],
     'actual_testcases':len(cases),
     'nonpassing':[c.attrib for c in cases if any(c.find(k) is not None for k in ('failure','error','skipped'))],
     'f0008_cases_by_class':{k:v for k,v in sorted(byclass.items()) if 'temporal' in k and any(s in k for s in ('test_bounds','test_contract_examples','test_temporal_'))},
     'new_testcases':{name:[c.attrib for c in cases if c.attrib['name']==name] for name in expected},
     'coverage_meta':coverage['meta'], 'coverage_totals':coverage['totals']}
covfiles={}
for name,data in coverage['files'].items():
    p=Path(name)
    rel=str(p.relative_to(ROOT)) if p.is_absolute() else 'engine/'+name
    covfiles[rel]=data
for label,base in (('remediation','339c9209385290247c01d1eea97a7c2c8b47fada'),('whole_feature','2badb9ad2756f38ee9a1d84930787a3df989a245')):
    diff=subprocess.run(['git','diff','-U0',base+'..3290d17750b62d70b9130ac9010d096a584eead5','--','engine'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
    changed={};current=None
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            current=line[6:];changed.setdefault(current,set())
        match=re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@',line)
        if match and current:
            start,count=int(match[1]),int(match[2] or 1)
            changed[current].update(range(start,start+count))
    rows=[];hit=total=0
    for name,lines in sorted(changed.items()):
        if '/src/' not in name or not name.endswith('.py'): continue
        data=covfiles.get(name)
        if data is None:
            rows.append({'path':name,'measured':False});continue
        executed,missing=set(data['executed_lines']),set(data['missing_lines'])
        covered,executable=len(lines&executed),len(lines&(executed|missing))
        hit+=covered;total+=executable
        rows.append({'path':name,'covered':covered,'executable':executable,'missing':sorted(lines&missing)})
    out[label+'_coverage']={'rows':rows,'covered':hit,'executable':total,'pct':round(hit/total*100,6)}
out['command_history']=[]
for num,line in enumerate((CAN/'commands.log').read_text().splitlines(),1):
    try: d=json.loads(line)
    except ValueError: continue
    cmd=d.get('command','')
    if any(s in cmd for s in ('pytest','runtime-probe','fresh-db-upgrade')) or d.get('exit_code') != 0:
        out['command_history'].append({'line':num,**d})
out['raw_output_tails']={}
names=['full-engine-regression.txt',*(f'concurrency-repeat-{i}.txt' for i in range(1,4)),*(f'ci-nodb-gate-brain_{n}.txt' for n in ('temporal','api','domain','factslots'))]
for name in names:
    p=CAN/'artifacts/test-results/command-output'/name
    out['raw_output_tails'][str(p.relative_to(ROOT))]={'linecount':len(p.read_text().splitlines()),'tail':p.read_text().splitlines()[-8:]}
print(json.dumps(out,indent=2))
