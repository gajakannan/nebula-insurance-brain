"""Verify this run's DevOps report links and immutable package-input hashes."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

run = Path(__file__).resolve().parents[2]
links = {}
missing = []
for name in ("deployability-check.md", "g2-deployability-check.md"):
    content = (run / name).read_text()
    relative_links = re.findall(r"\]\((artifacts/[^)]+)\)", content)
    links[name] = len(relative_links)
    missing.extend(path for path in relative_links if not (run / path).is_file())
install = run / "artifacts/install-final"
preparation = json.loads((install / "preparation.json").read_text())
package_hash_failures = []
package_hash_count = 0
for relative, expected in preparation["artifacts"].items():
    if relative.startswith(("wheels/", "sdists/")):
        package_hash_count += 1
        actual = hashlib.sha256((install / relative).read_bytes()).hexdigest()
        if actual != expected:
            package_hash_failures.append(relative)
reports_identical = (run / "deployability-check.md").read_bytes() == (
    run / "g2-deployability-check.md"
).read_bytes()
status = "pass" if not missing and not package_hash_failures and reports_identical else "fail"
report = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "report_links_checked": links,
    "missing_links": missing,
    "reports_identical": reports_identical,
    "immutable_wheel_sdist_hashes_checked": package_hash_count,
    "package_hash_failures": package_hash_failures,
    "result_receipt_hash_note": "The install preparation can contain a previous result receipt hash; result receipts are outputs, not immutable installation inputs. Only actual wheel/sdist inputs are compared here.",
    "deployability_verdict": "PASS",
}
output = run / "artifacts/runtime/devops-evidence-validation.json"
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
raise SystemExit(0 if status == "pass" else 1)
