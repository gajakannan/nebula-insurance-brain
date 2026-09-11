from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import (
    ArtifactManifest,
    DoclingDocumentRef,
    ExecutionRecord,
    ExtractionQuality,
)
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import ArtifactExists, ArtifactNotFound, LocalContentArtifactStore


def _make_store(tmp_path: Path) -> LocalContentArtifactStore:
    config = LocalObjectStoreConfig(
        provider="filesystem", root=tmp_path / "content", immutable=True
    )
    return LocalContentArtifactStore(LocalFilesystemObjectStore(config))


def _make_manifest(artifact_id=None) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_contract_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=artifact_id or uuid4(),
        source_sha256="a" * 64,
        artifact_sha256="b" * 64,
        docling_document=DoclingDocumentRef(
            path="docling-document.json", schema_version="1.0", sha256="c" * 64
        ),
        files=[],
        execution=ExecutionRecord(
            parser_package_version="docling==2.126.0",
            model_artifact_digests=[],
            configuration_hash="d" * 64,
            environment_digest="e" * 64,
        ),
        extraction_quality=ExtractionQuality(status="complete", failed_pages=[], warnings=[]),
        page_count=1,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_put_bundle_then_get_manifest_round_trips(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    manifest = _make_manifest()

    await store.put_bundle(manifest, {"normalized.md": b"# hello"})
    fetched = await store.get_manifest(manifest.artifact_id)

    assert fetched.artifact_id == manifest.artifact_id
    assert fetched.source_sha256 == manifest.source_sha256


@pytest.mark.asyncio
async def test_open_file_reads_a_bundled_file(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    manifest = _make_manifest()

    await store.put_bundle(manifest, {"normalized.md": b"# hello"})

    assert await store.open_file(manifest.artifact_id, "normalized.md") == b"# hello"


@pytest.mark.asyncio
async def test_put_bundle_twice_raises_artifact_exists(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    manifest = _make_manifest()
    await store.put_bundle(manifest, {"a.txt": b"1"})

    with pytest.raises(ArtifactExists):
        await store.put_bundle(manifest, {"a.txt": b"2"})


@pytest.mark.asyncio
async def test_get_manifest_missing_raises_not_found(tmp_path: Path) -> None:
    store = _make_store(tmp_path)

    with pytest.raises(ArtifactNotFound):
        await store.get_manifest(uuid4())


@pytest.mark.asyncio
async def test_open_file_missing_raises_not_found(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    manifest = _make_manifest()
    await store.put_bundle(manifest, {})

    with pytest.raises(ArtifactNotFound):
        await store.open_file(manifest.artifact_id, "missing.txt")
