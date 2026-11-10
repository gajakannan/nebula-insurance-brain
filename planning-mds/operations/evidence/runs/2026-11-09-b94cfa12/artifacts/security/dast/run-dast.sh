#!/usr/bin/env bash
# F0007 run 2026-11-09-b94cfa12 DAST: boot brain_api on an owned DB at head and run a
# ZAP API scan from its OpenAPI. No credentials are configured, so protected routes
# are exercised unauthenticated (401 path) plus request validation (422 path).
# The OIDC issuer is not running locally, so credential verification is not part of
# this scan's reach; F0007 adds no authentication surface.
set -u
PR=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
OUT=$PR/planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/artifacts/security/dast
PORT=8765
if curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null; then
  echo "port $PORT already served; refusing to scan a stale server"; exit 3
fi
NAME="f0007_dast_$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
docker exec brain-postgres psql -U brain -d brain -qAtc "CREATE DATABASE $NAME" >/dev/null
docker exec brain-postgres psql -U brain -d "$NAME" -qAtc "CREATE EXTENSION IF NOT EXISTS btree_gist" >/dev/null
( cd "$PR/engine/migrations" && BRAIN_DATABASE_URL="postgresql+psycopg://brain:brain@localhost:5432/$NAME" ../.venv/bin/alembic upgrade head >/dev/null 2>&1 )
cd "$PR"
BRAIN_DATABASE_URL="postgresql+asyncpg://brain:brain@localhost:5432/$NAME" \
  engine/.venv/bin/uvicorn brain_api.app:create_app --factory --host 0.0.0.0 --port "$PORT" \
  > "$OUT/uvicorn.log" 2>&1 &
API=$!
for _ in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null && break; sleep 1; done
curl -s -o /dev/null -w "openapi HTTP %{http_code} (api pid $API, db $NAME)\n" "http://127.0.0.1:$PORT/openapi.json"
docker run --rm --add-host=host.docker.internal:host-gateway -v "$OUT":/zap/wrk:rw -u "$(id -u):$(id -g)" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py -t "http://host.docker.internal:$PORT/openapi.json" -f openapi \
  -r api-scan.html -J api-scan.json -T 4 \
  -z "-silent -config autoupdate.checkOnStart=false -config autoupdate.installAddonUpdates=false -config autoupdate.installScannerRules=false" \
  > "$OUT/zap.out" 2>&1
rc=$?
kill "$API" 2>/dev/null; wait "$API" 2>/dev/null
if curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null; then echo "WARNING: port $PORT still served"; fi
docker exec brain-postgres psql -U brain -d brain -qAtc "DROP DATABASE $NAME WITH (FORCE)" >/dev/null
echo "zap exit=$rc (0 pass, 1 fail alerts, 2 warn alerts, 3 error)"
grep -E "^(FAIL-NEW|WARN-NEW|PASS)" "$OUT/zap.out" | tail -5
exit 0
