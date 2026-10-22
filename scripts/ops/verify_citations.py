#!/usr/bin/env python3
"""Resolve restored citations through trusted v1/v2 keys and common verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg
from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.object_store import LocalFilesystemObjectStore, ObjectNotFoundError
from brain_content.validation import ArtifactIntegrityError, ArtifactKey


def verify(*, database_url: str, content_root: Path) -> tuple[int, int, list[str]]:
    """Returns (resolved_count, total_count, failure_descriptions)."""
    failures: list[str] = []
    resolved = 0
    total = 0

    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT e.id,e.assertion_id,e.artifact_id,e.block_id,e.page,e.precision,"
            "a.tenant_id,a.knowledge_base_id,COALESCE(a.artifact_contract_version,1),"
            "e.tenant_id,e.knowledge_base_id "
            "FROM assertion_evidence e JOIN content_artifact a ON a.id=e.artifact_id"
        )
        rows = cursor.fetchall()

    store = CheckpointStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", content_root, True))
    )
    for (
        row_id,
        assertion_id,
        artifact_id,
        block_id,
        page,
        _precision,
        tenant,
        kb,
        version,
        evidence_tenant,
        evidence_kb,
    ) in rows:
        total += 1
        if (tenant, kb) != (evidence_tenant, evidence_kb):
            failures.append(f"evidence {row_id}: artifact owner mismatch")
            continue
        try:
            bundle = store.load_verified(ArtifactKey(artifact_id, tenant, kb, version))
        except (
            ArtifactIntegrityError,
            ArtifactVersionUnsupported,
            ObjectNotFoundError,
            PermissionError,
            OSError,
            ValueError,
        ) as exc:
            failures.append(f"evidence {row_id}: bundle verification failed ({type(exc).__name__})")
            continue
        if block_id is not None:
            blocks = [
                json.loads(line) for line in bundle.files["blocks.jsonl"].splitlines() if line
            ]
            if not any(b.get("block_id") == block_id for b in blocks):
                failures.append(
                    f"evidence {row_id} (assertion {assertion_id}): block_id={block_id!r} "
                    "not found in verified blocks"
                )
                continue
        elif page is not None:
            layout = [
                json.loads(line) for line in bundle.files["layout.jsonl"].splitlines() if line
            ]
            if not any(entry.get("page") == page for entry in layout):
                failures.append(
                    f"evidence {row_id} (assertion {assertion_id}): page={page} "
                    "not found in verified layout"
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
