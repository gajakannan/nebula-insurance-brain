#!/usr/bin/env python3
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
RUN = ROOT / 'planning-mds/operations/evidence/runs/2026-11-14-7cba50ff'

def append_json(path, obj):
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(obj) + '\n')
        fcntl.flock(stream, fcntl.LOCK_UN)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--artifact')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--gate')
    parser.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv and args.argv[0] == '--' else args.argv
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    env = dict(os.environ, NEBULA_PRODUCT_ROOT=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    start = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=args.cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=args.timeout)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b'')
        if isinstance(output, bytes):
            output = output.decode(errors='replace')
        output += '\nTIMEOUT\n'
        code = 124
    artifacts = []
    if args.artifact:
        target = RUN / args.artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output)
        artifacts.append(str(target.relative_to(ROOT)))
    record = dict(schema_version=1, timestamp=started, cwd=args.cwd,
                  command=shlex.join(argv), exit_code=code, artifacts=artifacts, redactions=[])
    append_json(RUN / 'commands.log', record)
    if args.gate:
        append_json(RUN / 'lifecycle-gates.log', dict(record, stage=args.gate,
                    elapsed_seconds=round(time.monotonic()-start, 3),
                    summary=output[-1200:]))
    sys.stdout.write(output)
    sys.exit(code)

if __name__ == '__main__':
    main()
