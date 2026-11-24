"""Snapshot changed F0011 Python/JS/TS source immediately before SAST."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PRODUCT = Path("/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain")
OUTPUT = Path(__file__).resolve().parent
BASE = "bf78e111934570f83439057ea3c73a1eaefbb022"
EXTENSIONS = {".py", ".mjs", ".js", ".jsx", ".ts", ".tsx"}
CACHE_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache", "dist", "build", "coverage", ".next"}
SOURCE_PATHS = [".", ":(exclude)planning-mds/operations/**"]

def git_lines(*arguments):
    value = subprocess.check_output(["git", *arguments], cwd=PRODUCT, text=True)
    return value.splitlines()

def selected_paths():
    """Return all changed/untracked existing files without evidence or caches."""
    paths = set(git_lines("diff", "--name-only", BASE, "--", *SOURCE_PATHS))
    paths.update(git_lines("ls-files", "--others", "--exclude-standard", "--", *SOURCE_PATHS))
    return sorted(
        path for path in paths
        if not (set(Path(path).parts) & CACHE_PARTS) and (PRODUCT / path).is_file()
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-all", action="store_true", help="Read-only JSON list of all source extensions; no snapshot is written.")
    arguments = parser.parse_args()
    paths = selected_paths()
    if arguments.list_all:
        print(json.dumps(paths, indent=2))
        return
    selected = [path for path in paths if Path(path).suffix in EXTENSIONS]
    if (OUTPUT / "source").exists():
        raise SystemExit("Source snapshot already exists; preserve it and use a new evidence directory for reruns.")
    entries = []
    for relative in selected:
        source = PRODUCT / relative
        data = source.read_bytes()
        target = OUTPUT / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (OUTPUT / "source" / ".semgrepignore").write_text("")
    record = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "product_root": str(PRODUCT),
        "base_ref": BASE,
        "head_ref": git_lines("rev-parse", "HEAD")[0],
        "selection": "Existing changed and untracked Python/JS/TS files, excluding cold evidence and caches; generated Python and tests included.",
        "files": entries,
    }
    (OUTPUT / "source-inputs.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"files": len(entries), "artifact": str(OUTPUT / "source-inputs.json")}))

if __name__ == "__main__":
    main()
