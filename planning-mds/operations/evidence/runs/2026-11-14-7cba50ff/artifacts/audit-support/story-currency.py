import difflib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
framework = Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
review = root / 'planning-mds/operations/evidence/runs/2026-11-14-7cba50ff'
source = root / 'planning-mds/features'
temporary = Path(tempfile.mkdtemp(prefix='f0064-story-currency-'))
copied = temporary / 'features'
shutil.copytree(source, copied, symlinks=True)
argv = ['python3', str(framework / 'agents/product-manager/scripts/generate-story-index.py'),
        '--product-root', str(root), str(copied)]
result = subprocess.run(argv, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                        capture_output=True, text=True)
print('Canonical root:', root)
print('Isolated copy:', copied)
print('Generator stdout:', result.stdout)
print('Generator stderr:', result.stderr)
print('Generator exit:', result.returncode)
if result.returncode:
    sys.exit(result.returncode)
original = (source / 'STORY-INDEX.md').read_text()
generated = (copied / 'STORY-INDEX.md').read_text()
diff = ''.join(difflib.unified_diff(original.splitlines(True), generated.splitlines(True),
                                 fromfile='canonical/STORY-INDEX.md', tofile='generated/STORY-INDEX.md'))
(review / 'artifacts/diffs/story-index-currency.diff').write_text(diff)
print('Story index byte-identical:', original == generated)
print(diff)
sys.exit(0 if original == generated else 1)
