#!/usr/bin/env python3
"""F0064-S0001 AC1, AC2 and AC5 assertions against the product manifest.

Usage: s0001-manifest-assertions.py <product-root>
Prints one line per check and exits non-zero on the first failed assertion group.
"""
from __future__ import annotations

import glob
import re
import subprocess
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1]).resolve()
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


m = yaml.safe_load((root / ".nebula-project.yaml").read_text(encoding="utf-8"))

# AC1 — exact declaration.
check("AC1 version == 1", m.get("version") == 1, repr(m.get("version")))
instr = m.get("instructions") or []
check("AC1 two instructions in order",
      [i.get("path") for i in instr] == ["docs/agent-instructions.md", "docs/plan-review-checklist.md"],
      repr([i.get("path") for i in instr]))
check("AC1 agent-instructions applies to all actions", "actions" not in instr[0], repr(instr[0]))
check("AC1 checklist restricted to plan-review", instr[1].get("actions") == ["plan-review"], repr(instr[1].get("actions")))
checks = m.get("checks") or []
check("AC1 exactly one check", len(checks) == 1, str(len(checks)))
c = checks[0]
expected = {"id": "plan-readiness", "action": "plan-review", "stage": "PR2",
            "event": "before_stage_complete", "cwd": "product", "timeout_seconds": 60}
for key, value in expected.items():
    check(f"AC1 check.{key} == {value!r}", c.get(key) == value, repr(c.get(key)))

# AC2 — argv shape, placeholders, no shell string.
argv = c.get("argv") or []
check("AC2 argv is a list of strings", isinstance(argv, list) and all(isinstance(a, str) for a in argv))
check("AC2 argv[0] is python3", argv[:1] == ["python3"], repr(argv[:1]))
check("AC2 argv[1] ends with scripts/validation/validate_plan_readiness.py",
      len(argv) > 1 and argv[1].endswith("scripts/validation/validate_plan_readiness.py"), repr(argv[1:2]))
for flag in ["--product-root", "--plan-scope", "--target"]:
    check(f"AC2 argv carries {flag}", flag in argv)
placeholders = {p for a in argv for p in re.findall(r"\{([A-Z_]+)\}", a)}
check("AC2 placeholder set == {NEBULA_PRODUCT_ROOT, PLAN_SCOPE, TARGET}",
      placeholders == {"NEBULA_PRODUCT_ROOT", "PLAN_SCOPE", "TARGET"}, repr(sorted(placeholders)))
shell_tokens = [a for a in argv if a in {"sh", "bash", "-c"} or any(ch in a for ch in ";|&$`")]
check("AC2 no shell evaluation token in argv", not shell_tokens, repr(shell_tokens))
check("AC2 no shell/command string key", not ({"shell", "command", "run"} & set(c)), repr(sorted(c)))

# AC5 — every input pattern matches a tracked file; every validator read is covered.
tracked = set(subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True,
                             check=True).stdout.splitlines())
patterns = c.get("inputs") or []
matched_by: dict[str, set[str]] = {}
for pattern in patterns:
    hits = {Path(p).relative_to(root).as_posix() for p in glob.glob(str(root / pattern), recursive=True)
            if Path(p).is_file() and "__pycache__" not in Path(p).parts}
    hits_tracked = hits & tracked
    matched_by[pattern] = hits
    check(f"AC5 pattern matches a tracked file: {pattern}", bool(hits_tracked), f"{len(hits_tracked)} tracked")
covered = set().union(*matched_by.values())

# Enumerate the validator's reads exactly as validate_plan_readiness.py performs them.
reads = ["planning-mds/BLUEPRINT.md", "docs/agent-instructions.md", "docs/plan-review-checklist.md",
         "planning-mds/features/REGISTRY.md", "scripts/validation/validate_plan_readiness.py"]
checklist = (root / "docs/plan-review-checklist.md").read_text(encoding="utf-8")
rows = [[x.strip().strip("`") for x in line.strip().strip("|").split("|")]
        for line in checklist.splitlines() if line.startswith("|")]
sources = [r[3] for r in rows[2:] if len(r) == 5]
check("AC5 eight governing sources enumerated", len(sources) == 8, repr(sources))
reads += sources
for folder in sorted((root / "planning-mds/features").glob("F[0-9][0-9][0-9][0-9]-*")):
    for name in ["README.md", "STATUS.md", "PRD.md"]:
        if (folder / name).exists():
            reads.append((folder / name).relative_to(root).as_posix())
    reads += [p.relative_to(root).as_posix() for p in folder.glob(f"{folder.name[:5]}-S[0-9][0-9][0-9][0-9]-*.md")]
uncovered = sorted(r for r in set(reads) if r not in covered)
check(f"AC5 every validator read ({len(set(reads))} files) is under a declared pattern", not uncovered, repr(uncovered[:10]))

print(f"\nSUMMARY {'PASS' if not failures else 'FAIL'}: {len(failures)} failed")
sys.exit(1 if failures else 0)
