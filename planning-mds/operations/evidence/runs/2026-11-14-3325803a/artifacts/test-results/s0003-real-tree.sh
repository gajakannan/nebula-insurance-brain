#!/usr/bin/env bash
# F0064-S0003 AC1, AC2 (exit-2 cases), AC5, AC6, AC7, NFE on the real working tree. Run from the product root.
V=".venv/bin/python scripts/validation/validate_plan_readiness.py"
E=planning-mds/operations/evidence/runs/2026-11-14-3325803a/artifacts/test-results
.venv/bin/python $E/tree-hash.py . > $E/s0003-ac7-hash-before.txt
git status --porcelain --untracked-files=all | grep -v "^?? $E/\|^?? planning-mds/operations/evidence/runs/2026-11-14-3325803a/" > $E/s0003-ac7-status-before.txt
run() { echo "### $*"; "$@"; echo "exit=$?"; echo; }
echo "== AC1 + NFE (project scope, timed)"; s=$(date +%s.%N); run $V --plan-scope project --target project; e=$(date +%s.%N); echo "wall_seconds=$(python3 -c "print(round($e-$s,3))")"; echo
echo "== AC2 invalid invocations (expect exit 2, BRAIN-INVOCATION)"
run $V --plan-scope project --target F0001
run $V --plan-scope feature --target F0001,F0002
run $V --plan-scope feature-set --target F0001,F0001
run $V --plan-scope feature --target F01
echo "== AC5 compliance entry point"
run .venv/bin/python scripts/kg/validate_plan_compliance.py planning-mds/features/F0064-repository-instructions-and-planning-check-adoption/PRD.md
run .venv/bin/python scripts/kg/validate_plan_compliance.py README.md
echo "== AC6 own package"
run $V --plan-scope feature --target F0064
.venv/bin/python $E/tree-hash.py . > $E/s0003-ac7-hash-after.txt
git status --porcelain --untracked-files=all | grep -v "^?? $E/\|^?? planning-mds/operations/evidence/runs/2026-11-14-3325803a/" > $E/s0003-ac7-status-after.txt
echo "== AC7"
if cmp -s $E/s0003-ac7-hash-before.txt $E/s0003-ac7-hash-after.txt && cmp -s $E/s0003-ac7-status-before.txt $E/s0003-ac7-status-after.txt; then
  echo "AC7 PASS: $(tail -1 $E/s0003-ac7-hash-after.txt) tracked files byte-identical; git status unchanged"
else echo "AC7 FAIL"; diff $E/s0003-ac7-hash-before.txt $E/s0003-ac7-hash-after.txt | head; fi
