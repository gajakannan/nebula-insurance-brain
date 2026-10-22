from __future__ import annotations

import json
from uuid import uuid4

import pytest
from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.outputs import PipelineIdentity, RunManifestV2, parse_run_manifest
from brain_content.validation import ArtifactIntegrityError

from .test_versioned_content import bundle_fixture, seal


@pytest.fixture(params=[1, 2])
def content(request, tmp_path):
    manifest, files = bundle_fixture()
    if request.param == 1:
        for name in (
            "source_file",
            "recipe_sha256",
            "bundle_hash_algorithm",
            "record_contract_version",
            "page_number_base",
            "coordinate_units",
            "text_normalization_version",
        ):
            manifest.pop(name)
        manifest["execution"].pop("parser_name")
        manifest["execution"].pop("projection_version")
        manifest["artifact_contract_version"] = 1
    key, raw, files = seal(manifest, files)
    store = CheckpointStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    )
    store.verified.publish(key, raw, files)
    return store, key, raw


@pytest.mark.parametrize("output_version", [1, 2])
@pytest.mark.parametrize("selection", [None, "pinned"])
def test_output_versions_are_independent_of_parse_version_and_pin_the_exact_basis(
    content, output_version, selection
):
    store, key, original = content
    run_id = uuid4()
    files = {
        name: b"{}" for name in ("result.json", "provenance.json", "graph.json", "metadata.json")
    }
    pipeline = PipelineIdentity(
        name="docling-graph", package_version="synthetic-1", configuration_sha256="a" * 64
    )
    selected_id = uuid4() if selection else None
    options = (
        dict(pipeline=pipeline, document_date_selection_id=selected_id)
        if output_version == 2
        else {}
    )
    ref = store.publish_run(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=key.artifact_id,
        artifact_key=key,
        run_id=run_id,
        files=files,
        output_contract_version=output_version,
        **options,
    )
    retained = store.objects.read(ref)
    verified = store.load_run_bundle(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=key.artifact_id,
        artifact_key=key,
        run_id=run_id,
    )
    assert verified.manifest_bytes == retained and dict(verified.files) == files
    if output_version == 2:
        assert isinstance(verified.manifest, RunManifestV2)
        assert verified.manifest.document_date_selection_id == selected_id
        assert verified.manifest.pipeline == pipeline
        with pytest.raises(ArtifactIntegrityError):
            store.publish_run(
                tenant_id=key.tenant_id,
                knowledge_base_id=key.knowledge_base_id,
                artifact_id=key.artifact_id,
                artifact_key=key,
                run_id=run_id,
                files=files,
                output_contract_version=2,
                pipeline=pipeline,
                document_date_selection_id=uuid4(),
            )
    else:
        assert "pipeline" not in json.loads(retained)
        assert "document_date_selection_id" not in json.loads(retained)
    assert store.load_verified(key).manifest_bytes == original
    # Closed inventory is checked on every read, including after process restart.
    store.objects.create_exclusive(ref.removesuffix("manifest.json") + "unexpected.bin", b"extra")
    with pytest.raises(ArtifactIntegrityError):
        CheckpointStore(store.objects).load_run(
            tenant_id=key.tenant_id,
            knowledge_base_id=key.knowledge_base_id,
            artifact_id=key.artifact_id,
            artifact_key=key,
            run_id=run_id,
        )


def test_run_marker_dispatch_is_strict_and_never_falls_back():
    for version in (3, True, "2", None):
        with pytest.raises(ArtifactVersionUnsupported):
            parse_run_manifest(json.dumps({"contract_version": version}).encode())
    with pytest.raises(ArtifactIntegrityError):
        parse_run_manifest(b'{"contract_version": 1, "contract_version": 2}')
