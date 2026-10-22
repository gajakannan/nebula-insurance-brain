#!/bin/sh
set -u
status=0
for scope in engine neuron scripts; do
  docker run --rm -v '/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain:/src:ro' -v '/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/security:/reports' sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f dir "/src/$scope" --redact --report-format json --report-path "/reports/secrets-$scope.json" || status=1
done
exit "$status"
