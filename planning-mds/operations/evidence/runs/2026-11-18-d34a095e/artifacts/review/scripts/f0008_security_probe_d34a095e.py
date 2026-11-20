import json
from pathlib import Path

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
evidence = root / 'planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0'
manifest = json.loads((evidence / 'evidence-manifest.json').read_text())
out = {}
for name, lane in manifest['security_scans'].items():
    path = evidence / lane['artifact']
    raw = json.loads(path.read_text())
    row = {'artifact': lane['artifact'], 'manifest_result': lane['result']}
    if name in ('sast', 'secrets'):
        hits = [r for run in raw['runs'] for r in run.get('results', [])]
        row.update(count=len(hits), results=[{
            'rule': r.get('ruleId'),
            'level': r.get('level'),
            'locations': [loc.get('physicalLocation') for loc in r.get('locations', [])],
            'suppressions': r.get('suppressions', []),
        } for r in hits])
    elif name == 'dependency':
        deps = raw.get('dependencies', raw) if isinstance(raw, dict) else raw
        row.update(count=len(deps), vulnerabilities=sum(len(d.get('vulns', [])) for d in deps))
    else:
        row['sites'] = [{
            'name': site.get('@name'), 'alerts': site.get('alerts', []),
        } for site in raw.get('site', [])]
    out[name] = row
print(json.dumps(out, indent=2))
