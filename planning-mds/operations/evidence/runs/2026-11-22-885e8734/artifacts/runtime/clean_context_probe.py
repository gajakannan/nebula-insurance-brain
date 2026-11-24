"""Hash only F0011 build inputs; never read credentials or local runtime data."""
import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path

import yaml

root = Path('/app/brain')
parser = argparse.ArgumentParser()
parser.add_argument('--require-clean', action='store_true')
args = parser.parse_args()
excluded = ['.git', '.env', 'engine/.venv', 'neuron/.venv',
            'experience/node_modules', 'planning-mds/operations']
absent = {name: not (root / name).exists() for name in excluded}
if args.require_clean and not all(absent.values()):
    raise AssertionError('Host-local input entered the clean engine build')

def tree(paths):
    rows = []
    for path in sorted(paths):
        if path.is_file() and path.suffix in {'.py', '.json', '.yaml', '.mjs', '.toml', '.lock'}:
            rows.append(f'{path.relative_to(root)} {hashlib.sha256(path.read_bytes()).hexdigest()}')
    return {'files': len(rows), 'sha256': hashlib.sha256('\n'.join(rows).encode()).hexdigest()}

inventory = yaml.safe_load((root / 'scripts/contracts/sources.yaml').read_text())
groups = {name: tree((root / name).rglob('*')) for name in (
    'scripts/contracts', 'engine/packages/brain-contracts/src/brain_contracts',
    'schemas/contracts/v1', 'experience/scripts/contracts',
    'experience/src/generated/contracts/v1')}
groups['authored-selected-schemas'] = tree(root / item['source'] for item in inventory['resources'])
selected = ['.dockerignore', 'docker/contracts/Dockerfile', 'engine/pyproject.toml',
            'engine/uv.lock', 'neuron/uv.lock', 'experience/package.json',
            'experience/pnpm-lock.yaml', 'planning-mds/api/brain-api.yaml']
hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in selected}
report = {'uid': os.getuid(), 'excluded_paths_absent': absent, 'source_groups': groups,
          'selected_input_hashes': hashes,
          'bundle_digest': hashlib.sha256((root/'schemas/contracts/v1/manifest.json').read_bytes()).hexdigest(),
          'versions': {name: metadata.version(name) for name in ('pydantic','jsonschema','referencing','datamodel-code-generator')}}
print(json.dumps(report, indent=2, sort_keys=True))
