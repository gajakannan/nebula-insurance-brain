"""Audit one final installed Python workspace; never install or fix product packages."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path('/app/brain')
out = root / 'planning-mds/operations/evidence/runs/2026-11-22-885e8734/artifacts/security/dependency'
workspace = os.environ['F0011_DEP_WORKSPACE']
if workspace not in {'engine', 'neuron'}:
    raise SystemExit(2)
lock = root / workspace / 'uv.lock'
before = hashlib.sha256(lock.read_bytes()).hexdigest()
prefix = Path(os.environ['UV_PROJECT_ENVIRONMENT'])
site = prefix / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
requirements = out / f'{workspace}-exact-requirements.txt'
inventory = out / f'{workspace}-installed-inventory.json'
collection = subprocess.run([str(prefix/'bin/python'), str(out/'collect_installed.py'),
                             '--workspace', workspace, '--requirements', str(requirements),
                             '--inventory', str(inventory)], text=True, capture_output=True)
(out / f'{workspace}-collection.log').write_text(collection.stdout + collection.stderr)
if collection.returncode:
    print(collection.stderr, file=sys.stderr)
    raise SystemExit(2)
output = out / f'{workspace}.json'
env = dict(os.environ, UV_TOOL_DIR='/tmp/f0011-uv-tools', UV_TOOL_BIN_DIR='/tmp/f0011-uv-bin')
command = ['uv', 'tool', 'run', '--from', 'pip-audit==2.10.1', 'pip-audit',
           '--requirement', str(requirements), '--no-deps', '--disable-pip',
           '--strict', '--progress-spinner', 'off',
           '--format', 'json', '--output', str(output), '--cache-dir', '/tmp/f0011-audit-cache',
           '--timeout', '30']
result = subprocess.run(command, env=env, text=True, capture_output=True)
(out / f'{workspace}-auditor.log').write_text(result.stdout + result.stderr)
after = hashlib.sha256(lock.read_bytes()).hexdigest()
record = {'workspace': workspace, 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'tool': 'pip-audit 2.10.1', 'argv': command, 'target_site_packages': str(site),
          'lock_sha256_before': before, 'lock_sha256_after': after,
          'lock_unchanged': before == after, 'audit_exit_code': result.returncode,
          'editable_project_packages_skipped': json.loads(inventory.read_text())['omitted_editable_workspace_packages'],
          'all_installed_third_party_pins_audited': True, 'product_fix_requested': False}
(out / f'{workspace}-execution.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'workspace': workspace, 'audit_exit_code': result.returncode,
                  'lock_unchanged': before == after, 'artifact': str(output)}))
raise SystemExit(result.returncode if before == after else 2)
