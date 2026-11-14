#!/usr/bin/env bash
# Combined verification coverage of validate_plan_readiness.py: fixture suite + the S0003 CLI invocations (real tree and copies).
# Args: product root, scratch dir, output json. Copies come from `git archive HEAD`.
set -u
P=$1; T=$2; OUT=$3
export COVERAGE_FILE="$T/.coverage-combined"; rm -f "$COVERAGE_FILE"
CV="uv run --no-project --python 3.12 --with pytest==9.0.3 --with coverage==7.10.7 python -m coverage"
INC="--include=*/scripts/validation/validate_plan_readiness.py"
cd "$P"
$CV run --branch -a $INC -m pytest -q -p no:cacheprovider scripts/validation/tests/test_plan_readiness.py | tail -1
V="scripts/validation/validate_plan_readiness.py"
for args in "--plan-scope project --target project" "--plan-scope project --target F0001" "--plan-scope feature --target F0001,F0002" \
            "--plan-scope feature-set --target F0001,F0001" "--plan-scope feature --target F01" "--plan-scope feature --target F0064" \
            "--plan-scope feature-set --target F0064,F0065" "--plan-scope feature --target F9999"; do
  $CV run --branch -a $INC $V $args >/dev/null; echo "cli [$args] exit=$?"
done
mk() { rm -rf "$T/cov-$1"; mkdir -p "$T/cov-$1"; git -C "$P" archive HEAD | tar -x -C "$T/cov-$1"; }
mk nochk; grep -v "^| BRAIN-EXAMPLES |" "$T/cov-nochk/docs/plan-review-checklist.md" > "$T/x" && mv "$T/x" "$T/cov-nochk/docs/plan-review-checklist.md"
$CV run --branch -a $INC $V --product-root "$T/cov-nochk" --plan-scope project --target project >/dev/null; echo "copy missing-rule exit=$?"
mk active; sed -i 's/^| F0009 | Provenance + human-correction lineage | Planned |/| F0009 | Provenance + human-correction lineage | Active |/' "$T/cov-active/planning-mds/features/REGISTRY.md"
$CV run --branch -a $INC $V --product-root "$T/cov-active" --plan-scope project --target project >/dev/null; echo "copy active-no-prd exit=$?"
$CV report -m
$CV json -o "$OUT" >/dev/null
