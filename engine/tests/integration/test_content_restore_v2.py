"""Real dump/restore drill in unique databases; no application parser or repair."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from brain_content.checkpoints import CheckpointStore
from brain_content.dates import DocumentDateValue
from brain_content.outputs import PipelineIdentity
from brain_content.validation import ArtifactIntegrityError
from brain_persistence.models import Assertion, AssertionEvidence
from sqlalchemy import text
from sqlalchemy.orm import Session

PRODUCT = Path(__file__).resolve().parents[3]
_helpers = runpy.run_path(str(Path(__file__).with_name("test_content_migration_states.py")))
database = _helpers["database"]
publication = _helpers["publication"]
date_services = _helpers["date_services"]
_clean_fact_tables = _helpers["_clean_fact_tables"]
ControlledHumanVerifier = _helpers["ControlledHumanVerifier"]
content_basis = _helpers["content_basis"]
_snapshot = runpy.run_path(str(PRODUCT / "scripts/ops/verify_content.py"))["snapshot"]
_backup = runpy.run_path(str(PRODUCT / "scripts/ops/backup_inventory.py"))


@pytest.mark.parametrize("publication", [1, 2], indirect=True)
async def test_dump_and_isolated_restore_preserve_bytes_indexes_and_date_lineage(
    date_services, database, tmp_path
):
    services, actor, human, bundle, publisher = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)
    async with services(human_selections=verifier) as service:
        candidate = await service.append_candidate(
            actor,
            artifact_id=bundle.key.artifact_id,
            date=DocumentDateValue(precision="DAY", value="2024-02-29"),
            basis=content_basis(bundle),
            supersedes_id=None,
            idempotency_key="restore-date",
            trace_id="restore-date",
        )
        selected = await service.select(
            actor,
            artifact_id=bundle.key.artifact_id,
            candidate_id=candidate.id,
            expected_selection_id=None,
            human_decision_id=verifier.selection(candidate.id),
            reason="controlled restore fixture",
            idempotency_key="restore-select",
            trace_id="restore-select",
        )
        await service.select(
            actor,
            artifact_id=bundle.key.artifact_id,
            candidate_id=None,
            expected_selection_id=selected.id,
            human_decision_id=verifier.selection(None, selected.id),
            reason="explicit undated",
            idempotency_key="restore-clear",
            trace_id="restore-clear",
        )
    store = CheckpointStore(publisher.store.objects)
    store.publish_run(
        tenant_id=bundle.key.tenant_id,
        knowledge_base_id=bundle.key.knowledge_base_id,
        artifact_id=bundle.key.artifact_id,
        artifact_key=bundle.key,
        run_id=uuid4(),
        files={
            name: b"{}"
            for name in ("result.json", "provenance.json", "graph.json", "metadata.json")
        },
        output_contract_version=2,
        pipeline=PipelineIdentity(
            name="controlled-restore-fixture", package_version="1", configuration_sha256="a" * 64
        ),
        document_date_selection_id=selected.id,
    )
    # Partial/unreferenced content is inventoried and reported, never promoted.
    store.objects.create_exclusive("bundles/partial-fixture/source.pdf", b"partial")
    with Session(publisher.queue.engine) as session, session.begin():
        assertion = Assertion(
            id=uuid4(),
            run_id=None,
            origin="HUMAN_REVIEW",
            subject_type="Document",
            slot_type="document_date",
            value={"value": "2024-02-29"},
            interpretation_basis="EXPLICIT",
            tenant_id=bundle.key.tenant_id,
            knowledge_base_id=bundle.key.knowledge_base_id,
        )
        session.add(assertion)
        session.flush()
        for block_id in ("#/texts/0", None):
            session.add(
                AssertionEvidence(
                    assertion_id=assertion.id,
                    artifact_id=bundle.key.artifact_id,
                    block_id=block_id,
                    page=1,
                    precision="span" if block_id else "page",
                    tenant_id=bundle.key.tenant_id,
                    knowledge_base_id=bundle.key.knowledge_base_id,
                )
            )
    before = _snapshot(database, tmp_path)
    assert len(before["verified_artifacts"]) == 1 and len(before["verified_runs"]) == 1
    assert "bundles/partial-fixture/source.pdf" in before["unreferenced_objects"]
    assert before["database"]["document_date_selection"]["rows"] == 2
    environment = os.environ | {
        "BRAIN_WRITERS_QUIESCED": "1",
        "BRAIN_OPS_PYTHON": sys.executable,
        "BRAIN_OPS_DATABASE_URL": database,
        "BRAIN_POSTGRES_DATABASE": database.rsplit("/", 1)[1],
        "BRAIN_CONTENT_ROOT": str(tmp_path),
        "BRAIN_BACKUP_ROOT": str(tmp_path.parent / (tmp_path.name + "-backups")),
    }
    # These tests run on the operator host with its existing Docker connection.
    backup = subprocess.run(
        ["bash", str(PRODUCT / "scripts/ops/backup.sh")],
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert backup.returncode == 0, backup.stdout + backup.stderr
    destination = Path(backup.stdout.split("Backup complete: ")[1].strip())
    restored = subprocess.run(
        ["bash", str(PRODUCT / "scripts/ops/restore.sh"), str(destination)],
        env=environment,
        text=True,
        capture_output=True,
        timeout=100,
    )
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert "Restore drill PASSED" in restored.stdout
    assert "Citations checked: 2; resolved: 2; failed: 0" in restored.stdout
    assert json.loads((destination / "content-inventory.json").read_bytes()) == before
    print(backup.stdout + restored.stdout)
    # The source is unchanged by restore; restore never writes operator history.
    assert _snapshot(database, tmp_path) == before


async def test_restore_verifier_rejects_missing_bytes_and_index_loss(
    date_services, database, tmp_path
):
    _, _, _, bundle, publisher = date_services
    raw = bundle.files["blocks.jsonl"]
    block_path = tmp_path / bundle.key.prefix / "blocks.jsonl"
    block_path.unlink()
    with pytest.raises(ArtifactIntegrityError):
        _snapshot(database, tmp_path)
    block_path.write_bytes(raw)
    with Session(publisher.queue.engine) as session, session.begin():
        session.execute(text("TRUNCATE content_block CASCADE"))
    with pytest.raises(ArtifactIntegrityError, match="inventory"):
        _snapshot(database, tmp_path)


def test_backup_inventory_rejects_missing_required_files(tmp_path):
    # A missing contract/dependency file fails before creating a restore target.
    with pytest.raises(ValueError, match="required"):
        _backup["inventory"](tmp_path)
