#!/bin/sh
exec uv tool run --from pip-audit pip-audit --path /opt/venv/lib/python3.14/site-packages --format json --output /app/brain/planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/artifacts/security/dependency-engine.json
