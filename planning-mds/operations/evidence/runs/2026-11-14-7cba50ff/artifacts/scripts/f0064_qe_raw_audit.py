from pathlib import Path
import hashlib
import json

root=Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
run=root/'planning-mds/operations/evidence/runs/2026-11-14-3325803a'
test=run/'artifacts/test-results'
checks=[]
def check(name, passed, details):
    checks.append({'check':name,'passed':bool(passed),'details':details})

contexts={}
def parse_json(raw):
    text=raw.decode() if isinstance(raw, bytes) else raw
    return json.loads(text[text.index('{'):])
for action in ['plan','plan-review']:
    paths=[test/f's0001-context-{action}-run{i}.json' for i in [1,2]]
    raw=[p.read_bytes() for p in paths]
    objects=[parse_json(data) for data in raw]
    contexts[action]=objects[0]
    check('S0001AC3 '+action+' deterministic',raw[0]==raw[1],{'paths':[str(p.relative_to(root)) for p in paths],'sha256':[hashlib.sha256(d).hexdigest() for d in raw]})
    obj=objects[0]
    context=obj.get('context',obj)
    instructions=context['instructions']
    expected=['planning-mds/BLUEPRINT.md','docs/agent-instructions.md']+(['docs/plan-review-checklist.md'] if action=='plan-review' else [])
    check('S0001AC3 '+action+' ordered instructions', [i['path'] for i in instructions]==expected and all(len(i['sha256'])==64 for i in instructions),{'paths':[i['path'] for i in instructions], 'manifest_hash':context['manifest_hash']})

listed=parse_json((test/'s0001-ac4-list.txt').read_text())
ops=listed.get('checks',[])
check('S0001AC4 list',len(ops)==1,{'count':len(ops),'check_ids':[c.get('check_id',c.get('id')) for c in ops]})

for prefix in ['s0003-ac7','s0004-ac3']:
    before=test/f'{prefix}-hash-before.txt'
    after=test/f'{prefix}-hash-after.txt'
    b,a=before.read_bytes(),after.read_bytes()
    check(prefix+' tracked hashes byte-identical',b==a,{'before':str(before.relative_to(root)),'after':str(after.relative_to(root)),'lines':len(b.splitlines()),'sha256':hashlib.sha256(b).hexdigest()})

before=test/'s0003-ac7-status-before.txt'
after=test/'s0003-ac7-status-after.txt'
check('S0003AC7 git status identical',before.read_bytes()==after.read_bytes(),{'before':str(before.relative_to(root)),'after':str(after.relative_to(root))})

result_path=test/'s0004-ac3-copy-run/artifacts/project-checks/PR2-plan-readiness-b5192693076344109f8f450bb7297608.result.json'
result=json.loads(result_path.read_text())
manifest=contexts['plan-review'].get('context',contexts['plan-review'])['manifest_hash']
check('cross-story manifest hash',result['identity']['manifest']==manifest,{'manifest_hash':manifest,'executor_manifest_hash':result['identity']['manifest']})
check('S0004AC3 fail-closed negative',result['exit_code']==1 and result['result']['status']=='fail' and any(f['rule_id']=='BRAIN-CHECKLIST' for f in result['result']['findings']),{'exit_code':result['exit_code'],'result':result['result']})

coverage=json.loads((run/'artifacts/coverage/combined-coverage.json').read_text())['totals']
check('coverage floor',coverage['covered_lines']/coverage['num_statements']>=.8 and coverage['covered_branches']/coverage['num_branches']>=.8,{'totals':coverage,'statement_percent':100*coverage['covered_lines']/coverage['num_statements'],'branch_percent':100*coverage['covered_branches']/coverage['num_branches'],'combined_percent':100*(coverage['covered_lines']+coverage['covered_branches'])/(coverage['num_statements']+coverage['num_branches'])})

print(json.dumps({'checks':checks,'all_pass':all(c['passed'] for c in checks)},indent=2))
