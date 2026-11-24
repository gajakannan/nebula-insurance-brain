"""Reconcile already-scanned code hashes after dependency metadata changes."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

folder = Path(__file__).resolve().parent
record = json.loads((folder / "source-inputs.json").read_text())
root = Path(record["product_root"])
spec = importlib.util.spec_from_file_location("f0011_selected_source", folder / "prepare_source.py")
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)
current = {path for path in selection.selected_paths() if Path(path).suffix in selection.EXTENSIONS}
scanned = {item["path"] for item in record["files"]}
changed = []
for item in record["files"]:
    path = root / item["path"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        changed.append(item["path"])
report = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "pass" if not changed and current == scanned else "fail",
    "scanned_code_files": len(scanned),
    "changed_scanned_code": changed,
    "new_unscanned_code": sorted(current - scanned),
    "no_longer_selected_code": sorted(scanned - current),
    "source_manifest": "source-inputs.json",
    "scan_receipt": "final-timeout60/execution.json",
}
(folder / "current-input-reconciliation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
raise SystemExit(0 if report["status"] == "pass" else 1)
