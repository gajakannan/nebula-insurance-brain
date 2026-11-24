#!/usr/bin/env python3
"""Record read-only F0011 review commands in the separate review package."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

PRODUCT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
FRAMEWORK = Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
REVIEW = PRODUCT / 'planning-mds/operations/evidence/runs/2026-11-24-96b7f791'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cwd', default=str(PRODUCT))
    p.add_argument('--artifact', required=True)
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--quiet', action='store_true')
    p.add_argument('argv', nargs=argparse.REMAINDER)
    a = p.parse_args()
    argv = a.argv[1:] if a.argv[:1] == ['--'] else a.argv
    dest = (REVIEW / a.artifact).resolve()
    if REVIEW not in dest.parents:
        raise SystemExit('artifact must stay in the review run')
    dest.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, NEBULA_PRODUCT_ROOT=str(PRODUCT), PYTHONDONTWRITEBYTECODE='1')
    started = dt.datetime.now().astimezone().isoformat()
    clock = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=a.cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=a.timeout)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as exc:
        output, code = (exc.stdout or b'') + b'\nTIMEOUT\n', 124
    dest.write_bytes(output)
    record = {'schema_version': 1, 'timestamp': started, 'cwd': a.cwd,
              'command': shlex.join(argv), 'exit_code': code,
              'artifacts': [a.artifact], 'redactions': []}
    with (REVIEW / 'commands.log').open('a') as log:
        log.write(json.dumps(record) + '\n')
    if not a.quiet:
        sys.stdout.buffer.write(output)
    print(json.dumps({'exit_code': code, 'artifact': str(dest),
                      'duration_seconds': round(time.monotonic() - clock, 3)}))
    return code

if __name__ == '__main__':
    raise SystemExit(main())
