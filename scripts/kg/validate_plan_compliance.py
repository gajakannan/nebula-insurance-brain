#!/usr/bin/env python3
"""Compatibility entry point; use scripts/validation/validate_plan_readiness.py."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/validation"))
from validate_plan_readiness import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 1 and not args[0].startswith("-"):
        target = Path(args[0]).resolve()
        features = ROOT / "planning-mds/features"
        if not target.is_relative_to(features) or not target.is_file():
            print("Provide an existing plan inside this product's feature tree.", file=sys.stderr)
            raise SystemExit(2)
        feature = target.relative_to(features).parts[0].split("-", 1)[0]
        if not re.fullmatch(r"F\d{4}", feature):
            print("The target must belong to an active F#### feature folder.", file=sys.stderr)
            raise SystemExit(2)
        args = ["--plan-scope", "feature", "--target", feature]
    raise SystemExit(main(args))
