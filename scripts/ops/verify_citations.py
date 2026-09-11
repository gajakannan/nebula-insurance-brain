#!/usr/bin/env python3
"""Verify every S0003 evidence binding resolves to a real block/page in the
restored content root (F0001-S0006 restore-drill acceptance criterion:
"every citation from S0003 resolves").

A citation is one `assertion_evidence` row. It resolves if:
  - its artifact's bundle manifest exists at
    `<content_root>/bundles/<artifact_id>/manifest.json`, and
  - when `block_id` is set, a line in that bundle's `blocks.jsonl` has a
    matching `block_id`;
  - when `block_id` is null (page/document-level precision), `page` (if set)
    is one of the pages listed in that bundle's `layout.jsonl`.

Usage:
    python3 scripts/ops/verify_citations.py --database-url <url> --content-root <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg


def _bundle_dir(content_root: Path, artifact_id: str) -> Path:
    return content_root / "bundles" / artifact_id


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify(*, database_url: str, content_root: Path) -> tuple[int, int, list[str]]:
    """Returns (resolved_count, total_count, failure_descriptions)."""
    failures: list[str] = []
    resolved = 0
    total = 0

    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, assertion_id, artifact_id, block_id, page, precision "
            "FROM assertion_evidence"
        )
        rows = cursor.fetchall()

    for row_id, assertion_id, artifact_id, block_id, page, _precision in rows:
        total += 1
        bundle_dir = _bundle_dir(content_root, str(artifact_id))
        manifest_path = bundle_dir / "manifest.json"
        if not manifest_path.is_file():
            failures.append(
                f"evidence {row_id} (assertion {assertion_id}): bundle manifest missing "
                f"at {manifest_path}"
            )
            continue

        if block_id is not None:
            blocks = _load_jsonl(bundle_dir / "blocks.jsonl")
            if not any(b.get("block_id") == block_id for b in blocks):
                failures.append(
                    f"evidence {row_id} (assertion {assertion_id}): block_id={block_id!r} "
                    f"not found in {bundle_dir / 'blocks.jsonl'}"
                )
                continue
        elif page is not None:
            layout = _load_jsonl(bundle_dir / "layout.jsonl")
            if not any(entry.get("page") == page for entry in layout):
                failures.append(
                    f"evidence {row_id} (assertion {assertion_id}): page={page} "
                    f"not found in {bundle_dir / 'layout.jsonl'}"
                )
                continue
        # precision == "unresolved" or document-level: manifest presence alone is
        # the citation (there is no tighter grounding to check by design).

        resolved += 1

    return resolved, total, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--content-root", required=True, type=Path)
    args = parser.parse_args()

    resolved, total, failures = verify(
        database_url=args.database_url, content_root=args.content_root
    )

    print(f"Citations checked: {total}; resolved: {resolved}; failed: {len(failures)}")
    for failure in failures:
        print(f"  FAIL: {failure}", file=sys.stderr)

    if total == 0:
        print("warning: no assertion_evidence rows found — nothing was actually verified.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
