#!/bin/sh
set -eu
base="${DAST_REPORT_BASENAME:-api-scan}"
exec zap-api-scan.py -t "$DAST_TARGET_URL/openapi.json" -f openapi -r "$base.html" -J "$base.json" -T 4 -z "-silent -config autoupdate.checkOnStart=false -config autoupdate.downloadNewRelease=false -config autoupdate.installAddonUpdates=false -config autoupdate.installScannerRules=false"
