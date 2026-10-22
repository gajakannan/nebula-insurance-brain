#!/usr/bin/env python3
"""Read-only, parser-free inventory for quiesced local backup/isolated restore."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.dates import ContentDateBasis, verify_content_date_basis
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.outputs import RunManifestV2, parse_run_manifest
from brain_persistence import content_models as tables
from brain_persistence.base import Base
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.document_dates import candidate_record, selection_record
from brain_persistence.models import (
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    ResourceAccessRow,
    SemanticInterpretationRun,
    SourceDocument,
)
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def owner(row):
    return row.tenant_id, row.knowledge_base_id


def snapshot(database_url: str, content_root: Path) -> dict:
    """Verify retained content/history, then describe exact DB and object bytes.

    This is an operator check, not application authorization or a permission
    grant. It makes no repairs and neither reparses nor promotes orphan bytes.
    """
    engine = create_engine(
        database_url.replace("postgresql://", "postgresql+psycopg://")
    )
    objects = LocalFilesystemObjectStore(
        LocalObjectStoreConfig("filesystem", content_root, True)
    )
    store = CheckpointStore(objects)
    referenced = set()
    try:
        with Session(engine) as session:
            repository = ContentArtifactRepository(session)
            artifacts = {
                row.id: row for row in session.scalars(select(ContentArtifact))
            }
            versions = {row.id: row for row in session.scalars(select(DocumentVersion))}
            sources = {row.id: row for row in session.scalars(select(SourceDocument))}
            bundles = {}
            for artifact in artifacts.values():
                version = versions[artifact.document_version_id]
                source = sources[version.source_document_id]
                if owner(artifact) != owner(version) or owner(version) != owner(source):
                    raise ValueError("artifact/version/source owner mismatch")
                security = session.get(
                    ResourceAccessRow, ("content_artifact", artifact.id)
                )
                if security is None or owner(security) != owner(artifact):
                    raise ValueError("artifact security owner mismatch")
                metadata = repository.get_metadata(artifact.id)
                if metadata.publication_state == "quarantined":
                    continue
                bundle = store.load_verified(metadata.key)
                metadata.verify_identity(bundle)
                repository.verify_indexes(bundle)
                bundles[artifact.id] = bundle
                referenced.update(
                    f"{bundle.key.prefix}/{name}" for name in bundle.files
                )
                referenced.add(f"{bundle.key.prefix}/manifest.json")

            candidates = {
                row["id"]: candidate_record(row)
                for row in session.execute(
                    select(tables.document_date_candidate)
                ).mappings()
            }
            selections = {
                row["id"]: selection_record(row)
                for row in session.execute(
                    select(tables.document_date_selection)
                ).mappings()
            }

            def same_version(record, other):
                return (
                    record.document_version_id,
                    record.tenant_id,
                    record.knowledge_base_id,
                ) == (
                    other.document_version_id,
                    other.tenant_id,
                    other.knowledge_base_id,
                )

            def date_owner(record):
                version = versions[record.document_version_id]
                if (record.tenant_id, record.knowledge_base_id) != owner(version):
                    raise ValueError("date/version owner mismatch")
                audit = session.get(AuditEventRow, record.authorization_audit_event_id)
                if audit is None or (
                    audit.decision_id,
                    audit.actor_principal_id,
                    audit.operation_outcome,
                ) != (
                    record.authorization_decision_id,
                    record.actor_principal_id,
                    "succeeded",
                ):
                    raise ValueError("date authorization audit mismatch")

            for candidate in candidates.values():
                date_owner(candidate)
                visited = {candidate.id}
                previous = candidate.supersedes_id
                while previous:
                    predecessor = candidates[previous]
                    if previous in visited or not same_version(candidate, predecessor):
                        raise ValueError("invalid candidate lineage")
                    visited.add(previous)
                    previous = predecessor.supersedes_id
                if isinstance(candidate.basis, ContentDateBasis):
                    bundle = bundles[candidate.basis.artifact_id]
                    if bundle.manifest.version_id != candidate.document_version_id or (
                        bundle.key.tenant_id,
                        bundle.key.knowledge_base_id,
                    ) != (candidate.tenant_id, candidate.knowledge_base_id):
                        raise ValueError("date content basis owner/version mismatch")
                    verify_content_date_basis(bundle, candidate.basis)
            for selection in selections.values():
                date_owner(selection)
                if selection.candidate_id and not same_version(
                    selection, candidates[selection.candidate_id]
                ):
                    raise ValueError("selection candidate belongs to another version")
                if selection.previous_selection_id:
                    previous = selections[selection.previous_selection_id]
                    if (
                        not same_version(selection, previous)
                        or previous.sequence + 1 != selection.sequence
                    ):
                        raise ValueError("invalid selection lineage")
                elif selection.sequence != 1:
                    raise ValueError("selection chain lacks its predecessor")
            run_markers = {}
            for path in sorted(content_root.glob("runs/*/*/*/manifest.json")):
                relative = path.relative_to(content_root).as_posix()
                marker = parse_run_manifest(objects.read(relative))
                bundle = bundles[marker.artifact_id]
                expected = (
                    f"runs/{marker.tenant_id}/{marker.knowledge_base_id}/"
                    f"{marker.run_id}/manifest.json"
                )
                if relative != expected:
                    raise ValueError("run marker path/owner mismatch")
                verified = store.load_run_bundle(
                    tenant_id=marker.tenant_id,
                    knowledge_base_id=marker.knowledge_base_id,
                    artifact_id=marker.artifact_id,
                    run_id=marker.run_id,
                    artifact_key=bundle.key,
                )
                if (
                    isinstance(marker, RunManifestV2)
                    and marker.document_date_selection_id
                ):
                    pinned = selections[marker.document_date_selection_id]
                    if (
                        pinned.document_version_id,
                        pinned.tenant_id,
                        pinned.knowledge_base_id,
                    ) != (
                        bundle.manifest.version_id,
                        marker.tenant_id,
                        marker.knowledge_base_id,
                    ):
                        raise ValueError("run date selection owner/version mismatch")
                run_markers[marker.run_id] = marker
                prefix = relative.removesuffix("manifest.json")
                referenced.add(relative)
                referenced.update(prefix + name for name in verified.files)
            for run in session.scalars(select(SemanticInterpretationRun)):
                artifact = artifacts[run.artifact_id]
                if owner(run) != owner(artifact) or run.id not in run_markers:
                    raise ValueError("retained run missing or has another owner")
                if run_markers[run.id].artifact_id != run.artifact_id:
                    raise ValueError("retained run artifact mismatch")

            # Hash every application table, including date/audit/repair history.
            # Source and restored inventories must match byte-for-byte after
            # canonical ordering, rather than merely comparing row counts.
            existing = set(inspect(session.connection()).get_table_names())
            database = {}
            for table in Base.metadata.sorted_tables:
                if table.name in existing:
                    rows = sorted(
                        canonical(dict(row))
                        for row in session.execute(select(table)).mappings()
                    )
                    database[table.name] = {
                        "rows": len(rows),
                        "sha256": digest(b"\n".join(rows)),
                    }
            revision = session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        inventory = []
        for path in sorted(content_root.rglob("*")):
            if path.is_symlink():
                raise ValueError("content snapshot contains a symlink")
            if path.is_file():
                relative = path.relative_to(content_root).as_posix()
                raw = path.read_bytes()
                inventory.append(
                    {"path": relative, "size_bytes": len(raw), "sha256": digest(raw)}
                )
        return {
            "inventory_version": 2,
            "database_revision": revision,
            "database": database,
            "objects": inventory,
            "verified_artifacts": sorted(str(value) for value in bundles),
            "verified_runs": sorted(str(value) for value in run_markers),
            "unreferenced_objects": sorted(
                entry["path"] for entry in inventory if entry["path"] not in referenced
            ),
        }
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--content-root", type=Path, required=True)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--expect", type=Path)
    args = parser.parse_args()
    result = snapshot(args.database_url, args.content_root)
    if args.expect and json.loads(args.expect.read_bytes()) != result:
        raise ValueError(
            "restored database/content inventory differs from quiesced snapshot"
        )
    if args.write:
        args.write.write_bytes(
            json.dumps(result, indent=2, sort_keys=True).encode() + b"\n"
        )
    print(
        json.dumps(
            {
                "database_revision": result["database_revision"],
                "verified_artifacts": len(result["verified_artifacts"]),
                "verified_runs": len(result["verified_runs"]),
                "unreferenced_objects": len(result["unreferenced_objects"]),
                "status": "verified",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
