#!/usr/bin/env bash
# Restore a backup produced by backup.sh into a genuinely fresh Postgres
# instance (a throwaway container on its own volume, not the running dev
# stack) plus a fresh content-root directory, then verify every S0003
# citation resolves. Prints the measured restore duration
# (F0001-S0006 acceptance criterion).
#
# Usage: scripts/ops/restore.sh <backup-dir> [--keep]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${1:?usage: restore.sh <backup-dir> [--keep]}"
KEEP="${2:-}"

if [ ! -f "$BACKUP_DIR/db.dump" ] || [ ! -f "$BACKUP_DIR/content.tar.gz" ]; then
  echo "FAIL: $BACKUP_DIR is missing db.dump or content.tar.gz — not a valid backup" >&2
  exit 1
fi

IMAGE="brain-postgres:18-pgvector-age"
RESTORE_CONTAINER="brain-postgres-restore-drill"
RESTORE_PORT="55432"
RESTORE_CONTENT_ROOT="$(mktemp -d)"

cleanup() {
  if [ "$KEEP" != "--keep" ]; then
    docker rm -f "$RESTORE_CONTAINER" >/dev/null 2>&1 || true
    rm -rf "$RESTORE_CONTENT_ROOT"
  else
    echo "==> --keep passed: leaving '$RESTORE_CONTAINER' on port $RESTORE_PORT and $RESTORE_CONTENT_ROOT in place"
  fi
}
trap cleanup EXIT

START_TIME=$(date +%s.%N)

echo "==> Starting a fresh, throwaway Postgres instance ($RESTORE_CONTAINER on :$RESTORE_PORT)..."
docker rm -f "$RESTORE_CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$RESTORE_CONTAINER" \
  -e POSTGRES_USER=brain -e POSTGRES_PASSWORD=brain -e POSTGRES_DB=brain \
  -p "$RESTORE_PORT:5432" \
  "$IMAGE" >/dev/null

echo -n "==> Waiting for it to become healthy"
READY=""
for _ in $(seq 1 60); do
  # `pg_isready` alone can succeed against the entrypoint's temporary
  # initdb-only server before it restarts into the real one and creates
  # POSTGRES_DB — query the actual target database, not just the socket.
  if docker exec -e PGPASSWORD=brain "$RESTORE_CONTAINER" \
      psql -U brain -d brain -c "SELECT 1" >/dev/null 2>&1; then
    echo " — ready."
    READY="1"
    break
  fi
  echo -n "."
  sleep 1
done
if [ -z "$READY" ]; then
  echo " FAILED to become ready within 60s" >&2
  exit 1
fi

echo "==> Restoring database from $BACKUP_DIR/db.dump..."
docker exec -i -e PGPASSWORD=brain "$RESTORE_CONTAINER" \
  pg_restore -U brain -d brain --no-owner --clean --if-exists < "$BACKUP_DIR/db.dump"

echo "==> Restoring content root to $RESTORE_CONTENT_ROOT..."
tar -xzf "$BACKUP_DIR/content.tar.gz" -C "$RESTORE_CONTENT_ROOT"
RESTORED_CONTENT_SUBDIR="$RESTORE_CONTENT_ROOT/$(basename "${BRAIN_CONTENT_ROOT:-$REPO_ROOT/content}")"

END_TIME=$(date +%s.%N)
DURATION=$(python3 -c "print(f'{${END_TIME} - ${START_TIME}:.2f}')")
echo "==> Measured restore duration: ${DURATION}s"

echo "==> Verifying every S0003 citation resolves against the restored data..."
set +e
uv run --directory "$REPO_ROOT/engine" python3 "$REPO_ROOT/scripts/ops/verify_citations.py" \
  --database-url "postgresql://brain:brain@localhost:$RESTORE_PORT/brain" \
  --content-root "$RESTORED_CONTENT_SUBDIR"
CITATION_STATUS=$?
set -e

if [ "$CITATION_STATUS" -eq 0 ]; then
  echo "==> Restore drill PASSED (duration ${DURATION}s)"
else
  echo "==> Restore drill FAILED citation check (duration ${DURATION}s)" >&2
fi
exit "$CITATION_STATUS"
