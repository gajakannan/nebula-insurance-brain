"""Run the stock story-index CLI against a temporary mirror, never the canonical tree."""
import datetime as dt
import difflib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

P = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
F = Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
R = P / 'planning-mds/operations/evidence/runs/2026-11-24-96b7f791'
source = P / 'planning-mds/features'
with tempfile.TemporaryDirectory(prefix='f0011-review-currency-') as tmp:
    mirror = Path(tmp) / 'features'
    mirror.mkdir()
    count = 0
    for path in source.rglob('*.md'):
        if re.match(r'F\d{4}-S\d{4}', path.name):
            target = mirror / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            count += 1
    argv = [sys.executable, str(F / 'agents/product-manager/scripts/generate-story-index.py'),
            '--product-root', str(P), str(mirror)]
    started = dt.datetime.now().astimezone().isoformat()
    cp = subprocess.run(argv, cwd=F, env=dict(os.environ, NEBULA_PRODUCT_ROOT=str(P),
                        PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=300)
    (R / 'artifacts/validators/story-index-generator.txt').write_text(cp.stdout + cp.stderr)
    with (R / 'commands.log').open('a') as log:
        log.write(json.dumps(dict(schema_version=1, timestamp=started, cwd=str(F),
            command=shlex.join(argv), exit_code=cp.returncode,
            artifacts=['artifacts/validators/story-index-generator.txt'], redactions=[])) + '\n')
    if cp.returncode:
        print(cp.stdout + cp.stderr)
        raise SystemExit(cp.returncode)
    generated = (mirror / 'STORY-INDEX.md').read_text()
    canonical = (source / 'STORY-INDEX.md').read_text()
    (R / 'artifacts/validators/STORY-INDEX.generated.md').write_text(generated)
    delta = ''.join(difflib.unified_diff(canonical.splitlines(True), generated.splitlines(True),
                     fromfile='canonical/STORY-INDEX.md', tofile='regenerated/STORY-INDEX.md'))
    (R / 'artifacts/diffs/story-index-currency.diff').write_text(delta)
    print(json.dumps({'story_files': count, 'generator_exit_code': cp.returncode,
          'currency': 'FAIL' if delta else 'PASS', 'canonical_write': False,
          'method': 'stock CLI on a temporary mirror of all story files, preserving relative paths',
          'diff_artifact': 'artifacts/diffs/story-index-currency.diff'}, indent=2))
    raise SystemExit(1 if delta else 0)
