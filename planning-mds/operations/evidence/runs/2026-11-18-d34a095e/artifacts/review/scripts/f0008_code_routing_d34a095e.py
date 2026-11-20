import json
from pathlib import Path
import shlex
import sys
sys.path.insert(0, '/tmp')
from f0008_review_exec_d34a095e import ROOT, RUN, run

impact = json.loads((RUN / 'artifacts/review/code-diff-impact.json').read_text())
rows = []
for i, node in enumerate(impact['affected_nodes']):
    code, text = run('python3 scripts/kg/risk.py ' + shlex.quote(node), ROOT,
                     f'artifacts/review/code-risk-{i:02d}.json')
    data = json.loads(text) if code == 0 else {'error': text}
    rows.append({'node': node, 'exit_code': code, 'data': data})
(RUN / 'artifacts/review/code-risk-summary.json').write_text(json.dumps(rows, indent=2) + '\n')
for row in rows:
    data = row['data']
    print(row['node'], json.dumps(data.get('risk', data.get('kg.risk', data.get('score', data))) if isinstance(data, dict) else data))

for i, name in enumerate(('TemporalFactReader', 'VersionTemporal', 'TemporalProposal')):
    code, text = run('python3 scripts/kg/lookup.py --defines ' + name, ROOT,
                     f'artifacts/review/code-defines-{name}.json')
    print(name, 'exit', code)
