"""Collect and lock-verify every installed third-party pin in the actual venv."""
import argparse
import importlib.metadata as metadata
import json
import os
import re
import sys
import sysconfig
import tomllib
from pathlib import Path

from packaging.markers import Marker

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', choices=('engine', 'neuron'), required=True)
parser.add_argument('--requirements', type=Path, required=True)
parser.add_argument('--inventory', type=Path, required=True)
args = parser.parse_args()
root = Path('/app/brain')
prefix = Path(sys.prefix).resolve()
if prefix != Path(os.environ['UV_PROJECT_ENVIRONMENT']).resolve():
    raise RuntimeError('Collector must run inside the actual candidate virtualenv')
locked = tomllib.loads((root / args.workspace / 'uv.lock').read_text())['package']
normalize = lambda name: re.sub(r'[-_.]+', '-', name).lower()
sites = sorted({sysconfig.get_path('purelib'), sysconfig.get_path('platlib')})
pins = {}
omitted = []
for distribution in metadata.distributions(path=sites):
    name = normalize(distribution.metadata['Name'])
    version = distribution.version
    candidates = [package for package in locked
                  if normalize(package['name']) == name and package['version'] == version
                  and (not package.get('resolution-markers') or any(
                      Marker(marker).evaluate() for marker in package['resolution-markers']))]
    if len(candidates) != 1:
        raise RuntimeError(f'Installed pin has no unique active lock match: {name}=={version}')
    direct = json.loads(distribution.read_text('direct_url.json') or '{}')
    if direct.get('dir_info', {}).get('editable'):
        if not name.startswith('brain-'):
            raise RuntimeError(f'Unexpected third-party editable package: {name}')
        omitted.append({'name': name, 'version': version,
                        'reason': 'Actual editable workspace source; reviewed by SAST and code/security roles.'})
        continue
    if name in pins and pins[name] != version:
        raise RuntimeError(f'Conflicting installed versions: {name}')
    pins[name] = version
if not pins:
    raise RuntimeError('No third-party dependencies collected')
args.requirements.write_text(''.join(f'{name}=={pins[name]}\n' for name in sorted(pins)))
record = {'workspace': args.workspace, 'python': sys.version.split()[0],
          'actual_venv': str(prefix), 'site_packages': sites,
          'all_pins_match_active_lock': True, 'third_party_pins': pins,
          'third_party_count': len(pins), 'omitted_editable_workspace_packages': omitted}
args.inventory.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'workspace': args.workspace, 'third_party_count': len(pins),
                  'omitted_editable_workspace_count': len(omitted)}))
