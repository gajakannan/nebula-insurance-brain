import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

PRODUCT = Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
RUN = PRODUCT / 'planning-mds/operations/evidence/runs/2026-11-09-8b8456df'
PLAN = PRODUCT / 'planning-mds/operations/evidence/runs/2026-11-09-7c8e8461'
sys.path.insert(0, str(PRODUCT / 'engine/packages/brain-domain/src'))
from brain_domain.fact_answers import parse_answer, stored_answer
from brain_domain.fact_values import ValueType

out = []
for kind, key in [('money', 'amount'), ('decimal', 'value')]:
    value = {'type': kind, key: '1E+64'}
    if kind == 'money':
        value['currency'] = 'USD'
    answer = parse_answer({'answer_contract': 'fact-answer/v1', 'state': 'PRESENT', 'value': value}, value_type=ValueType(kind))
    canonical = answer.to_json()
    try:
        stored_answer(canonical)
        reload_result = 'PASS'
    except Exception as exc:
        reload_result = f'{type(exc).__name__}: {exc}'
    out.append({'probe': 'canonical-roundtrip', 'kind': kind, 'input': '1E+64', 'canonical_length': len(canonical['value'][key]), 'reload': reload_result})

source = (PRODUCT / 'engine/migrations/versions/0012_f0007_factslot_identity.py').read_text()
expr = source.split('ADD CONSTRAINT ck_fact_slot_identity CHECK (', 1)[1].split(';', 1)[0]
expr = '(' + expr
columns = """1::smallint AS identity_version, 'SLOT'::text AS slot_role,
'test:foo@v1'::text AS predicate_key, 'registry/1'::text AS predicate_release_ref,
'SINGLE'::text AS cardinality, NULL::uuid AS object_entity_id,
NULL::uuid AS parent_slot_id, NULL::text AS member_key,
1::smallint AS fingerprint_version, NULL::text AS identity_fingerprint,
'11111111-1111-1111-1111-111111111111'::uuid AS created_by,
'test:foo@v1'::text AS slot_type"""
for label, replacement in [('v1-null-fingerprint', columns), ('null-version-nonlegacy-fields', columns.replace('1::smallint AS identity_version', 'NULL::smallint AS identity_version').replace('NULL::text AS identity_fingerprint', "repeat('a',64)::text AS identity_fingerprint"))]:
    sql = f'WITH candidate AS (SELECT {replacement}), evaluated AS (SELECT {expr} AS check_result FROM candidate) SELECT check_result IS NULL AS check_returns_unknown, check_result IS NOT FALSE AS postgres_check_accepts FROM evaluated;'
    argv = ['docker', 'compose', 'exec', '-T', 'postgres', 'psql', '-U', 'brain', '-d', 'brain', '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1']
    proc = subprocess.run(argv, input=sql, text=True, capture_output=True, cwd=PRODUCT)
    out.append({'probe': label, 'exit_code': proc.returncode, 'result': proc.stdout.strip(), 'stderr': proc.stderr.strip(), 'sql': sql})

text = json.dumps(out, indent=2) + '\n'
(RUN / 'artifacts/architect-probes.json').write_text(text)
(PLAN / 'artifacts/architect-probes.json').write_text(text)
print(text)
record = {'schema_version': 1, 'timestamp': datetime.now(timezone.utc).isoformat(), 'cwd': str(PRODUCT), 'command': 'python3 /tmp/f0007_architecture_probes.py (domain roundtrip and read-only PostgreSQL SELECT probes)', 'exit_code': 0, 'artifacts': ['artifacts/architect-probes.json'], 'redactions': []}
for folder in (RUN, PLAN):
    with (folder / 'commands.log').open('a') as handle:
        handle.write(json.dumps(record) + '\n')
