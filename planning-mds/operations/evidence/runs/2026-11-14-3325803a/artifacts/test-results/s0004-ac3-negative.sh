#!/usr/bin/env bash
# F0064-S0004 AC3: shared executor against a copy whose checklist lacks BRAIN-EXAMPLES. Args: product root, scratch dir, framework root, evidence dir.
P=$1; T=$2; F=$3; E=$4
python3 "$E/tree-hash.py" "$P" > "$E/s0004-ac3-hash-before.txt"
rm -rf "$T"; mkdir -p "$T"; git -C "$P" archive HEAD | tar -x -C "$T"
grep -v "^| BRAIN-EXAMPLES |" "$T/docs/plan-review-checklist.md" > "$T/x" && mv "$T/x" "$T/docs/plan-review-checklist.md"
echo "BRAIN-EXAMPLES rows remaining in copy: $(grep -c 'BRAIN-EXAMPLES' "$T/docs/plan-review-checklist.md")"
RID="$(date -u +%F)-$(python3 -c 'import secrets; print(secrets.token_hex(4))')"; echo "copy run_id=$RID"
cd "$F" && env -u NEBULA_PRODUCT_ROOT .venv/bin/python agents/scripts/project_checks.py --product-root "$T" --action plan-review --plan-scope project --target project --run-id "$RID"
EC=$?; echo "executor exit=$EC"
mkdir -p "$E/s0004-ac3-copy-run" && cp -r "$T/planning-mds/operations/evidence/runs/$RID/." "$E/s0004-ac3-copy-run/"
echo "copied run folder:"; ls -R "$E/s0004-ac3-copy-run" | head -20
python3 "$E/tree-hash.py" "$P" > "$E/s0004-ac3-hash-after.txt"
cmp -s "$E/s0004-ac3-hash-before.txt" "$E/s0004-ac3-hash-after.txt" && echo "real working tree tracked files unchanged: PASS" || echo "real tree changed: FAIL"
ls "$P/planning-mds/operations/evidence/runs/$RID" 2>/dev/null && echo "LEAK into real tree: FAIL" || echo "no run folder created in real tree: PASS"
