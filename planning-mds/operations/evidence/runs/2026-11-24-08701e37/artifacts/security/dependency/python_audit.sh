#!/bin/sh
# F0009 AI_DEP_SCAN_CMD: audit one locked Python workspace (cwd = that workspace).
# Exports the frozen lock (third-party only) and runs pinned pip-audit against it;
# never installs, upgrades or fixes a product package.
set -eu
OUT=/app/brain/planning-mds/operations/evidence/runs/2026-11-24-08701e37/artifacts/security/dependency
NAME=$(basename "$PWD")
export UV_TOOL_DIR=/tmp/f0009-uv-tools UV_TOOL_BIN_DIR=/tmp/f0009-uv-bin
uv export --frozen --no-hashes --no-emit-workspace --all-groups --no-header \
  --output-file "$OUT/$NAME-requirements.txt" >/dev/null
# First-party editable workspace paths are not PyPI artifacts; audit third-party pins only.
grep -v '^-e ' "$OUT/$NAME-requirements.txt" > "$OUT/$NAME-requirements.tmp" &&   mv "$OUT/$NAME-requirements.tmp" "$OUT/$NAME-requirements.txt"
sha256sum uv.lock > "$OUT/$NAME-lock.sha256"
uv tool run --from pip-audit==2.10.1 pip-audit --requirement "$OUT/$NAME-requirements.txt" \
  --no-deps --disable-pip --strict --progress-spinner off --format json \
  --output "$OUT/$NAME.json" --cache-dir /tmp/f0009-audit-cache --timeout 30
