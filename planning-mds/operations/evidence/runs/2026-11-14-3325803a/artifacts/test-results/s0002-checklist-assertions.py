#!/usr/bin/env python3
"""F0064-S0002 AC3/AC4 assertions on docs/plan-review-checklist.md. Usage: <product-root>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
text = (root / "docs/plan-review-checklist.md").read_text(encoding="utf-8")
rows = [[c.strip().strip("`") for c in l.strip().strip("|").split("|")] for l in text.splitlines() if l.startswith("|")]
fails = []
def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f" — {detail}" if detail else "")); ok or fails.append(label)
check("AC3 header columns", rows[0] == ["Rule ID", "Owner", "Criterion", "Governing source", "Planning evidence to inspect"], repr(rows[0]))
body = rows[2:]
ids = [r[0] for r in body]
want = ["BRAIN-SCOPE", "BRAIN-AUTHORITY", "BRAIN-EVIDENCE", "BRAIN-PARSE-ONCE", "BRAIN-TEMPORAL", "BRAIN-AUTHORIZATION", "BRAIN-BUILDABILITY", "BRAIN-EXAMPLES"]
check("AC3 exactly the eight rule IDs", sorted(ids) == sorted(want) and len(ids) == 8, repr(ids))
for r in body:
    check(f"AC3 {r[0]} five non-empty cells", len(r) == 5 and all(r), str(len(r)))
    check(f"AC3 {r[0]} owner allowed ({r[1]})", r[1] in {"product-manager", "architect", "security", "code-reviewer"})
    check(f"AC3 {r[0]} governing source resolves ({r[3]})", (root / r[3]).is_file())
lines = text.splitlines()
l_approval = [i + 1 for i, l in enumerate(lines) if "does not mean approval or regulatory compliance" in l]
l_reason = [i + 1 for i, l in enumerate(lines) if "If a rule does not apply, record the reason explicitly" in l]
check("AC4 script pass is not approval/regulatory compliance", bool(l_approval), f"line {l_approval}")
check("AC4 inapplicable rule needs explicit rationale", bool(l_reason), f"line {l_reason}")
print(f"SUMMARY {'PASS' if not fails else 'FAIL'}: {len(fails)} failed"); sys.exit(1 if fails else 0)
