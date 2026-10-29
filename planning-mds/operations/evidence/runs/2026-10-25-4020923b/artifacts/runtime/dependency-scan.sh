#!/bin/sh
set -u
status=0
cd '/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain'
for service in engine-validation neuron-validation; do
  report="${service%-validation}"
  docker compose -f 'planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/runtime/compose.yaml' exec -T -e UV_CACHE_DIR=/tmp/uv-audit-cache "$service" uv tool run --from pip-audit==2.9.0 pip-audit --path /opt/venv/lib/python3.14/site-packages --skip-editable --format json --output '/app/brain/planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/security/dependency-'"$report"'.json' || status=1
done
exit "$status"
