#!/usr/bin/env python3
"""Run the product-local gates declared in lifecycle-stage.yaml (CONSUMER-CONTRACT §6).

    python3 scripts/run-lifecycle-gates.py            # gates for current_stage
    python3 scripts/run-lifecycle-gates.py --list     # stage/gate matrix
    python3 scripts/run-lifecycle-gates.py --stage implementation

Commands run shell-free from the repository root. The framework's own runner executes from
the framework root and does not expand {PRODUCT_ROOT}, so this product carries its own.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / "lifecycle-stage.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run product lifecycle gates")
    parser.add_argument("--stage", default="", help="Stage override (default: current_stage)")
    parser.add_argument("--list", action="store_true", help="Print the stage/gate matrix and exit")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    stages, gates = config["stages"], config["gates"]
    stage = args.stage or config["current_stage"]
    if stage not in stages:
        print(f"[ERROR] unknown stage {stage!r}; known: {', '.join(stages)}")
        return 2

    if args.list:
        for name, spec in stages.items():
            print(f"{name}: {spec.get('description', '').strip()}")
            for gate in spec.get("required_gates", []) or ["(none)"]:
                print(f"  - {gate}")
        print(f"Current stage: {config['current_stage']}")
        return 0

    failures: list[str] = []
    print(f"Running lifecycle gates for stage: {stage}")
    for name in stages[stage].get("required_gates", []):
        gate = gates[name]
        command = gate["command"]
        print(f"[GATE] {name}\n  {gate.get('description', '').strip()}\n  command: {' '.join(command)}")
        rc = subprocess.run(command, cwd=REPO_ROOT).returncode
        print(f"[{'PASS' if rc == 0 else 'FAIL'}] {name}\n")
        if rc != 0:
            failures.append(name)
    if failures:
        print(f"[SUMMARY] FAILED ({len(failures)}): {', '.join(failures)}")
        return 1
    print(f"[SUMMARY] PASSED ({len(stages[stage].get('required_gates', []))} gate(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
