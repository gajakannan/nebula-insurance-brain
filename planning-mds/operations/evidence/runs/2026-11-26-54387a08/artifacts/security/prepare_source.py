"""Copy the run's changed files (from artifacts/diffs/changed-files.txt) into scan inputs.

secrets/source: every changed text file; sast/source: changed Python/JS sources.
Writes source-inputs.json with path + sha256 so reviewers can reconcile inputs.
"""
import hashlib, json, shutil
from pathlib import Path
root = Path(__file__).resolve().parents[7]
run = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
changed = [l for l in (run / 'artifacts/diffs/changed-files.txt').read_text().split() if l]
inputs = {'secrets': [], 'sast': []}
for target in ('secrets', 'sast'):
    dest = here / target / 'source'
    if dest.exists():
        shutil.rmtree(dest)
for rel in changed:
    src = root / rel
    if not src.is_file() or '/artifacts/security/' in rel:
        continue
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    for target in ('secrets', 'sast'):
        if target == 'sast' and not rel.endswith(('.py', '.mjs', '.js', '.ts', '.tsx')):
            continue
        out = here / target / 'source' / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        inputs[target].append({'path': rel, 'sha256': digest})
(here / 'source-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
print({k: len(v) for k, v in inputs.items()})
