"""Measure changed executable statements, counting unmeasured files as misses."""
import json
import sys
from pathlib import Path

from coverage.parser import PythonParser

folder = Path(sys.argv[1])
changed = json.loads((folder / "changed-lines.json").read_bytes())
coverage = json.loads((folder / "combined.json").read_bytes())
rows = []
for name, lines in changed.items():
    parser = PythonParser(filename=name)
    parser.parse_source()
    required = set(parser.statements) & set(lines)
    covered = set(coverage["files"].get(name, {}).get("executed_lines", [])) & required
    rows.append({
        "path": name, "statements": len(required), "covered": len(covered),
        "missing_lines": sorted(required - covered),
        "measured": name in coverage["files"],
    })
total = sum(row["statements"] for row in rows)
covered = sum(row["covered"] for row in rows)
result = {
    "basis": "git diff HEAD plus all untracked Python runtime files; unmeasured statements count as missed",
    "statements": total, "covered": covered,
    "percent": 100 * covered / total if total else 100, "files": rows,
}
(folder / "changed-runtime.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items() if key != "files"}))
raise SystemExit(0 if result["percent"] >= 80 else 1)

