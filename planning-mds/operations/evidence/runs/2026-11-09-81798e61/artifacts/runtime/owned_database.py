"""Execute a validation command against a fresh database, then drop only that database."""
import os
from pathlib import Path
import secrets
import subprocess
import sys

import psycopg
from psycopg import sql

root = Path('/app/brain')
admin = os.environ['BRAIN_MIGRATION_ADMIN_URL']
name = 'f0007_remediation_' + secrets.token_hex(6)
with psycopg.connect(admin, autocommit=True) as c:
    c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
url = admin.rsplit('/', 1)[0] + '/' + name
env = dict(os.environ)
env.update(BRAIN_DATABASE_URL=url.replace('postgresql://', 'postgresql+psycopg://'))
try:
    with psycopg.connect(url, autocommit=True) as c:
        c.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=root/'engine/migrations', env=env, check=True)
    env.update(BRAIN_DATABASE_URL=url.replace('postgresql://','postgresql+asyncpg://'),
               BRAIN_WORKER_DATABASE_URL=url.replace('postgresql://','postgresql+psycopg://'),
               BRAIN_TEST_POSTGRES_URL=url.replace('postgresql://','postgresql+psycopg://'))
    print('Owned migrated validation database:', name, flush=True)
    command = sys.argv[1:]
    if command and command[0] == '--': command.pop(0)
    result = subprocess.run(command, cwd=root, env=env)
    sys.exit(result.returncode)
finally:
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    print('Removed owned validation database:', name, flush=True)
