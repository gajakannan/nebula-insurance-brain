"""Recompute strict changed-statement coverage from durable raw coverage data."""

import argparse
import hashlib
import json
import pathlib
import re
import subprocess

import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--product-root", required=True)
parser.add_argument("--run-id", required=True)
args = parser.parse_args()
root = pathlib.Path(args.product_root).resolve()
run = root / "planning-mds/operations/evidence/runs" / args.run_id
manifest = json.loads((run / "evidence-manifest.json").read_text())
base = manifest["scm"]["base_ref"]
report = json.loads((run / "artifacts/coverage/combined-python.json").read_text())
changed = set(subprocess.check_output(["git", "diff", "--name-only", base], cwd=root, text=True).splitlines())
untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True).splitlines())
changed.update(untracked)
selected = sorted(p for p in changed if p.endswith(".py") and p.startswith(("engine/", "neuron/", "scripts/contracts/"))
                  and "/tests/" not in p and "/generated/" not in p)
rows = []
unmeasured = []
for path in selected:
    data = report["files"].get(path)
    if data is None:
        unmeasured.append(path)
        continue
    executed = set(data["executed_lines"])
    statements = executed | set(data["missing_lines"])
    if path in untracked:
        delta = statements
    else:
        diff = subprocess.check_output(["git", "diff", "--unified=0", base, "--", path], cwd=root, text=True)
        additions = set()
        for line in diff.splitlines():
            match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                start = int(match[1])
                count = int(match[2]) if match[2] is not None else 1
                additions.update(range(start, start + count))
        delta = statements & additions
    if delta:
        rows.append({"path": path, "changed_statements": len(delta), "covered": len(delta & executed),
                     "missing_lines": sorted(delta - executed),
                     "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()})
floor = yaml.safe_load((root.parent / "nebula-agents/agents/actions/spec/_contract.yaml").read_text())["shared"]["coverage_min_pct"]
total = sum(row["changed_statements"] for row in rows)
covered = sum(row["covered"] for row in rows)
pct = 100 * covered / total
result = {"run_id": args.run_id, "base_ref": base, "language": "Python",
          "covered_changed_statements": covered, "changed_statements": total,
          "coverage_pct": pct, "contract_min_pct": floor,
          "status": "pass" if not unmeasured and pct >= floor else "fail",
          "unmeasured": unmeasured, "files": rows,
          "scope": "All changed authored Python application/tool code; tests, generated models, data and non-Python config excluded. JS measured separately with V8."}
(run / "artifacts/coverage/changed-line-coverage.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items() if key != "files"}))
raise SystemExit(0 if result["status"] == "pass" else 1)
