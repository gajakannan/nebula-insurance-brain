from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_content.dates import (
    ContentDateBasis,
    DateBasisInvalid,
    DocumentDateCandidate,
    DocumentDateValue,
    HumanBasisUnavailable,
    HumanDateInput,
    SourceMetadataDateBasis,
    UnavailableHumanDateVerifier,
    UnavailableSourceMetadataVerifier,
    metadata_snapshot_hash,
    verify_content_date_basis,
)
from brain_content.validation import sha256, verify_bundle
from pydantic import ValidationError

from .test_versioned_content import bundle_fixture, seal


@pytest.mark.parametrize(
    "precision,value",
    [
        ("YEAR", "2024"),
        ("MONTH", "2024-02"),
        ("DAY", "2024-02-29"),
        ("YEAR", "0001"),
    ],
)
def test_calendar_precision_is_preserved(precision, value):
    date = DocumentDateValue(precision=precision, value=value)
    assert date.value == value and date.precision == precision


@pytest.mark.parametrize(
    "precision,value",
    [
        ("YEAR", "0000"),
        ("YEAR", "2024-01-01"),
        ("YEAR", 2024),
        ("MONTH", "2024-00"),
        ("MONTH", "2024-13"),
        ("MONTH", "0000-01"),
        ("DAY", "2023-02-29"),
        ("DAY", "2024-04-31"),
        ("DAY", "2024-1-01"),
    ],
)
def test_invalid_or_invented_precision_is_rejected(precision, value):
    with pytest.raises((ValueError, ValidationError)):
        DocumentDateValue(precision=precision, value=value)


def test_human_and_source_authority_are_unavailable_by_default():
    verifier = UnavailableHumanDateVerifier()
    with pytest.raises(HumanBasisUnavailable):
        verifier.verify(uuid4(), document_version_id=uuid4(), date_value="2024", precision="YEAR")
    for candidate in (None, uuid4()):
        with pytest.raises(HumanBasisUnavailable):
            verifier.verify_selection(
                uuid4(),
                document_version_id=uuid4(),
                candidate_id=candidate,
                expected_selection_id=None,
            )
    with pytest.raises(DateBasisInvalid):
        UnavailableSourceMetadataVerifier().verify(
            document_version_id=uuid4(),
            system="source",
            record_id="1",
            field="document_date",
            date=DocumentDateValue(precision="YEAR", value="2024"),
        )
    with pytest.raises(ValidationError):
        HumanDateInput(kind="HUMAN", decision_id=uuid4(), receipt_sha256="a" * 64)


@pytest.mark.parametrize("field", ["uploaded_at", "receiptTime", "extraction_date", "received_at"])
def test_processing_timestamp_is_never_a_document_date(field):
    with pytest.raises(ValidationError):
        SourceMetadataDateBasis(
            kind="SOURCE_METADATA",
            system="trusted",
            record_id="1",
            field=field,
            source_value="2024",
            snapshot_sha256=metadata_snapshot_hash("trusted", "1", field, "2024"),
        )


def test_source_snapshot_digest_is_exact_and_detects_tampering():
    basis = SourceMetadataDateBasis(
        kind="SOURCE_METADATA",
        system="trusted",
        record_id="1",
        field="document_date",
        source_value="2024-02",
        snapshot_sha256=metadata_snapshot_hash("trusted", "1", "document_date", "2024-02"),
    )
    with pytest.raises(ValidationError):
        SourceMetadataDateBasis.model_validate({**basis.model_dump(), "source_value": "2025-02"})


def test_content_basis_binds_unicode_quote_exact_line_ordinal_and_hash():
    key, raw, files = seal(*bundle_fixture())
    bundle = verify_bundle(key, raw, files)
    basis = ContentDateBasis(
        kind="CONTENT",
        artifact_id=key.artifact_id,
        block_id="#/texts/0",
        record_ordinal=0,
        record_sha256=sha256(files["blocks.jsonl"].splitlines()[0]),
        quote="😀B",
    )
    verify_content_date_basis(bundle, basis)
    for changed in (
        {"artifact_id": uuid4()},
        {"record_ordinal": 1},
        {"block_id": "other"},
        {"record_sha256": "b" * 64},
        {"quote": "A B"},
    ):
        with pytest.raises(DateBasisInvalid):
            verify_content_date_basis(
                bundle, ContentDateBasis.model_validate({**basis.model_dump(), **changed})
            )
    candidate = DocumentDateCandidate(
        contract_version=1,
        record_type="candidate",
        id=uuid4(),
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        document_version_id=bundle.manifest.version_id,
        created_at=datetime.now(UTC),
        actor_principal_id=uuid4(),
        authorization_decision_id=uuid4(),
        authorization_audit_event_id=uuid4(),
        idempotency_key="unicode",
        supersedes_id=None,
        date=DocumentDateValue(precision="YEAR", value="2024"),
        basis=basis,
    )
    assert DocumentDateCandidate.model_validate_json(candidate.model_dump_json()) == candidate
