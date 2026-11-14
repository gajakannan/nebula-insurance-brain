#!/usr/bin/env bash
# F0064-S0003 AC2 (exit 1) and AC4 selection, each on a fresh `git archive HEAD` copy. Arg 1: product root, arg 2: scratch dir.
P=$1; T=$2; V="$P/.venv/bin/python scripts/validation/validate_plan_readiness.py"
fresh() { rm -rf "$T/$1"; mkdir -p "$T/$1"; git -C "$P" archive HEAD | tar -x -C "$T/$1"; cd "$T/$1"; }
echo "== AC2 exit 1: F0064 PRD 'Dependencies' section emptied in copy"
fresh empty-section
python3 - <<'PY'
import re, pathlib
p = next(pathlib.Path("planning-mds/features").glob("F0064-*/PRD.md")); t = p.read_text()
t = re.sub(r"(## Dependencies\n)(.*?)(\n## )", r"\1\nTBD\n\3", t, flags=re.S); p.write_text(t)
PY
$V --plan-scope project --target project; echo "exit=$?"
echo; echo "== AC4a: F0009 (folder without PRD.md) flipped Planned->Active in copy registry: expect it selected (missing PRD finding)"
fresh active-no-prd
sed -i 's/^| F0009 | Provenance + human-correction lineage | Planned |/| F0009 | Provenance + human-correction lineage | Active |/' planning-mds/features/REGISTRY.md
grep -n "^| F0009 " planning-mds/features/REGISTRY.md
$V --plan-scope project --target project; echo "exit=$?"
echo; echo "== AC4b: archived F0001 PRD.md deleted in copy: expect archived feature not selected (still pass)"
fresh archived
rm planning-mds/features/archive/F0001-repository-and-engineering-foundation/PRD.md
$V --plan-scope project --target project; echo "exit=$?"
echo; echo "== AC4c: selected set at project scope on HEAD (introspection)"
fresh selection
python3 - "$P" <<'PY'
import sys, re, pathlib
root = pathlib.Path(".").resolve()
reg = (root / "planning-mds/features/REGISTRY.md").read_text()
sel = []
for line in reg.splitlines():
    c = [x.strip().strip("`") for x in line.strip().strip("|").split("|")]
    if c and re.fullmatch(r"F\d{4}", c[0]):
        f = [x for x in c[1:] if re.fullmatch(r"(?:archive/)?F\d{4}-[a-z0-9-]+/?", x)][0]
        path = root / "planning-mds/features" / f.rstrip("/")
        if "/archive/" not in str(path) and ({"Active", "In Progress", "Done"} & set(c) or (path / "PRD.md").exists()):
            sel.append(c[0])
print("selected:", sel)
PY
