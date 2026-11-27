#!/bin/sh
# The framework wrapper supplies DAST_TARGET_URL. Preserve every warning in JSON.
exec /zap/zap-api-scan.py -t "$DAST_TARGET_URL" -f openapi -O http://brain-f0012-54387a08-engine-validation-1:8000 -I -T 3 -J api-scan.json -r api-scan.html -w api-scan.md -x api-scan.xml
