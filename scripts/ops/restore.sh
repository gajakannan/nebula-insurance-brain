#!/usr/bin/env bash
# Always restore into a new container and fresh content directory.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${1:?usage: restore.sh <backup-dir> [--keep]}"
KEEP="${2:-}"
python3 "$REPO_ROOT/scripts/ops/backup_inventory.py" verify "$BACKUP_DIR"
IMAGE="${BRAIN_RESTORE_IMAGE:-brain-postgres:18-pgvector-age}"
RESTORE_CONTENT_ROOT="$(mktemp -d)"
RESTORE_CONTAINER="brain-restore-$(date -u +%Y%m%d%H%M%S)-$$"
cleanup() {
  if [ "$KEEP" != "--keep" ]; then
    docker rm -f "$RESTORE_CONTAINER" >/dev/null 2>&1 || true
    rm -rf "$RESTORE_CONTENT_ROOT"
  else
    echo "Kept isolated target: $RESTORE_CONTAINER; content: $RESTORE_CONTENT_ROOT"
  fi
}
trap cleanup EXIT
START_TIME=$(date +%s)
NETWORK_ARGS=(-p "127.0.0.1::5432")
if [ -n "${BRAIN_RESTORE_NETWORK:-}" ]; then
  NETWORK_ARGS=(--network "$BRAIN_RESTORE_NETWORK")
fi
docker run -d --name "$RESTORE_CONTAINER" \
  -e POSTGRES_USER=brain -e POSTGRES_PASSWORD=brain -e POSTGRES_DB=brain \
  "${NETWORK_ARGS[@]}" "$IMAGE" >/dev/null
READY=""
for _ in $(seq 1 60); do
  if docker exec -e PGPASSWORD=brain "$RESTORE_CONTAINER" \
      psql -h 127.0.0.1 -U brain -d brain -c "SELECT 1" >/dev/null 2>&1; then
    READY="1"
    break
  fi
  sleep 1
done
if [ -z "$READY" ]; then
  echo "FAIL: isolated database did not become ready" >&2
  exit 1
fi
RESTORE_HOST=127.0.0.1
if [ -n "${BRAIN_RESTORE_NETWORK:-}" ]; then
  RESTORE_HOST="$RESTORE_CONTAINER"
  RESTORE_PORT=5432
else
  RESTORE_PORT="$(docker port "$RESTORE_CONTAINER" 5432/tcp)"
  RESTORE_PORT="${RESTORE_PORT##*:}"
fi
docker exec -i -e PGPASSWORD=brain "$RESTORE_CONTAINER" \
  pg_restore -U brain -d brain --no-owner --exit-on-error < "$BACKUP_DIR/db.dump"
python3 "$REPO_ROOT/scripts/ops/backup_inventory.py" extract "$BACKUP_DIR" \
  --destination "$RESTORE_CONTENT_ROOT"
ops_python() {
  if [ -n "${BRAIN_OPS_PYTHON:-}" ]; then
    "$BRAIN_OPS_PYTHON" "$@"
  else
    uv run --frozen --directory "$REPO_ROOT/engine" python "$@"
  fi
}
DATABASE_URL="postgresql://brain:brain@$RESTORE_HOST:$RESTORE_PORT/brain"
ops_python "$REPO_ROOT/scripts/ops/verify_content.py" \
  --database-url "$DATABASE_URL" --content-root "$RESTORE_CONTENT_ROOT" \
  --expect "$BACKUP_DIR/content-inventory.json"
ops_python "$REPO_ROOT/scripts/ops/verify_citations.py" \
  --database-url "$DATABASE_URL" --content-root "$RESTORE_CONTENT_ROOT"
echo "Restore drill PASSED: $(( $(date +%s) - START_TIME ))s; isolated DB and content verified"
