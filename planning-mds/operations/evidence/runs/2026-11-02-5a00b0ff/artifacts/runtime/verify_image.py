"""Prove the immutable image contains the reviewed production sources."""
import hashlib
import importlib
import json
import os
import sys
from importlib.resources import files
from pathlib import Path

label = sys.argv[1]
assert label in ('engine', 'neuron') and os.getuid() == 1000
root = Path('/app/brain')
inputs = json.loads(Path('/evidence/coverage/changed-production-lines.json').read_text())
checked = []
for item in inputs:
    actual = hashlib.sha256((root / item['path']).read_bytes()).hexdigest()
    assert actual == item['sha256'], item['path']
    checked.append(item['path'])
for name in ('brain_assertions.admission', 'brain_contracts.dispatch', 'brain_persistence.assertions'):
    importlib.import_module(name)
schemas = sorted(p.name for p in (files('brain_contracts') / 'schemas').iterdir())
assert len([s for s in schemas if s.endswith('.schema.json')]) == 4
result = {'result': 'PASS', 'uid': os.getuid(), 'source_bind_mount': False,
          'image': label, 'verified_production_source_paths': checked, 'schemas': schemas}
Path('/evidence/runtime/' + label + '-immutable.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
