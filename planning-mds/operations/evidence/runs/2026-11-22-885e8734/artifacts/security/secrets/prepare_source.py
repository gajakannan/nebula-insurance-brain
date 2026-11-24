"""Prepare path/hash inventory, keeping source bytes out of durable scan evidence."""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
run = root / 'planning-mds/operations/evidence/runs/2026-11-22-885e8734'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
selection = run / 'artifacts/security/sast/prepare_source.py'
spec = importlib.util.spec_from_file_location('f0011_source_selection', selection)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
paths = module.selected_paths()
for relative in paths:
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or '\n' in relative or '\r' in relative:
        raise ValueError('Unsafe source path')
    if (root / path).is_symlink():
        raise ValueError('Symlink source requires explicit review')
inputs = args.output / 'inputs'
reports = args.output / 'reports'
inputs.mkdir(parents=True, exist_ok=True)
reports.mkdir(exist_ok=True)
(inputs / 'paths.txt').write_text('\n'.join(paths) + '\n')
record = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Existing changed and untracked feature source, all extensions; cold evidence and caches excluded.',
          'source_bytes_stored': False,
          'files': [{'path': p, 'sha256': hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths]}
(args.output / 'source-inputs.json').write_text(json.dumps(record, indent=2) + '\n')
script = '''#!/bin/sh
set -eu
stage=/tmp/f0011-secrets-source
mkdir -p "$stage"
while IFS= read -r relative; do
    [ -n "$relative" ] || continue
    parent=$(dirname "$relative")
    mkdir -p "$stage/$parent"
    cp "/scan/$relative" "$stage/$relative"
done < /inputs/paths.txt
sh /framework/agents/security/scripts/check-secrets.sh --path "$stage" --mode filesystem --report-dir /reports -- --no-git
'''
(inputs / 'run.sh').write_text(script)
print(json.dumps({'files': len(paths), 'source_manifest': str(args.output/'source-inputs.json'), 'source_bytes_stored': False}))
