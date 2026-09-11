#!/usr/bin/env bash
# Back up the brain database, the local content root, and the dependency matrix
# into one timestamped, sha256-manifested directory (F0001-S0006 restore-drill
# proof; master blueprint section 114.3). Requires the compose `postgres`
# service to be running (`docker compose up -d postgres`).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTENT_ROOT="${BRAIN_CONTENT_ROOT:-$REPO_ROOT/content}"
BACKUP_ROOT="${BRAIN_BACKUP_ROOT:-$REPO_ROOT/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$BACKUP_ROOT/$TIMESTAMP"
CONTAINER="${BRAIN_POSTGRES_CONTAINER:-brain-postgres}"

mkdir -p "$DEST"

echo "==> Dumping database (custom format) from container '$CONTAINER'..."
docker exec -e PGPASSWORD=brain "$CONTAINER" pg_dump -U brain -Fc -d brain > "$DEST/db.dump"

echo "==> Snapshotting content root ($CONTENT_ROOT)..."
if [ -d "$CONTENT_ROOT" ]; then
  tar -czf "$DEST/content.tar.gz" -C "$(dirname "$CONTENT_ROOT")" "$(basename "$CONTENT_ROOT")"
else
  echo "    (content root does not exist yet — writing an empty snapshot)"
  tar -czf "$DEST/content.tar.gz" --files-from /dev/null
fi

echo "==> Snapshotting dependency matrix..."
cp "$REPO_ROOT/docker/DEPENDENCY-MATRIX.md" "$DEST/DEPENDENCY-MATRIX.md"

echo "==> Writing manifest..."
python3 - "$DEST" <<'PYEOF'
import hashlib
import json
import sys
from pathlib import Path

dest = Path(sys.argv[1])
files = sorted(p for p in dest.iterdir() if p.is_file() and p.name != "manifest.json")
manifest = {
    "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    "files": [
        {
            "path": f.name,
            "size_bytes": f.stat().st_size,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        }
        for f in files
    ],
}
(dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
PYEOF

echo "==> Backup complete: $DEST"
