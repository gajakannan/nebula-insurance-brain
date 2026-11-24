"""Fetch unmodified official Semgrep rules for reproducible F0011 execution."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
entries = []
for pack in ("python", "javascript", "security-audit"):
    url = f"https://semgrep.dev/c/p/{pack}"
    request = Request(url, headers={"User-Agent": "Semgrep/1.169.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        status = response.status
        resolved_url = response.url
    target = ROOT / f"rules-{pack}.yaml"
    target.write_bytes(raw)
    entries.append({
        "registry_pack": f"p/{pack}",
        "request_url": url,
        "resolved_url": resolved_url,
        "status": status,
        "artifact": target.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    })
result = {
    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    "scanner_image": "sha256:2b33f46ba66cf8cc2ad59ccfa7d22951fd00c632c38f1339e84ec8e6e641a942",
    "semgrep_version": "1.169.0",
    "rules": entries,
    "source_scan_executed": False,
}
(ROOT / "rules-provenance.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
