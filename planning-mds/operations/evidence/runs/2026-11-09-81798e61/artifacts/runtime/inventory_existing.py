"""Read-only rollout inventory. Emit counts/IDs only; never repair fact evidence."""
import importlib.util
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from brain_domain.fact_answers import parse_answer
from brain_domain.fact_slots import PredicateKey, member_key
from brain_factslots.predicates import production_registry

root = Path('/app/brain')
spec = importlib.util.spec_from_file_location('guard0013', root/'engine/migrations/versions/0013_f0007_identity_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
summary = {'mode': 'read-only; no repair', 'samples': {}}
with psycopg.connect(os.environ['BRAIN_MIGRATION_ADMIN_URL'], row_factory=dict_row) as c:
    c.execute('SET TRANSACTION READ ONLY')
    summary['database_revision'] = c.execute('SELECT version_num FROM alembic_version').fetchone()['version_num']
    adopted = c.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='fact_slot' AND column_name='identity_version') AS adopted").fetchone()['adopted']
    if not adopted:
        summary.update(status='not-adopted', identity_v1_rows=0, note='Database predates F0007 columns; no canonical numeric/member carriers are adopted here.')
    else:
        summary['identity_v1_rows'] = c.execute('SELECT count(*) AS n FROM fact_slot WHERE identity_version=1').fetchone()['n']
        malformed = c.execute(f'SELECT id FROM fact_slot WHERE ({guard.IDENTITY_SHAPE}) IS NOT TRUE ORDER BY id').fetchall()
        summary['malformed_identity_count'] = len(malformed)
        summary['samples']['malformed_slot_ids'] = [str(r['id']) for r in malformed[:10]]
        counters = dict(oversized_numeric=0, member_mismatch=0, unverified_contract=0, invalid_carrier=0)
        registry = production_registry()
        rows = c.execute('SELECT v.id,v.value,s.slot_role,s.member_key,s.predicate_key,s.predicate_release_ref FROM canonical_fact_version v JOIN fact_slot s ON s.id=v.slot_id WHERE s.identity_version=1')
        for row in rows:
            value = row['value']
            typed = value.get('value', {}) if isinstance(value, dict) else {}
            numeric = typed.get('amount') if typed.get('type') == 'money' else typed.get('value') if typed.get('type') == 'decimal' else None
            issue = None
            if isinstance(numeric, str) and len(numeric) > 64:
                issue = 'oversized_numeric'
            else:
                contract = registry.find(PredicateKey.parse(row['predicate_key']), row['predicate_release_ref'])
                if contract is None:
                    issue = 'unverified_contract'
                else:
                    try:
                        answer = parse_answer(value, value_type=contract.value_type, basis_required=contract.basis_required)
                        if row['slot_role'] == 'MEMBER' and answer.value is not None and member_key(answer.value, contract) != row['member_key']:
                            issue = 'member_mismatch'
                    except ValueError:
                        issue = 'invalid_carrier'
            if issue:
                counters[issue] += 1
                samples = summary['samples'].setdefault(issue+'_version_ids', [])
                if len(samples) < 10: samples.append(str(row['id']))
        summary.update(counters)
        summary['status'] = 'requires-governed-resolution' if malformed or any(counters.values()) else 'clean'
print(json.dumps(summary, indent=2))
raise SystemExit(1 if summary['status'] == 'requires-governed-resolution' else 0)
