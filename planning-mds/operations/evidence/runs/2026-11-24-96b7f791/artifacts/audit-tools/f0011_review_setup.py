import datetime as dt
import json
from pathlib import Path
import shlex
import subprocess

P = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
F = Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
R = P / 'planning-mds/operations/evidence/runs/2026-11-24-96b7f791'
BASE = 'eac6b5a72d028da09d79f0e2cde0262a4b4e5f5a'
HEAD = 'a125d2cdf1520b90150bf397d267c8a332039fdf'

def git(args, artifact):
    cmd = ['git'] + args
    cp = subprocess.run(cmd, cwd=P, capture_output=True, text=True)
    (R / artifact).parent.mkdir(parents=True, exist_ok=True)
    (R / artifact).write_text(cp.stdout + cp.stderr)
    with (R / 'commands.log').open('a') as out:
        out.write(json.dumps(dict(schema_version=1, timestamp=dt.datetime.now().astimezone().isoformat(),
                    cwd=str(P), command=shlex.join(cmd), exit_code=cp.returncode,
                    artifacts=[artifact], redactions=[])) + '\n')
    if cp.returncode:
        raise SystemExit(cp.stderr)
    return cp.stdout

local_head = git(['rev-parse', 'HEAD'], 'artifacts/diffs/local-head.txt').strip()
changed = git(['diff', '--name-only', '--no-renames', f'{BASE}..{HEAD}'], 'artifacts/diffs/changed-files.txt').splitlines()
git(['diff', '--name-status', '--no-renames', f'{BASE}..{HEAD}'], 'artifacts/diffs/changed-file-status.txt')
git(['status', '--porcelain=v1'], 'artifacts/diffs/initial-status.txt')
git(['rev-parse', 'HEAD:planning-mds/operations/evidence/runs/2026-11-22-885e8734'], 'artifacts/diffs/canonical-evidence-tree.txt')
identity = dict(product_root=str(P), framework_root=str(F), feature_id='F0011', mode='closeout-audit',
    feature_run_id='2026-11-22-885e8734', review_run_id=R.name,
    feature_path='planning-mds/features/archive/F0011-json-schema-contract-system',
    feature_run_folder='planning-mds/operations/evidence/runs/2026-11-22-885e8734',
    diff_range=f'{BASE}..{HEAD}', local_head=local_head, run_devops='yes',
    pr_url='https://github.com/gajakannan/nebula-insurance-brain/pull/64', changed_file_count=len(changed))
(R / 'artifacts/context/identity.json').write_text(json.dumps(identity, indent=2) + '\n')
(R / 'action-context.md').write_text('''# Action Context

## Run Identity

''' + ''.join(f'- **{k}:** {v}\n' for k, v in identity.items()) + '''
## Inputs

- NEBULA_PRODUCT_ROOT was supplied by the shell environment and normalized once by `_product_root.py`.
- Operator selected F0011. Connected GitHub discovery identified its merged implementation PR #64; planning PRs #61/#63 are not the implementation target.
- MODE derives from merged PR #64: closeout-audit. FEATURE_RUN_ID is the approved latest-run.json value.
- DIFF_RANGE uses PR #64's immutable base/head SHAs. A live origin/main range after merge would lose the feature changes.
- Changed paths: artifacts/diffs/changed-files.txt (complete Git name-only set, including archive moves as adds/deletes).
- RUN_DEVOPS=auto resolves to yes: runtime code, Docker build and CI changes, confirmed by the canonical manifest booleans.

## Assumptions

- Review the current checkout at the recorded PR head. The PR is merged but its feature branch remains checked out; no checkout mutation is necessary.
- Review-only untracked files created in this run are excluded from the implementation diff and tracked separately. Any other uncommitted work must be reported.
- No earlier feature approval establishes completion for this independent audit.

## Scope Boundaries

- F0011 only; cross-feature impact is recorded when relevant.
- Writes are limited to this review run and scratch helpers under /tmp. The canonical feature evidence package, code, tests, feature documents, closeout, trackers and KG are read-only.
- Raw evidence is read only through the manifest, cited role reports, validator findings, or explicitly required audit paths.
- Six role sections retain strict ownership. Four execution slots require pairing role lanes in three concurrent reviewer tasks; each lane has a separate section and self-review.
- Every post-initialization shell command is captured with the review telemetry helper. Pre-initialization reads are bootstrap activity; their paths are recorded in the artifact trace.

## Lifecycle Stage

- FR0 scope and diff locked; FR1 pending.
''')
print(json.dumps(identity, indent=2))
