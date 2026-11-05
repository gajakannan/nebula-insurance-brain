"""Refresh unreleased 0011 only in this run's empty-v2 validation database."""
import hashlib
import json
import os
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config

url = 'postgresql://brain:brain@postgres:5432/brain_f0006_runtime'
def fingerprint():
    with psycopg.connect(url) as connection:
        assert connection.execute('SELECT current_database()').fetchone()[0] == 'brain_f0006_runtime'
        for table in ('assertion_semantics', 'assertion_document_reference', 'assertion_name_claim'):
            assert connection.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0
        assert connection.execute('SELECT count(*) FROM assertion WHERE semantic_contract_version=2').fetchone()[0] == 0
        return connection.execute(
            "SELECT md5(coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.id)::text,'[]')) FROM assertion a"
        ).fetchone()[0]

before = fingerprint()
os.environ['BRAIN_DATABASE_URL'] = url.replace('postgresql://', 'postgresql+psycopg://')
config = Config('engine/migrations/alembic.ini')
config.set_main_option('script_location', str(Path('engine/migrations').resolve()))
command.downgrade(config, '0010')
command.upgrade(config, '0011')
after = fingerprint()
assert before == after
with psycopg.connect(url) as connection:
    function = connection.execute(
        "SELECT pg_get_functiondef('brain_assertion_v2_integrity'::regproc)"
    ).fetchone()[0]
assert 'e.page IS NOT DISTINCT FROM' in function and 'NULLIF(e.bbox::jsonb' in function
result = {'result':'PASS','database':'brain_f0006_runtime','legacy_rows_unchanged':before==after,
          'v2_tables_empty_before_refresh':True,'page_and_bbox_guard_deployed':True,
          'function_sha256':hashlib.sha256(function.encode()).hexdigest()}
Path('planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/artifacts/runtime/migration-carrier-refresh.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
