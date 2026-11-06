"""Measure executable changed lines, retaining per-file misses and raw inputs."""
import hashlib
import json
from pathlib import Path
import yaml

root = Path('/app/brain')
run = root / 'planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff'
data = run / 'artifacts/coverage'
inputs = ['engine-changed.json', 'neuron-importer.json']
merged = {}
for name in inputs:
    for filename, measured in json.loads((data / name).read_text())['files'].items():
        path = Path(filename)
        absolute = path if path.is_absolute() else root / path
        relative = str(absolute.resolve().relative_to(root))
        covered, executable = merged.setdefault(relative, (set(), set()))
        covered.update(measured['executed_lines'])
        executable.update(measured['executed_lines'])
        executable.update(measured['missing_lines'])
rows, missing_instrumentation = [], []
for item in json.loads((data / 'changed-production-lines.json').read_text()):
    path = item['path']
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == item['sha256'], path
    if path not in merged:
        if (root / path).read_text().strip():
            missing_instrumentation.append(path)
        continue
    covered, executable = merged[path]
    changed = set(item['changed_lines']) & executable
    misses = sorted(changed - covered)
    rows.append({'path': path, 'changed_executable_lines': len(changed),
                 'covered_lines': len(changed & covered), 'missing_lines': misses})
denominator = sum(row['changed_executable_lines'] for row in rows)
numerator = sum(row['covered_lines'] for row in rows)
contract = yaml.safe_load(Path('/app/framework/agents/actions/spec/_contract.yaml').read_text())
def find_floor(value):
    if isinstance(value, dict):
        if 'coverage_min_pct' in value:
            return value['coverage_min_pct']
        for child in value.values():
            found = find_floor(child)
            if found is not None:
                return found
floor = find_floor(contract)
assert isinstance(floor, (int, float))
pct = 100 * numerator / denominator
result = {'method': 'git HEAD diff added/modified executable lines plus new production Python files; union of container coverage observations',
          'inputs': inputs, 'covered_lines': numerator, 'executable_lines': denominator,
          'coverage_pct': round(pct, 4), 'coverage_min_pct_from_contract': floor,
          'missing_instrumentation': missing_instrumentation, 'files': rows,
          'result': 'PASS' if pct >= floor and not missing_instrumentation else 'FAIL'}
(data / 'changed-code-summary.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2))
assert result['result'] == 'PASS'
