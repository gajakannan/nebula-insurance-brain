"""Summarize raw scan facts and verify they still match the live feature files."""
import argparse
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
PRODUCT = Path("/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain")
parser = argparse.ArgumentParser()
parser.add_argument("--report-subdir", default="final")
arguments = parser.parse_args()
REPORT = OUTPUT / arguments.report_subdir
inputs = json.loads((OUTPUT / "source-inputs.json").read_text())
execution = json.loads((REPORT / "execution.json").read_text())
raw = json.loads((REPORT / "results.json").read_text())
scanned = raw.get("paths", {}).get("scanned", [])
expected = {item["path"] for item in inputs["files"]}
normalized = {str(Path(path)).removeprefix("/evidence/source/").removeprefix("./") for path in scanned}
changed = []
for item in inputs["files"]:
    path = PRODUCT / item["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if digest != item["sha256"]:
        changed.append(item["path"])
specification = importlib.util.spec_from_file_location("sast_source_selection", OUTPUT / "prepare_source.py")
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)
current = {path for path in module.selected_paths() if Path(path).suffix in module.EXTENSIONS}
sarif_files = sorted(REPORT.glob("*.sarif"))
rules = []
for sarif_file in sarif_files:
    sarif = json.loads(sarif_file.read_text())
    rules.extend(rule for run in sarif.get("runs", []) for rule in run.get("tool", {}).get("driver", {}).get("rules", []))
findings = raw.get("results", [])
rule_count = re.search(r"Ran (\d+) rules on", (REPORT / "wrapper.log").read_text())
control_files = normalized & {".semgrepignore"}
summary = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "semgrep_version": raw.get("version", execution["semgrep_version"]),
    "report_subdirectory": arguments.report_subdir,
    "wrapper_exit_code": execution["exit_code"],
    "input_files": len(expected),
    "scanned_source_files": len(expected & normalized),
    "scanned_total_files": len(normalized),
    "scanner_control_files": sorted(control_files),
    "configured_rules": len({rule["id"] for rule in rules}),
    "applicable_rules_run": int(rule_count.group(1)) if rule_count else None,
    "findings": len(findings),
    "findings_by_severity": dict(Counter(item.get("extra", {}).get("severity", "UNKNOWN") for item in findings)),
    "scanner_errors": raw.get("errors", []),
    "unscanned_inputs": sorted(expected - normalized),
    "unexpected_scanned_files": sorted(normalized - expected - control_files),
    "source_changes_after_snapshot": changed,
    "new_source_paths_after_snapshot": sorted(current - expected),
    "removed_source_paths_after_snapshot": sorted(expected - current),
    "sarif_artifacts": [str(path.relative_to(OUTPUT)) for path in sarif_files],
    "findings_index": [{
        "rule_id": item["check_id"],
        "path": item["path"],
        "line": item.get("start", {}).get("line"),
        "severity": item.get("extra", {}).get("severity"),
    } for item in findings],
    "security_verdict_owner": "Security Reviewer",
}
(OUTPUT / f"execution-summary-{arguments.report_subdir}.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
