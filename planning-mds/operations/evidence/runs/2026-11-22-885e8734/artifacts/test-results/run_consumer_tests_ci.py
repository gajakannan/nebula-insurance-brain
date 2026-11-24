"""Reproduce F0011 owned-database checks without exposing connection URLs."""

import os
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree

from sqlalchemy.engine import make_url

run = Path("planning-mds/operations/evidence/runs/2026-11-22-885e8734")
environment = os.environ.copy()
environment["BRAIN_MIGRATION_ADMIN_URL"] = make_url(
    environment["BRAIN_DATABASE_URL"]
).set(drivername="postgresql", database="postgres").render_as_string(hide_password=False)
environment["COVERAGE_FILE"] = str((run / "artifacts/coverage/consumer-ci.coverage").resolve())
command = [
    "pytest", "-c", "engine/pyproject.toml",
    "engine/tests/integration/test_f0011_consumer_contracts.py",
    "engine/tests/integration/test_factslot_answers.py",
    "engine/tests/integration/test_temporal_reads.py",
    "engine/apps/api/tests/test_contract_openapi.py",
    "engine/packages/brain-contracts/tests/test_native_compatibility.py",
    "scripts/contracts/tests/test_stored_fact_versions.py",
    "--cov", "--cov-config=" + str(run / "artifacts/coverage/coverage.rc"),
    "--cov-report=term",
    "--cov-report=xml:" + str(run / "artifacts/coverage/consumer-ci.xml"),
    "--junitxml=" + str(run / "artifacts/test-results/consumer-integration-ci.xml"),
    "-q", "-rs",
]
result = subprocess.run(command, capture_output=True, text=True, env=environment)
pattern = r"postgres(?:ql)?(?:\+[A-Za-z0-9_]+)?://[^\s'\"<>]+"
output = re.sub(pattern, "<database-url-redacted>", result.stdout + result.stderr)
(run / "artifacts/test-results/consumer-integration-ci.txt").write_text(output)
xml_path = run / "artifacts/test-results/consumer-integration-ci.xml"
if xml_path.exists():
    xml_path.write_text(re.sub(pattern, "database-url-redacted", xml_path.read_text()))
    skipped = sum(1 for case in ElementTree.parse(xml_path).iter("testcase") if case.find("skipped") is not None)
else:
    skipped = 0
print(output)
if skipped:
    print("F0011 targeted runtime checks require zero skips")
raise SystemExit(result.returncode or (1 if skipped else 0))
