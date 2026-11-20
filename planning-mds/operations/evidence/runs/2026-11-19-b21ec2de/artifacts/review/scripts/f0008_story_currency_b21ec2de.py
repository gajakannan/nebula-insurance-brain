import difflib
import hashlib
import json
import re
import shlex
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, '/tmp')
from f0008_review2_exec_b21ec2de import ROOT, FRAMEWORK, RUN, run

source = ROOT / 'planning-mds/features'
mirror = Path(tempfile.mkdtemp(prefix='f0008-currency-b21ec2de-')) / 'features'
mirror.mkdir()
stories = [p for p in source.rglob('*.md') if re.match(r'F\d{4}-S\d{4}', p.name)]
for path in stories:
    target = mirror / path.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(path.read_bytes())
original = (source / 'STORY-INDEX.md').read_bytes()
command = shlex.join(['python3', 'agents/product-manager/scripts/generate-story-index.py',
                      '--product-root', str(ROOT), str(mirror)])
code, output = run(command, FRAMEWORK, 'artifacts/test-results/fr2-story-index-generator.txt')
if code:
    print(output)
    sys.exit(code)
generated = (mirror / 'STORY-INDEX.md').read_bytes()
delta = ''.join(difflib.unified_diff(original.decode().splitlines(True), generated.decode().splitlines(True),
                                    fromfile='committed/STORY-INDEX.md', tofile='regenerated/STORY-INDEX.md'))
(RUN / 'artifacts/diffs/fr2-story-index-currency.diff').write_text(delta)
data = {'stories': len(stories), 'generator_exit_code': code, 'currency_pass': not delta,
        'original_sha256': hashlib.sha256(original).hexdigest(),
        'generated_sha256': hashlib.sha256(generated).hexdigest(),
        'protected_original_unchanged': (source / 'STORY-INDEX.md').read_bytes() == original,
        'mirror': str(mirror), 'method': 'Same generator on byte-identical story files at identical relative paths; writes confined to temporary mirror.'}
(RUN / 'artifacts/test-results/fr2-story-index-currency.json').write_text(json.dumps(data, indent=2)+'\n')
with (RUN / 'lifecycle-gates.log').open('a') as handle:
    handle.write(f'\n### FR2 — Story-index currency\nCommand: {command}\nStage: FR2\nExit Code: {code}\nResult: {"PASS" if not delta else "FAIL"}\nSummary: {len(stories)} stories; {len(delta.splitlines())} diff lines; original unchanged.\nOutput References: artifacts/test-results/fr2-story-index-currency.json, artifacts/diffs/fr2-story-index-currency.diff\nSkipped Gates: -\n')
print(json.dumps(data, indent=2))
sys.exit(0 if not delta else 1)
