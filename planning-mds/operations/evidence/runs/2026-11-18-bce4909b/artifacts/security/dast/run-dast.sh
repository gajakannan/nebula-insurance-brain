#!/usr/bin/env bash
# F0008 run 2026-11-18-bce4909b DAST (remediation run; operator-approved DAST pattern from 2026-11-18): boot brain_api on an
# owned throwaway DB at head and run a ZAP API scan from its OpenAPI. No credentials are
# configured, so protected routes are exercised unauthenticated (401 path) plus request
# validation (422/400 paths). F0008 adds no route or authentication surface.
# Docker Desktop's WSL integration is off, so docker.exe is called directly and every
# docker call reads /dev/null (docker.exe otherwise consumes the caller's stdin).
set -u
PR=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
OUT=$PR/planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/security/dast
D="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
PORT=8768
if curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null; then
  echo "port $PORT already served; refusing to scan a stale server"; exit 3
fi
NAME="f0008r_dast_$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
"$D" exec brain-postgres psql -U brain -d brain -qAtc "CREATE DATABASE $NAME" >/dev/null </dev/null
"$D" exec brain-postgres psql -U brain -d "$NAME" -qAtc "CREATE EXTENSION IF NOT EXISTS btree_gist" >/dev/null </dev/null
( cd "$PR/engine/migrations" && BRAIN_DATABASE_URL="postgresql+psycopg://brain:brain@localhost:5432/$NAME" ../.venv/bin/alembic upgrade head >/dev/null 2>&1 )
cd "$PR"
BRAIN_DATABASE_URL="postgresql+asyncpg://brain:brain@localhost:5432/$NAME" \
  engine/.venv/bin/uvicorn brain_api.app:create_app --factory --host 0.0.0.0 --port "$PORT" \
  > "$OUT/uvicorn.log" 2>&1 &
API=$!
for _ in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null && break; sleep 1; done
curl -s -o /dev/null -w "openapi HTTP %{http_code} (api pid $API, db $NAME)\n" "http://127.0.0.1:$PORT/openapi.json"
# Pick a target the container can reach: Docker Desktop's host gateway, else the WSL IP.
TARGET=""
for HOST in host.docker.internal "$(hostname -I | awk '{print $1}')"; do
  code=$("$D" run --rm --add-host=host.docker.internal:host-gateway curlimages/curl:8.10.1 \
    -s -m 5 -o /dev/null -w "%{http_code}" "http://$HOST:$PORT/openapi.json" </dev/null)
  echo "probe $HOST -> $code"
  if [ "$code" = "200" ]; then TARGET=$HOST; break; fi
done
rc=4
if [ -n "$TARGET" ]; then
  "$D" run --rm --add-host=host.docker.internal:host-gateway -v "$(wslpath -w "$OUT"):/zap/wrk:rw" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-api-scan.py -t "http://$TARGET:$PORT/openapi.json" -f openapi \
    -r api-scan.html -J api-scan.json -T 4 \
    -z "-silent -config autoupdate.checkOnStart=false -config autoupdate.installAddonUpdates=false -config autoupdate.installScannerRules=false" \
    > "$OUT/zap.out" 2>&1 </dev/null
  rc=$?
else
  echo "no container-reachable target; scan not run"
fi
kill "$API" 2>/dev/null; wait "$API" 2>/dev/null
if curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null; then echo "WARNING: port $PORT still served"; fi
"$D" exec brain-postgres psql -U brain -d brain -qAtc "DROP DATABASE $NAME WITH (FORCE)" >/dev/null </dev/null
echo "zap exit=$rc (0 pass, 1 fail alerts, 2 warn alerts, 3 error, 4 not run)"
grep -E "^(FAIL-NEW|WARN-NEW|PASS)" "$OUT/zap.out" 2>/dev/null | tail -5
exit 0
