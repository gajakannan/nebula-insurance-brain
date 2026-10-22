"""Read-only review routing/quality checks, with output confined to this directory."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}


def run(name, args):
    result = subprocess.run([sys.executable, *args], cwd=ROOT, env=ENV, capture_output=True, text=True)
    (OUT / name).write_text(result.stdout + result.stderr)
    return result


impact = run('kg-diff-impact.json', ['scripts/kg/diff-impact.py', 'HEAD'])
data = json.loads(impact.stdout)
nodes = sorted(set(data['affected_nodes']) | {
    'capability:document-date-provenance', 'capability:versioned-content-contracts',
    'endpoint:content-artifact-get', 'endpoint:content-artifact-file-get',
    'entity:content-artifact', 'entity:content-block', 'entity:content-table',
    'entity:content-table-cell', 'entity:document-date-candidate', 'entity:document-date-selection',
})
summary = []
for node in nodes:
    result = run('risk-' + node.replace(':', '-') + '.json', ['scripts/kg/risk.py', node])
    value = json.loads(result.stdout)
    summary.append({'node': node, 'exit_code': result.returncode,
        'score': value.get('score'), 'band': value.get('band'),
        'recommendations': value.get('reviewer_recommendations', [])})
for symbol in ('DocumentDateService', 'AuthorizedContentPublisher', 'ArtifactKey', 'VerifiedBundleStore'):
    run('defines-' + symbol + '.json', ['scripts/kg/lookup.py', '--defines', symbol])
(OUT / 'routing-summary.json').write_text(json.dumps({'affected_nodes': data['affected_nodes'],
    'untracked_scope_note': 'git diff HEAD excludes untracked implementations; canonical changed-files.txt and manual review supply that scope. G7 symbol and binding reconciliation is pending.',
    'risks': summary}, indent=2) + '\n')
print(json.dumps({'affected_nodes': data['affected_nodes'], 'risk_nodes': len(summary),
    'scores': {item['node']: item['score'] for item in summary}}, sort_keys=True))
