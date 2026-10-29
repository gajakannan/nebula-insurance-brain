#!/bin/sh
set -eu
exec docker run --rm --network nebula-insurance-brain_default -v '/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/security/g2r3:/zap/wrk:rw' sha256:8d387b1a63e3425beef4846e39719f5af2a787753af2d8b6558c6257d7a577a2 zap-api-scan.py -t http://engine-validation:8000/openapi.json -f openapi -S -J dast.json -r dast.html -w dast.md
