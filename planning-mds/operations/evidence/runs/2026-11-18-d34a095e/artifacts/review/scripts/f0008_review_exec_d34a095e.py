import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
FRAMEWORK = ROOT.parent / 'nebula-agents'
RUN = ROOT / 'planning-mds/operations/evidence/runs/2026-11-18-d34a095e'
BOOTSTRAP = Path('/tmp/f0008-review-d34a095e-bootstrap.jsonl')

def append(path, row):
    with path.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write(json.dumps(row) + '\n')
        handle.flush()

def run(command, cwd=FRAMEWORK, output=None, timeout=300):
    stamp = datetime.datetime.now().astimezone().isoformat()
    env = dict(os.environ, NEBULA_PRODUCT_ROOT=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    try:
        result = subprocess.run(command, shell=True, executable='/usr/bin/zsh', cwd=cwd,
                                env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
        code, text = result.returncode, result.stdout
    except subprocess.TimeoutExpired as exc:
        code, text = 124, (exc.stdout or b'').decode() if isinstance(exc.stdout, bytes) else (exc.stdout or '')
    artifacts = []
    if output:
        dest = RUN / output
        if RUN not in dest.resolve().parents:
            raise ValueError('Output must be in review run')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
        artifacts.append(str(dest.relative_to(ROOT)))
    log = RUN / 'commands.log' if RUN.is_dir() else BOOTSTRAP
    append(log, dict(schema_version=1, timestamp=stamp, cwd=str(cwd), command=command,
                     exit_code=code, artifacts=artifacts, redactions=[]))
    if RUN.is_dir() and BOOTSTRAP.exists():
        for line in BOOTSTRAP.read_text().splitlines():
            append(RUN / 'commands.log', json.loads(line))
        BOOTSTRAP.unlink()
    return code, text

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cwd', default=str(FRAMEWORK))
    parser.add_argument('--output')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('command')
    args = parser.parse_args()
    code, text = run(args.command, args.cwd, args.output, args.timeout)
    print(text, end='')
    sys.exit(code)
