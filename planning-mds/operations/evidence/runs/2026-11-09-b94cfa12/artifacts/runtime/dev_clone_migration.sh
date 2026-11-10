#!/usr/bin/env bash
# F0007 deployability: apply 0011+0012 to a CLONE of the local dev database, prove
# downgrade to 0011 and re-upgrade, and compare pilot fact rows before and after.
# The shared dev database itself is only read (pg_dump).
set -euo pipefail
PR=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
NAME="f0007_devclone_$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
URL="postgresql+psycopg://brain:brain@localhost:5432/$NAME"
docker exec brain-postgres psql -U brain -d brain -qAtc "CREATE DATABASE $NAME"
trap 'docker exec brain-postgres psql -U brain -d brain -qAtc "DROP DATABASE $NAME WITH (FORCE)" >/dev/null; echo "dropped $NAME"' EXIT
docker exec brain-postgres sh -c "pg_dump -U brain -d brain | psql -q -U brain -d $NAME" >/dev/null
snap() {
  docker exec brain-postgres psql -U brain -d "$NAME" -qAtc \
    "SELECT md5(string_agg(t, '|' ORDER BY t)) FROM (
       SELECT (s.id, s.entity_id, s.slot_type, s.tenant_id, s.knowledge_base_id, s.created_at)::text t FROM fact_slot s
       UNION ALL SELECT v::text FROM canonical_fact_version v
       UNION ALL SELECT c::text FROM canonical_fact_change c) x"
}
rev() { docker exec brain-postgres psql -U brain -d "$NAME" -qAtc "SELECT version_num FROM alembic_version"; }
counts() { docker exec brain-postgres psql -U brain -d "$NAME" -qAtc "SELECT (SELECT count(*) FROM fact_slot)||' slots, '||(SELECT count(*) FROM canonical_fact_version)||' versions'"; }
cd "$PR/engine/migrations"
echo "clone at $(rev): $(counts); pilot hash $(snap)"
BRAIN_DATABASE_URL=$URL ../.venv/bin/alembic upgrade head 2>&1 | grep -E "Running|preflight"
echo "after upgrade at $(rev): pilot hash $(snap)"
BRAIN_DATABASE_URL=$URL ../.venv/bin/alembic downgrade 0011 2>&1 | grep -E "Running"
echo "after downgrade at $(rev): pilot hash $(snap)"
BRAIN_DATABASE_URL=$URL ../.venv/bin/alembic upgrade head 2>&1 | grep -E "Running"
echo "after re-upgrade at $(rev): pilot hash $(snap); $(counts)"
docker exec brain-postgres psql -U brain -d "$NAME" -qAtc "SELECT count(*) FILTER (WHERE identity_version IS NOT NULL) || ' identity rows, ' || count(*) FILTER (WHERE identity_version IS NULL) || ' legacy rows' FROM fact_slot"
