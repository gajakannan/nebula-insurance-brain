"""Execute the required framework wrapper over an immutable feature snapshot."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("/evidence")
parser = argparse.ArgumentParser()
parser.add_argument("--report-subdir", default="final")
parser.add_argument("--timeout", type=int, default=5)
arguments = parser.parse_args()
REPORT = OUTPUT / arguments.report_subdir
REPORT.mkdir(exist_ok=True)
environment = dict(os.environ)
environment.update(SEMGREP_SEND_METRICS="off", SEMGREP_ENABLE_VERSION_CHECK="0")
provenance = json.loads((OUTPUT / "rules-provenance.json").read_text())
for entry in provenance["rules"]:
    digest = hashlib.sha256((OUTPUT / entry["artifact"]).read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"Rule pack integrity mismatch: {entry['artifact']}")
inputs = json.loads((OUTPUT / "source-inputs.json").read_text())
for entry in inputs["files"]:
    digest = hashlib.sha256((OUTPUT / "source" / entry["path"]).read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"Source snapshot integrity mismatch: {entry['path']}")
version = subprocess.check_output(["semgrep", "--version"], env=environment, text=True).strip()
command = [
    "sh", "/framework/agents/security/scripts/run-sast-scan.sh",
    "--path", ".", "--config", "/evidence/rules-python.yaml",
    "--report-dir", str(REPORT), "--",
    "--config", "/evidence/rules-javascript.yaml",
    "--config", "/evidence/rules-security-audit.yaml",
    "--metrics=off", "--disable-version-check", "--strict", "--oss-only",
    "--no-git-ignore", "--disable-nosem", "--x-ignore-semgrepignore-files",
    "--json-output", str(REPORT / "results.json"),
    "--text-output", str(REPORT / "results.txt"),
    "--jobs", "2", "--timeout", str(arguments.timeout), "--verbose",
]
started = datetime.now(timezone.utc).isoformat()
with (REPORT / "wrapper.log").open("w") as log:
    result = subprocess.run(command, cwd=OUTPUT / "source", env=environment, stdout=log, stderr=subprocess.STDOUT)
execution = {
    "started_at_utc": started,
    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    "semgrep_version": version,
    "scanner_image": "sha256:2b33f46ba66cf8cc2ad59ccfa7d22951fd00c632c38f1339e84ec8e6e641a942",
    "required_framework_wrapper": "/framework/agents/security/scripts/run-sast-scan.sh",
    "framework_wrapper_sha256": hashlib.sha256(Path(command[1]).read_bytes()).hexdigest(),
    "command_argv": command,
    "cwd": "/evidence/source",
    "exit_code": result.returncode,
    "source_inputs": "source-inputs.json",
    "rules_provenance": "rules-provenance.json",
    "rule_pack_integrity_verified": True,
    "source_snapshot_integrity_verified": True,
    "security_verdict_owner": "Security Reviewer",
}
(REPORT / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
print(json.dumps(execution, indent=2))
print((REPORT / "wrapper.log").read_text()[-6000:])
raise SystemExit(result.returncode)
