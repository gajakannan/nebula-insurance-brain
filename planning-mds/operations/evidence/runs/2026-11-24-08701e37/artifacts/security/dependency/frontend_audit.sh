#!/bin/sh
# F0009 FRONTEND_DEP_SCAN_CMD: pnpm audit of the frozen experience lock (cwd = experience).
OUT=/app/brain/planning-mds/operations/evidence/runs/2026-11-24-08701e37/artifacts/security/dependency
sha256sum pnpm-lock.yaml > "$OUT/experience-lock.sha256"
corepack pnpm audit --audit-level high --json > "$OUT/experience.json"
