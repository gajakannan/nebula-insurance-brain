from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_content.checkpoints import ArtifactIntegrityError, CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import (
    ArtifactFile,
    ArtifactManifest,
    DoclingDocumentRef,
    ExecutionRecord,
    ExtractionQuality,
)
from brain_content.object_store import LocalFilesystemObjectStore, ObjectNotFoundError


@pytest.fixture
def checkpoint(tmp_path):
    files = {
        name: b"{}"
        for name in (
            "docling-document.json",
            "blocks.jsonl",
            "layout.jsonl",
            "tables.jsonl",
            "normalized.md",
        )
    }
    files["source.pdf"] = b"source"
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    manifest = ArtifactManifest(
        artifact_contract_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256=hashes["source.pdf"],
        artifact_sha256=hashlib.sha256(
            "".join(hashes[n] for n in sorted(hashes)).encode()
        ).hexdigest(),
        docling_document=DoclingDocumentRef(
            path="docling-document.json", schema_version="1", sha256=hashes["docling-document.json"]
        ),
        files=[ArtifactFile(path=n, sha256=hashes[n], size_bytes=len(v)) for n, v in files.items()],
        execution=ExecutionRecord(
            parser_package_version="fixture",
            model_artifact_digests=[],
            configuration_hash="a" * 64,
            environment_digest="b" * 64,
        ),
        extraction_quality=ExtractionQuality(status="complete", failed_pages=[], warnings=[]),
        page_count=1,
        created_at=datetime.now(UTC),
    )
    store = CheckpointStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    )
    return store, manifest, files


def test_checkpoint_resume_and_scope_integrity(checkpoint):
    store, manifest, files = checkpoint
    prefix = f"bundles/{manifest.artifact_id}"
    with pytest.raises(ObjectNotFoundError):
        store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)
    store.objects.create_exclusive(f"{prefix}/normalized.md", files["normalized.md"])
    assert store.publish(manifest, files) == manifest
    assert (
        store.publish(manifest.model_copy(update={"created_at": datetime.now(UTC)}), files)
        == manifest
    )
    assert (
        store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)[1] == files
    )
    with pytest.raises(PermissionError):
        store.load(manifest.artifact_id, uuid4(), manifest.knowledge_base_id)
    with pytest.raises(ArtifactIntegrityError, match="identity conflict"):
        store.publish(manifest.model_copy(update={"document_id": uuid4()}), files)
    store.objects.delete(f"{prefix}/normalized.md")
    with pytest.raises(ArtifactIntegrityError, match="missing a file"):
        store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)


@pytest.mark.parametrize("fault", ["inventory", "hash", "aggregate", "native", "unsafe"])
def test_corrupt_bundle_is_never_published(checkpoint, fault):
    store, manifest, files = checkpoint
    if fault == "inventory":
        files.pop("blocks.jsonl")
    elif fault == "hash":
        files["blocks.jsonl"] = b"corrupted"
    elif fault == "aggregate":
        manifest = manifest.model_copy(update={"artifact_sha256": "0" * 64})
    elif fault == "native":
        manifest = manifest.model_copy(
            update={
                "docling_document": DoclingDocumentRef(
                    path="absent.json", schema_version="1", sha256="a" * 64
                )
            }
        )
    else:
        manifest.files[0].path = "../escape"
        files["../escape"] = files.pop("docling-document.json")
    with pytest.raises(ArtifactIntegrityError):
        store.publish(manifest, files)
    assert not store.objects.exists(f"bundles/{manifest.artifact_id}/manifest.json")


def test_run_publication_is_immutable_scoped_and_hash_verified(checkpoint):
    store, manifest, files = checkpoint
    store.publish(manifest, files)
    run_id = uuid4()
    scope = dict(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        run_id=run_id,
    )
    outputs = {
        name: b"{}" for name in ("result.json", "metadata.json", "graph.json", "provenance.json")
    }
    with pytest.raises(ArtifactIntegrityError, match="inventory"):
        store.publish_run(**scope, files={})
    marker = store.publish_run(**scope, files=outputs)
    assert store.publish_run(**scope, files=outputs) == marker
    assert store.load_run(**scope) == outputs
    with pytest.raises(ArtifactIntegrityError, match="conflict"):
        store.publish_run(**scope, files={**outputs, "result.json": b"changed"})
    with pytest.raises(PermissionError):
        store.load_run(**{**scope, "knowledge_base_id": uuid4()})
    result_key = marker.removesuffix("manifest.json") + "result.json"
    store.objects.delete(result_key)
    with pytest.raises(ArtifactIntegrityError, match="missing a file"):
        store.load_run(**scope)
    store.objects.create_exclusive(result_key, b"tampered")
    with pytest.raises(ArtifactIntegrityError, match="hash"):
        store.load_run(**scope)
    data = json.loads(store.objects.read(marker))
    data["run_id"] = str(uuid4())
    store.objects.delete(marker)
    store.objects.create_exclusive(marker, json.dumps(data).encode())
    with pytest.raises(ArtifactIntegrityError, match="identity"):
        store.load_run(**scope)
