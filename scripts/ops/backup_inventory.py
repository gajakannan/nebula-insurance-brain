#!/usr/bin/env python3
"""Seal/check local backup files and safely extract the content snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path

REQUIRED = {
    "db.dump",
    "content.tar.gz",
    "content-inventory.json",
    "DEPENDENCY-MATRIX.md",
    "engine.uv.lock",
    "neuron.uv.lock",
    "contracts/content-records-v2.schema.json",
    "contracts/content-artifact-manifest.schema.json",
    "contracts/content-artifact-manifest-v2.schema.json",
    "contracts/document-date-record.schema.json",
    "contracts/interpretation-output-manifest.schema.json",
}


def inventory(folder):
    result = []
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError("backup contains symlinks")
        if path.is_file() and path != folder / "manifest.json":
            raw = path.read_bytes()
            result.append(
                {
                    "path": path.relative_to(folder).as_posix(),
                    "size_bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    if not {entry["path"] for entry in result} >= REQUIRED:
        raise ValueError("backup lacks required dependency/contract/content files")
    return result


def seal(folder):
    content = json.loads((folder / "content-inventory.json").read_bytes())
    manifest = {
        "backup_version": 2,
        "writers_quiesced": True,
        "created_at": datetime.now(UTC).isoformat(),
        "database_revision": content["database_revision"],
        "files": inventory(folder),
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def verify(folder):
    manifest = json.loads((folder / "manifest.json").read_bytes())
    if (
        manifest.get("backup_version") != 2
        or manifest.get("writers_quiesced") is not True
    ):
        raise ValueError("backup is not a verified quiesced v2 local snapshot")
    if manifest["files"] != inventory(folder):
        raise ValueError("backup file inventory mismatch")
    content = json.loads((folder / "content-inventory.json").read_bytes())
    if content["database_revision"] != manifest["database_revision"]:
        raise ValueError("backup database revision mismatch")


def extract(folder, destination):
    verify(folder)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("restore content target must be empty")
    with tarfile.open(folder / "content.tar.gz") as archive:
        if any(
            not (member.isdir() or member.isfile()) for member in archive.getmembers()
        ):
            raise ValueError("content archive contains links or special files")
        archive.extractall(destination, filter="data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["seal", "verify", "extract"])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action == "seal":
        seal(args.folder)
    elif args.action == "verify":
        verify(args.folder)
    elif args.destination:
        extract(args.folder, args.destination)
    else:
        parser.error("extract requires --destination")
    print(f"Backup {args.action}: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
