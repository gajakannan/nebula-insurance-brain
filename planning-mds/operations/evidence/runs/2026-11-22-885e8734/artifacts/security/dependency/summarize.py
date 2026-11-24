"""Summarize scan mechanics and identifiers, leaving risk interpretation to Security."""
import json
from pathlib import Path

directory = Path(__file__).resolve().parent
summary = {}
for workspace in ('engine', 'neuron'):
    data = json.loads((directory / f'{workspace}.json').read_text())
    dependencies = data['dependencies']
    summary[workspace] = {
        'dependencies_reported': len(dependencies),
        'skipped': [{'name': d['name'], 'version': d.get('version'), 'reason': d['skip_reason']}
                    for d in dependencies if d.get('skip_reason')],
        'findings': [{'package': d['name'], 'version': d.get('version'),
                      'id': v['id'], 'aliases': v.get('aliases', []),
                      'fix_versions': v.get('fix_versions', [])}
                     for d in dependencies for v in d.get('vulns', [])],
    }
frontend = json.loads((directory / 'frontend.json').read_text())
if 'error' in frontend:
    summary['experience'] = {'scanner_error': frontend['error']}
elif 'advisories' in frontend:
    summary['experience'] = {
        'metadata': frontend.get('metadata'),
        'findings': [{'package': a.get('module_name'), 'severity': a.get('severity'),
                      'id': a.get('id'), 'cves': a.get('cves', []), 'title': a.get('title')}
                     for a in frontend['advisories'].values()]}
elif 'vulnerabilities' in frontend:
    summary['experience'] = {'metadata': frontend.get('metadata'), 'vulnerabilities': frontend['vulnerabilities']}
else:
    summary['experience'] = {'scanner_error': 'Unrecognized audit response shape', 'keys': sorted(frontend)}
(directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
