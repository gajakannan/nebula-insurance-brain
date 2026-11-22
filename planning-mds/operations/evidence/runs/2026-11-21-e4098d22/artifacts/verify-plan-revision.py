from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import yaml

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
feature = root / 'planning-mds/features/F0011-json-schema-contract-system'

def baseline(path):
    return subprocess.check_output(['git', 'show', f'HEAD:{path.relative_to(root)}'], cwd=root, text=True)

inventory = yaml.safe_load((feature / 'contract-inventory.yaml').read_text())
old_inventory = yaml.safe_load(baseline(feature / 'contract-inventory.yaml'))
old_by_name = {r['name']: r for r in old_inventory['resources']}
assert len(inventory['resources']) == len(old_by_name) == 21
assert len({r['id'] for r in inventory['resources']}) == 21
existing_paths = set()
planned_paths = set()
for resource in inventory['resources']:
    old = old_by_name[resource['name']]
    for key in ('name', 'id', 'version', 'source', 'source_sha256_at_design', 'owner'):
        assert resource[key] == old[key], (resource['name'], key)
    source = root / resource['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == resource['source_sha256_at_design']
    assert resource['disposition'] in {'adopt', 'delegate', 'retain-versioned-boundary'}
    assert resource['version_selector'] and resource['wire_profile'] in {'native-compat/v1', 'portable-json/v1'}
    assert resource['consumer_entry_points'] and resource['compatibility_tests']
    for item in resource['consumer_entry_points'] + resource['compatibility_tests']:
        path = root / item['path']
        assert path.resolve().is_relative_to(root)
        if item['state'] in {'existing', 'OpenAPI/doc-only'}:
            assert path.is_file(), (resource['name'], item['path'])
            existing_paths.add(item['path'])
        else:
            assert item['state'] == 'planned'
            planned_paths.add(item['path'])
    if resource['name'] in {'content-artifact-manifest-read', 'problem-details'}:
        assert resource['disposition'] == 'retain-versioned-boundary'
        assert all(i['state'] == 'OpenAPI/doc-only' for i in resource['consumer_entry_points'])

stories = sorted(feature.glob('F0011-S*.md'))
assert len(stories) == 6
total_acs = 0
for path in stories:
    old = baseline(path)
    current = path.read_text()
    assert current == old.replace('**I want** ', '**I want** to '), path
    criteria = re.findall(r'^- \[ \] \*\*F0011-S\d{4}-AC\d+:\*\*.*$', current, re.M)
    total_acs += len(criteria)
assert total_acs == 41, total_acs

changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=root, text=True).splitlines()
assert not any(p.startswith(('engine/', 'neuron/', 'experience/', 'scripts/', 'planning-mds/schemas/', 'planning-mds/api/', 'planning-mds/architecture/decisions/')) for p in changed)
prd_path = feature / 'PRD.md'
assert prd_path.read_text() == baseline(prd_path).replace(
    '**Plan Run:** 2026-11-20-ccb1bd39 (A+B; feature mode new)\n',
    '**Plan Run:** 2026-11-20-ccb1bd39 (A+B; feature mode new)\n'
    '**Plan Revision:** 2026-11-21-e4098d22 (Phase B, existing; pending G5 approval). Requirements and 41 ACs are unchanged; the revision specifies the review\'s compatibility proof and consumer mapping.\n')
subprocess.run(['git', 'diff', '--check'], cwd=root, check=True)
print(json.dumps({'status': 'pass', 'resources': 21, 'source_hashes_unchanged': 21,
                  'existing_consumer_test_paths_checked': len(existing_paths),
                  'planned_paths_explicitly_marked': len(planned_paths),
                  'stories': 6, 'unchanged_numbered_acs': total_acs,
                  'runtime_schema_api_adr_edits': 0,
                  'dispositions': dict(Counter(r['disposition'] for r in inventory['resources']))}, indent=2))
