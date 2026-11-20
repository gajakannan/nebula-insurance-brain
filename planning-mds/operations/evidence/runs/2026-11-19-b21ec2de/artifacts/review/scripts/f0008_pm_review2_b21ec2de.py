import json
import re
import sys
sys.path.insert(0,'/tmp')
from f0008_review2_exec_b21ec2de import ROOT,RUN
feature=ROOT/'planning-mds/features/archive/F0008-bitemporal-canonical-facts'
can=ROOT/'planning-mds/operations/evidence/runs/2026-11-18-bce4909b'
status=(feature/'STATUS.md').read_text()
ledger=(can/'signoff-ledger.md').read_text()
latest={}
for line in status.splitlines():
    if not line.startswith('| F0008-S'): continue
    cols=[x.strip() for x in line.strip('|').split('|')]
    if len(cols)!=7: continue
    story,role,reviewer,verdict,ref,date,note=cols
    latest[story,role]=dict(story=story,role=role,reviewer=reviewer,verdict=verdict,path=ref.strip('`'),date=date)
assert len(latest)==35
for item in latest.values():
    assert '2026-11-18-bce4909b/' in item['path'],item
    assert (ROOT/item['path']).is_file(),item
    assert item['verdict'] in ['PASS','APPROVED','PASS WITH RECOMMENDATIONS'],item
    assert item['story'] in ledger and item['role'] in ledger and item['path'] in ledger,item
stories=[]
for path in sorted(feature.glob('F0008-S*.md')):
    text=path.read_text()
    raw=[dict(line=n,text=line) for n,line in enumerate(text.splitlines(),1) if '**AC' in line or '**Status:**' in line]
    stories.append(dict(path=str(path.relative_to(ROOT)),criteria=raw))
assert len(stories)==7
manifest=json.loads((can/'evidence-manifest.json').read_text())
prior=json.loads((ROOT/'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json').read_text())
assert manifest['status']=='approved' and prior['status']=='superseded'
data=dict(latest_signoffs=list(latest.values()),story_raw_lines=stories,selected_manifest_status=manifest['status'],prior_manifest_status=prior['status'])
(RUN/'artifacts/review/pm-source-checks.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(signoffs=len(latest),stories=len(stories),current_run='approved',prior_run='superseded')))
