"""Changed-production-line coverage for F0007 run 2026-11-09-b94cfa12.

Inputs: coverage JSON from the owned-DB full engine run; `git diff -U0` against the
run's base commit for modified files; every line of new files. Usage (product root):
  python3 <this> <coverage.json> <base-ref> > changed-code-summary.json
"""
import json, re, subprocess, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
base = sys.argv[2]
prefix = "engine/"
files = {k if k.startswith("engine/") else prefix + k: v for k, v in data["files"].items()}
status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "engine/apps", "engine/packages"],
                        capture_output=True, text=True, check=True).stdout.splitlines()
production = [l[3:] for l in status if l[3:].endswith(".py") and "/src/" in l[3:]]
summary, covered_total, measured_total = [], 0, 0
for path in sorted(production):
    entry = files.get(path)
    if entry is None:
        summary.append({"file": path, "status": "not-measured"}); continue
    executable = set(entry["executed_lines"]) | set(entry["missing_lines"])
    if status and any(l.startswith("??") and path.startswith(l[3:].rstrip("/")) for l in status):
        changed = executable
    else:
        diff = subprocess.run(["git", "diff", "-U0", base, "--", path], capture_output=True, text=True).stdout
        changed = set()
        for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
            start, count = int(m[1]), int(m[2] or 1)
            changed.update(range(start, start + count))
        changed &= executable
    hit = changed & set(entry["executed_lines"])
    covered_total += len(hit); measured_total += len(changed)
    summary.append({"file": path, "changed_executable": len(changed), "covered": len(hit),
                    "missing": sorted(changed - hit)})
print(json.dumps({"base": base, "files": summary, "changed_executable_lines": measured_total,
                  "covered": covered_total,
                  "percent": round(100 * covered_total / measured_total, 2) if measured_total else None},
                 indent=2))
