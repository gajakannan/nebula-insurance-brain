#!/usr/bin/env bash
# Wait until the authentik "brain" OIDC application serves discovery, recovering a
# stalled authentik worker along the way.
#
# Server health does not mean the worker has applied the custom blueprint. The worker
# can also hang partway through its startup blueprint queue while its healthcheck
# stays green. When that happens, discovery returns 404 indefinitely because the
# Nebula blueprint was enqueued but never ran (CI run 43153176311, 2026-11-12).
#
# Recovery: discovery is not 200 and the worker has written no log line for
# WORKER_STALL_SECONDS. In that case the script restarts the worker and applies the
# Nebula blueprint synchronously with `ak apply_blueprint`, which bypasses the task
# queue. That happens at most MAX_WORKER_RECOVERIES times. Applying a blueprint is
# idempotent, so an unnecessary recovery is harmless.
#
# Run from the repository root (docker compose context). Exit 0 when discovery is
# 200; exit 1 when the budget runs out.
set -uo pipefail

DISCOVERY_URL="${OIDC_DISCOVERY_URL:-http://localhost:9010/application/o/brain/.well-known/openid-configuration}"
BUDGET_SECONDS="${OIDC_WAIT_SECONDS:-300}"
STALL_SECONDS="${WORKER_STALL_SECONDS:-60}"
MAX_RECOVERIES="${MAX_WORKER_RECOVERIES:-2}"
WORKER_SERVICE="authentik-worker"
WORKER_CONTAINER="brain-authentik-worker"
BLUEPRINT="custom/nebula-brain-dev.yaml" # relative to /blueprints in the container

discovery_status() {
  local code
  code="$(curl --silent --output /dev/null --write-out '%{http_code}' \
    --connect-timeout 2 --max-time 5 "$DISCOVERY_URL")" || code=unreachable
  echo "$code"
}

worker_is_quiet() {
  [[ -z "$(docker logs --since "${STALL_SECONDS}s" "$WORKER_CONTAINER" 2>&1 | head -n 1)" ]]
}

wait_for_worker_healthy() {
  local health
  for _ in $(seq 1 18); do
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
      "$WORKER_CONTAINER" 2>/dev/null)"
    if [[ "$health" == "healthy" || "$health" == "running" ]]; then return 0; fi
    sleep 5
  done
  echo "::warning::authentik worker did not report healthy after restart (last: ${health:-unknown})"
  return 1
}

recover_worker() {
  echo "::warning::authentik worker silent for ${STALL_SECONDS}s while discovery is not ready; restarting it (recovery $1/$MAX_RECOVERIES)"
  docker compose restart "$WORKER_SERVICE"
  wait_for_worker_healthy || true
  echo "Applying $BLUEPRINT synchronously"
  if ! docker compose exec -T "$WORKER_SERVICE" ak apply_blueprint "$BLUEPRINT"; then
    echo "::warning::synchronous blueprint apply failed; relying on the restarted worker's discovery"
  fi
}

deadline=$((SECONDS + BUDGET_SECONDS))
last_progress_check=$SECONDS
recoveries=0
while ((SECONDS < deadline)); do
  status="$(discovery_status)"
  echo "OIDC discovery HTTP status: $status"
  if [[ "$status" == "200" ]]; then
    ((recoveries > 0)) && echo "OIDC application ready after $recoveries worker recovery(ies)"
    exit 0
  fi
  if ((SECONDS - last_progress_check >= STALL_SECONDS && recoveries < MAX_RECOVERIES)) && worker_is_quiet; then
    recoveries=$((recoveries + 1))
    recover_worker "$recoveries"
    last_progress_check=$SECONDS
  fi
  sleep 5
done

echo "::error::OIDC application did not become ready within ${BUDGET_SECONDS}s ($recoveries worker recovery(ies) attempted)"
exit 1
