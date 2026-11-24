"""Nonsecret, read-only local environment inventory for feature F0011."""
import hashlib
import importlib.metadata as metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from brain_api.config import Settings
from sqlalchemy.engine import make_url

root = Path('/app/brain')
selected = json.loads((root / 'scripts/contracts/environments.json').read_text())
base = make_url(Settings.from_env().database_url)
environments = {}
for label, target in selected.items():
    url = base.set(drivername='postgresql', **target)
    with psycopg.connect(url.render_as_string(hide_password=False)) as connection:
        connection.execute('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        environments[label] = {
            'database': connection.execute('SELECT current_database()').fetchone()[0],
            'server_version': connection.execute('SHOW server_version').fetchone()[0],
            'schema_version': connection.execute('SELECT version_num FROM alembic_version').fetchone()[0],
            'history_rows': connection.execute('SELECT count(*) FROM canonical_fact_version').fetchone()[0],
            'read_only': connection.execute('SHOW transaction_read_only').fetchone()[0],
            'extensions': dict(connection.execute('SELECT extname,extversion FROM pg_extension ORDER BY extname').fetchall()),
        }
        connection.rollback()
prior = {}
for package in ('brain-content', 'brain-contracts'):
    directory = root / f'engine/packages/{package}/src/{package.replace("-", "_")}/schemas'
    for source in sorted(directory.glob('*.json')):
        prior[str(source.relative_to(root))] = hashlib.sha256(source.read_bytes()).hexdigest()
report = {
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'python': platform.python_version(),
    'packages': {name: metadata.version(name) for name in ('pydantic', 'jsonschema', 'referencing', 'rfc3986-validator', 'datamodel-code-generator', 'build')},
    'environments': environments,
    'prior_common_bundle': None,
    'prior_package_schema_hashes': prior,
    'guard_rollout': 'not activated; candidate sweeps still required',
}
print(json.dumps(report, indent=2, sort_keys=True))
