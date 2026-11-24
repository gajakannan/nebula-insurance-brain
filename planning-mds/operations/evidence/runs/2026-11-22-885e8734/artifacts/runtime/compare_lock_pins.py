"""Verify that the approved dependency was added without upgrading other pins."""
import argparse
import json
import tomllib
from pathlib import Path

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()

def pins(path):
    data = tomllib.loads(path.read_text())
    return {(p['name'], p['version'], json.dumps(p['source'], sort_keys=True)) for p in data['package']}

results = {}
for workspace in ('engine', 'neuron'):
    before = pins(Path(f'/tmp/f0011-{workspace}-before-rfc8785.lock'))
    after = pins(root / workspace / 'uv.lock')
    added = sorted(after - before)
    removed = sorted(before - after)
    passing = not removed and len(added) == 1 and added[0][:2] == ('rfc8785', '0.1.4')
    results[workspace] = {'status': 'pass' if passing else 'fail',
                          'added': [{'name': p[0], 'version': p[1]} for p in added],
                          'removed_or_upgraded': [{'name': p[0], 'version': p[1]} for p in removed]}
report = {'status': 'pass' if all(r['status'] == 'pass' for r in results.values()) else 'fail',
          'workspaces': results}
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if report['status'] == 'pass' else 1)
