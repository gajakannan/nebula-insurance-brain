#!/usr/bin/env bash
# Local DB + complete content snapshot. Operator must stop ingestion/date writes.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ "${BRAIN_WRITERS_QUIESCED:-}" != "1" ]; then
  echo "FAIL: stop local ingestion/date writers, then set BRAIN_WRITERS_QUIESCED=1" >&2
  exit 1
fi
CONTENT_ROOT="${BRAIN_CONTENT_ROOT:-$REPO_ROOT/content}"
BACKUP_ROOT="${BRAIN_BACKUP_ROOT:-$REPO_ROOT/backups}"
CONTAINER="${BRAIN_POSTGRES_CONTAINER:-brain-postgres}"
DATABASE="${BRAIN_POSTGRES_DATABASE:-brain}"
DATABASE_URL="${BRAIN_OPS_DATABASE_URL:-postgresql://brain:brain@127.0.0.1:5432/$DATABASE}"
mkdir -p "$BACKUP_ROOT" "$CONTENT_ROOT"
DEST="$(mktemp -d "$BACKUP_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
ops_python() {
  if [ -n "${BRAIN_OPS_PYTHON:-}" ]; then
    "$BRAIN_OPS_PYTHON" "$@"
  else
    uv run --frozen --directory "$REPO_ROOT/engine" python "$@"
  fi
}
# Quiescence is an operator precondition, not a distributed snapshot claim.
ops_python "$REPO_ROOT/scripts/ops/verify_content.py" \
  --database-url "$DATABASE_URL" --content-root "$CONTENT_ROOT" \
  --write "$DEST/content-inventory.json"
docker exec -e PGPASSWORD=brain "$CONTAINER" \
  pg_dump -U brain -Fc -d "$DATABASE" > "$DEST/db.dump"
tar -czf "$DEST/content.tar.gz" -C "$CONTENT_ROOT" .
cp "$REPO_ROOT/docker/DEPENDENCY-MATRIX.md" "$DEST/DEPENDENCY-MATRIX.md"
cp "$REPO_ROOT/engine/uv.lock" "$DEST/engine.uv.lock"
cp "$REPO_ROOT/neuron/uv.lock" "$DEST/neuron.uv.lock"
mkdir "$DEST/contracts"
cp "$REPO_ROOT/engine/packages/brain-content/src/brain_content/schemas/"*.json "$DEST/contracts/"
ops_python "$REPO_ROOT/scripts/ops/verify_content.py" \
  --database-url "$DATABASE_URL" --content-root "$CONTENT_ROOT" \
  --expect "$DEST/content-inventory.json"
python3 "$REPO_ROOT/scripts/ops/backup_inventory.py" seal "$DEST"
echo "Backup complete: $DEST"
