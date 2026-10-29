"""F0004 PostgreSQL 18 expansion/retention proofs in owned throwaway databases."""

from __future__ import annotations

import asyncio
import json
import os
import runpy
import threading
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from brain_content.config import LocalObjectStoreConfig
from brain_content.dates import (
    ContentDateBasis,
    DateBasisInvalid,
    DateSelectionStale,
    DocumentDateValue,
    HumanBasisUnavailable,
    HumanDateInput,
    IdempotencyConflict,
    SourceMetadataDateBasis,
    SourceMetadataDateInput,
    VerifiedHumanDateBasis,
    VerifiedHumanSelectionBasis,
    metadata_snapshot_hash,
)
from brain_content.identities import fallback_key, new_source_identity
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_content.validation import ArtifactIntegrityError, sha256, verify_bundle
from brain_content.verified_store import VerifiedBundleStore
from brain_domain.authx import NO_FILTER, OperationOutcome, ResourceKey, ResourceType
from brain_domain.principal import PrincipalKind
from brain_jobs.queue import DocumentJobQueue, LeaseLost
from brain_persistence import content_models
from brain_persistence.authx import SqlAlchemyAuthorityStore, SyncAuthorityStore, principal_from_row
from brain_persistence.content_operations import ContentIntegrityOperations
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.document_dates import DocumentDateService
from brain_persistence.models import (
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    PrincipalRow,
    SourceDocument,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationExecution, decide
from brain_testing import fixtures
from psycopg import sql
from sqlalchemy import create_engine, event, inspect, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from brain_worker.content_publication import AuthorizedContentPublisher
from brain_worker.document_delivery import _register_artifact

PRODUCT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _clean_fact_tables():
    # Each test owns a fresh database. Override the parent module's cleanup;
    # these migration tests must never truncate the shared development stack.
    yield


@pytest.fixture
def database(monkeypatch):
    admin_url = os.environ.get("BRAIN_MIGRATION_ADMIN_URL")
    if not admin_url:
        pytest.skip("Set BRAIN_MIGRATION_ADMIN_URL for owned PostgreSQL migration/restore tests")
    name = f"f0004_8a6cc79f_migration_{uuid4().hex[:12]}"
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    url = admin_url.rsplit("/", 1)[0] + "/" + name
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    monkeypatch.setenv("BRAIN_DATABASE_URL", url.replace("postgresql://", "postgresql+psycopg://"))
    try:
        yield url
    finally:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )


def configuration():
    path = PRODUCT / "engine/migrations/alembic.ini"
    config = Config(str(path))
    config.set_main_option("script_location", str(path.parent))
    return config


def legacy_row(url):
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    tenant, kb, document, version, artifact = (uuid4() for _ in range(5))
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, tenant, kb)
        principal = fixtures.seed_principal(
            session, issuer="urn:f0004:synthetic", subject=str(uuid4())
        )
        session.add(
            SourceDocument(
                id=document, tenant_id=tenant, knowledge_base_id=kb, source_sha256="a" * 64
            )
        )
        session.flush()
        session.add(
            DocumentVersion(
                id=version, source_document_id=document, tenant_id=tenant, knowledge_base_id=kb
            )
        )
        session.flush()
        actor = principal.id
    engine.dispose()
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO content_artifact (id,document_version_id,artifact_sha256,page_count,"
            "extraction_status,tenant_id,knowledge_base_id) VALUES (%s,%s,%s,1,'complete',%s,%s)",
            (artifact, version, "b" * 64, tenant, kb),
        )
    return tenant, kb, artifact, actor


def test_expand_and_safe_empty_downgrade_preserve_existing_owner_constraints(database):
    config = configuration()
    command.upgrade(config, "0007")
    command.upgrade(config, "0008")
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0008"
        assert connection.execute("SELECT count(*) FROM document_date_candidate").fetchone()[0] == 0
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    uniques = inspect(engine).get_unique_constraints("content_artifact", schema="public")
    assert any(c["column_names"] == ["document_version_id"] for c in uniques)
    engine.dispose()
    command.downgrade(config, "0007")
    command.upgrade(config, "0008")


def test_expansion_keeps_legacy_identity_and_rejects_unwitnessed_state_change(database):
    config = configuration()
    command.upgrade(config, "0007")
    tenant, kb, artifact, actor = legacy_row(database)
    with psycopg.connect(database) as connection:
        before = connection.execute(
            "SELECT * FROM content_artifact WHERE id=%s", (artifact,)
        ).fetchone()
    command.upgrade(config, "0008")
    with psycopg.connect(database, autocommit=True) as connection:
        after = connection.execute(
            "SELECT * FROM content_artifact WHERE id=%s", (artifact,)
        ).fetchone()
        assert after[: len(before)] == before
        assert connection.execute(
            "SELECT artifact_contract_version,manifest_sha256,publication_state "
            "FROM content_artifact "
            "WHERE id=%s",
            (artifact,),
        ).fetchone() == (None, None, "legacy_unverified")
        with (
            pytest.raises(psycopg.Error, match="same-transaction state event"),
            connection.transaction(),
        ):
            connection.execute(
                "UPDATE content_artifact SET publication_state='ready' WHERE id=%s", (artifact,)
            )
        with pytest.raises(psycopg.Error, match="immutable"), connection.transaction():
            connection.execute(
                "UPDATE content_artifact SET artifact_sha256=%s WHERE id=%s",
                ("c" * 64, artifact),
            )
        with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
            connection.execute(
                "INSERT INTO content_block (artifact_id,block_id,tenant_id,knowledge_base_id,"
                "native_ref,reading_order,section_path,text_origin,producer,origin_anchor,"
                "record_ordinal,record_sha256,created_by) VALUES "
                "(%s,'b',%s,%s,'#/texts/0',0,'[]','STATED','{}','{}',0,%s,%s)",
                (artifact, tenant, uuid4(), "a" * 64, actor),
            )


def test_index_history_is_append_only_and_blocks_destructive_downgrade(database):
    config = configuration()
    command.upgrade(config, "0007")
    tenant, kb, artifact, actor = legacy_row(database)
    command.upgrade(config, "0008")
    with psycopg.connect(database, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO content_block "
            "(artifact_id,block_id,tenant_id,knowledge_base_id,native_ref,"
            "reading_order,section_path,text_origin,producer,origin_anchor,record_ordinal,"
            "record_sha256,created_by) VALUES "
            "(%s,'b',%s,%s,'#/texts/0',0,'[]','STATED','{}','{}',0,%s,%s)",
            (artifact, tenant, kb, "a" * 64, actor),
        )
        with pytest.raises(psycopg.Error, match="append-only"), connection.transaction():
            connection.execute("UPDATE content_block SET reading_order=1")
    with pytest.raises(RuntimeError, match="forward repair"):
        command.downgrade(config, "0007")
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM content_block").fetchone()[0] == 1
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0008"


def test_reader_metadata_adapter_supports_legacy_schema_before_expansion(database):
    command.upgrade(configuration(), "0007")
    tenant, kb, artifact, _ = legacy_row(database)
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    with Session(engine) as session:
        repository = ContentArtifactRepository(session)
        assert not repository.expanded()
        metadata = repository.get_metadata(artifact)
        assert (metadata.key.tenant_id, metadata.key.knowledge_base_id) == (tenant, kb)
        assert metadata.key.contract_version == 1
        assert metadata.publication_state == "legacy_unverified"
        assert metadata.manifest_sha256 is None
    engine.dispose()


def test_ready_registration_indexes_and_audit_commit_once_and_detect_incomplete_restore(database):
    command.upgrade(configuration(), "0008")
    helpers = runpy.run_path(
        str(PRODUCT / "engine/packages/brain-content/tests/test_versioned_content.py")
    )
    key, raw, files = helpers["seal"](*helpers["bundle_fixture"]())
    bundle = verify_bundle(key, raw, files)
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    model = PRODUCT / "planning-mds/security/policies/model.conf"
    policy = PRODUCT / "planning-mds/security/policies/policy.csv"
    evaluator = CasbinAuthorizationAdapter(model, policy)
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, key.tenant_id, key.knowledge_base_id)
        principal = fixtures.seed_principal(
            session, issuer="urn:f0004:synthetic", subject=str(uuid4()), kind=PrincipalKind.SERVICE
        )
        fixtures.seed_grant(
            session, principal.id, key.tenant_id, key.knowledge_base_id, "ServicePrincipal"
        )
        fixtures.activate_policy(session, model, policy)
        resource = ResourceKey(ResourceType.CONTENT_ARTIFACT, key.artifact_id)
        fixtures.protect(
            session, resource, key.tenant_id, key.knowledge_base_id, before_record=True
        )
        store = SyncAuthorityStore(session)
        (evaluated,) = decide(
            store,
            evaluator,
            evaluator.release,
            authenticated_id=principal.id,
            keys=[resource],
            action="ingest",
            requested=NO_FILTER,
            trace_id="f0004-register",
            delegation_id=None,
            clock=lambda: datetime.now(UTC),
            new_id=uuid4,
            require_record=False,
        )
        assert evaluated.decision.allowed
        decision = evaluated.decision.with_outcome(OperationOutcome.SUCCEEDED)
        store.append_decision(decision)
        repository = ContentArtifactRepository(session)
        for _ in range(2):
            repository.register_ready(
                bundle,
                actor_id=decision.actor_principal_id,
                authorization_decision_id=decision.decision_id,
                supersedes_artifact_id=None,
            )
        repository.get_metadata(key.artifact_id).verify_identity(bundle)
        repository.verify_indexes(bundle)
        audit = repository.authorization_audit(
            decision.decision_id, decision.actor_principal_id, key
        )
        assert audit.id != decision.decision_id
        events = (
            session.execute(
                select(AuditEventRow).where(
                    AuditEventRow.resource_id == key.artifact_id,
                    AuditEventRow.event_type == "content_artifact_published",
                )
            )
            .scalars()
            .all()
        )
        assert len(events) == 1
    with Session(engine) as session, session.begin():
        session.execute(text("TRUNCATE content_block CASCADE"))
    with Session(engine) as session, pytest.raises(ArtifactIntegrityError, match="inventory"):
        ContentArtifactRepository(session).verify_indexes(bundle)
    engine.dispose()


@pytest.fixture
def publication(database, tmp_path, request):
    command.upgrade(configuration(), "head")
    helpers = runpy.run_path(
        str(PRODUCT / "engine/packages/brain-content/tests/test_versioned_content.py")
    )
    manifest, files = helpers["bundle_fixture"]()
    text_value = (
        "Effective 2026-06-01; issued 2026-06-10; received 2026-06-12; accepted 2026-06-14 😀"
        if getattr(request, "param", None) == "june"
        else "Issued 2024-02-29 😀"
    )
    native = json.loads(files["docling-document.json"])
    native["texts"][0]["text"] = text_value
    block = json.loads(files["blocks.jsonl"])
    block["text"] = text_value
    block["origin_anchor"]["regions"][0]["char_end"] = len(text_value)
    files["docling-document.json"] = json.dumps(native).encode()
    files["blocks.jsonl"] = json.dumps(block).encode() + b"\n"
    files["normalized.md"] = text_value.encode()
    mode = getattr(request, "param", 2)
    if mode == "tables":
        records = []
        native["tables"] = []
        for number in range(2):
            cell = {
                "cell_id": f"cell-{number}",
                "row_start": 0,
                "col_start": 0,
                "row_span": 2,
                "col_span": 1,
                "text": text_value,
                "block_ids": ["#/texts/0"],
            }
            records.append(
                {
                    "record_type": "table",
                    "contract_version": 2,
                    "table_id": f"t{number}",
                    "native_ref": f"#/tables/{number}",
                    "num_rows": 2,
                    "num_cols": 1,
                    "header_rows": [0],
                    "continuation_of": "t0" if number else None,
                    "cells": [cell],
                }
            )
            native["tables"].append(
                {
                    "data": {
                        "num_rows": 2,
                        "num_cols": 1,
                        "table_cells": [
                            {
                                "text": text_value,
                                "start_row_offset_idx": 0,
                                "end_row_offset_idx": 2,
                                "start_col_offset_idx": 0,
                                "end_col_offset_idx": 1,
                            }
                        ],
                    }
                }
            )
        # Persist continuation before predecessor in file order; the repository
        # must insert by dependency while retaining each original ordinal/hash.
        files["tables.jsonl"] = b"".join(
            json.dumps(row).encode() + b"\n" for row in reversed(records)
        )
        files["docling-document.json"] = json.dumps(native).encode()
    fenced_artifact_id = UUID(manifest["artifact_id"])
    if mode == "fallback":
        identity = new_source_identity(
            tenant_id=UUID(manifest["tenant_id"]),
            knowledge_base_id=UUID(manifest["knowledge_base_id"]),
            document_id=UUID(manifest["document_id"]),
            source_sha256=manifest["source_sha256"],
            recipe_sha256=manifest["recipe_sha256"],
            contract_version=2,
        )
        manifest["version_id"] = str(identity.version_id)
        manifest["artifact_id"] = str(
            fallback_key(
                identity.version_id, identity.key.tenant_id, identity.key.knowledge_base_id
            ).artifact_id
        )
        manifest["execution"]["configuration_hash"] = manifest["recipe_sha256"]
        fenced_artifact_id = identity.key.artifact_id
        files["blocks.jsonl"] = (
            json.dumps({"block_id": "text-0", "text": text_value}).encode() + b"\n"
        )
        files["layout.jsonl"] = b'{"page":1,"width":612,"height":792}\n'
    if mode in (1, "fallback"):
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
    key, raw, files = helpers["seal"](manifest, files)
    bundle = verify_bundle(key, raw, files)
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    model = PRODUCT / "planning-mds/security/policies/model.conf"
    policy = PRODUCT / "planning-mds/security/policies/policy.csv"
    now = datetime.now(UTC)
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, key.tenant_id, key.knowledge_base_id)
        principal = fixtures.seed_principal(
            session, issuer="urn:f0004:synthetic", subject=str(uuid4()), kind=PrincipalKind.SERVICE
        )
        fixtures.seed_grant(
            session,
            principal.id,
            key.tenant_id,
            key.knowledge_base_id,
            "ServicePrincipal",
            expires_at=now + timedelta(minutes=1),
        )
        fixtures.activate_policy(session, model, policy)
        fixtures.protect(
            session,
            ResourceKey(ResourceType.CONTENT_ARTIFACT, key.artifact_id),
            key.tenant_id,
            key.knowledge_base_id,
            before_record=True,
        )
        if fenced_artifact_id != key.artifact_id:
            fixtures.protect(
                session,
                ResourceKey(ResourceType.CONTENT_ARTIFACT, fenced_artifact_id),
                key.tenant_id,
                key.knowledge_base_id,
                before_record=True,
            )
    queue_clock, auth_clock = [100.0], [now]
    queue = DocumentJobQueue(engine, lease_seconds=10, clock=lambda: queue_clock[0])
    queue.enqueue(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=fenced_artifact_id,
        request_key="synthetic-publication",
        payload={
            "content_contract_version": 2 if mode == "fallback" else key.contract_version,
            "actor_id": str(principal.id),
            "correlation_id": str(uuid4()),
            "document_id": str(bundle.manifest.document_id),
            "version_id": str(bundle.manifest.version_id),
            "source_sha256": bundle.manifest.source_sha256,
            "recipe_sha256": getattr(
                bundle.manifest, "recipe_sha256", bundle.manifest.execution.configuration_hash
            ),
        },
    )
    objects = LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    store = VerifiedBundleStore(objects)
    publisher = AuthorizedContentPublisher(
        queue,
        store,
        CasbinAuthorizationAdapter(model, policy),
        clock=lambda: auth_clock[0],
        objects=objects,
    )
    try:
        yield publisher, queue.claim(), bundle, queue_clock, auth_clock
    finally:
        engine.dispose()


def publication_events(publisher, artifact_id):
    with Session(publisher.queue.engine) as session:
        return session.scalars(
            select(AuditEventRow).where(
                AuditEventRow.resource_id == artifact_id,
                AuditEventRow.event_type.in_(
                    ["authorization_decision", "content_artifact_published"]
                ),
            )
        ).all()


@pytest.mark.parametrize("fault", ["registration", "commit"])
def test_orphan_marker_is_adopted_with_exact_bytes_after_database_failure(
    publication, monkeypatch, fault
):
    publisher, lease, bundle, _, _ = publication
    original = ContentArtifactRepository.register_ready

    def fail_registration(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError("synthetic registration interruption")

    def fail_commit(connection):
        raise RuntimeError("synthetic commit interruption")

    if fault == "registration":
        monkeypatch.setattr(ContentArtifactRepository, "register_ready", fail_registration)
    else:
        event.listen(publisher.queue.engine, "commit", fail_commit, once=True)
    with pytest.raises(RuntimeError, match="synthetic"):
        publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        assert (
            ContentArtifactRepository(session).find_source(
                bundle.key.tenant_id, bundle.key.knowledge_base_id, bundle.manifest.source_sha256
            )
            is None
        )
    audits = publication_events(publisher, bundle.key.artifact_id)
    assert len(audits) == 1
    assert audits[0].event_type == "authorization_decision"
    assert audits[0].operation_outcome == "failed"
    monkeypatch.setattr(ContentArtifactRepository, "register_ready", original)
    # No converter is involved: a reopened publisher adopts the retained marker.
    for _ in range(2):
        retained = publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
        assert retained.manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        repository = ContentArtifactRepository(session)
        repository.get_metadata(bundle.key.artifact_id).verify_identity(retained)
        repository.verify_indexes(retained)
    assert (
        len(
            [
                row
                for row in publication_events(publisher, bundle.key.artifact_id)
                if row.event_type == "content_artifact_published"
            ]
        )
        == 1
    )


@pytest.mark.parametrize("expiry", ["authority", "lease"])
def test_expiry_after_marker_rolls_back_readiness_and_success_audit(
    publication, monkeypatch, expiry
):
    publisher, lease, bundle, queue_clock, auth_clock = publication
    original = publisher.store.publish

    def publish_then_expire(*args):
        retained = original(*args)
        if expiry == "authority":
            auth_clock[0] += timedelta(minutes=2)
        else:
            queue_clock[0] += 11
        return retained

    monkeypatch.setattr(publisher.store, "publish", publish_then_expire)
    with pytest.raises(AuthorizationDenied if expiry == "authority" else LeaseLost):
        publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        assert (
            ContentArtifactRepository(session).find_source(
                bundle.key.tenant_id, bundle.key.knowledge_base_id, bundle.manifest.source_sha256
            )
            is None
        )
    audits = publication_events(publisher, bundle.key.artifact_id)
    assert len(audits) == 1
    assert audits[0].event_type == "authorization_decision"
    assert audits[0].operation_outcome != "succeeded"
    assert audits[0].decision is (expiry != "authority")


def test_current_denial_prevents_all_object_writes(publication):
    publisher, lease, bundle, _, auth_clock = publication
    auth_clock[0] += timedelta(minutes=2)
    with pytest.raises(AuthorizationDenied):
        publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    assert not publisher.store.objects.list_keys(bundle.key.prefix)
    audits = publication_events(publisher, bundle.key.artifact_id)
    assert len(audits) == 1 and not audits[0].decision


@pytest.fixture
async def date_services(publication):
    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    with Session(publisher.queue.engine) as session, session.begin():
        principal = principal_from_row(session.get(PrincipalRow, lease.payload["actor_id"]))
        human = fixtures.seed_principal(
            session, issuer="urn:f0004:human-fixture", subject=str(uuid4())
        )
    engine = create_async_engine(publisher.queue.engine.url.set(drivername="postgresql+asyncpg"))
    policy = publisher.policy
    content = LocalContentArtifactStore(publisher.store.objects)

    @asynccontextmanager
    async def service(**verifiers):
        async with AsyncSession(engine, expire_on_commit=False) as session:
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), policy, policy.release
            )
            yield DocumentDateService(session, execution, content, **verifiers)

    try:
        yield service, principal, human, bundle, publisher
    finally:
        await engine.dispose()


class ControlledHumanVerifier:
    """Contract fixture only: explicit trusted decisions, no production authority."""

    def __init__(self, human, version_id):
        self.human, self.version_id = human, version_id
        self.dates, self.selections = {}, {}
        self.revoked = False

    def verify(self, decision_id, **command):
        if self.revoked or decision_id not in self.dates:
            raise HumanBasisUnavailable("controlled receipt is unavailable")
        return self.dates[decision_id]

    def verify_selection(self, decision_id, **command):
        if self.revoked or decision_id not in self.selections:
            raise HumanBasisUnavailable("controlled selection receipt is unavailable")
        return self.selections[decision_id]

    def receipt(self):
        return dict(
            decision_id=uuid4(),
            document_version_id=self.version_id,
            actor_principal_id=self.human.id,
            authorization_decision_id=uuid4(),
            decided_at=datetime.now(UTC) - timedelta(seconds=1),
            receipt_sha256="c" * 64,
        )

    def date(self, value="2024-02-29"):
        receipt = VerifiedHumanDateBasis(**self.receipt(), date_value=value, precision="DAY")
        self.dates[receipt.decision_id] = receipt
        return HumanDateInput(kind="HUMAN", decision_id=receipt.decision_id)

    def selection(self, candidate_id, previous=None):
        receipt = VerifiedHumanSelectionBasis(
            **self.receipt(), candidate_id=candidate_id, expected_selection_id=previous
        )
        self.selections[receipt.decision_id] = receipt
        return receipt.decision_id


class ControlledMetadataVerifier:
    def __init__(self, version_id):
        self.version_id = version_id

    def verify(self, *, document_version_id, system, record_id, field, date):
        assert document_version_id == self.version_id
        assert (system, record_id, field) == ("synthetic-source", "document-1", "document_date")
        return SourceMetadataDateBasis(
            kind="SOURCE_METADATA",
            system=system,
            record_id=record_id,
            field=field,
            source_value=date.value,
            snapshot_sha256=metadata_snapshot_hash(system, record_id, field, date.value),
        )


def content_basis(bundle):
    return ContentDateBasis(
        kind="CONTENT",
        artifact_id=bundle.key.artifact_id,
        block_id="#/texts/0",
        record_ordinal=0,
        record_sha256=sha256(bundle.files["blocks.jsonl"].splitlines()[0]),
        quote="2024-02-29",
    )


async def test_date_candidates_round_trip_all_bases_without_selecting_and_keep_audit_identity(
    date_services,
):
    services, actor, human, bundle, publisher = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)
    source = ControlledMetadataVerifier(bundle.manifest.version_id)
    candidates = []
    inputs = [
        (DocumentDateValue(precision="YEAR", value="2024"), content_basis(bundle)),
        (
            DocumentDateValue(precision="MONTH", value="2025-03"),
            SourceMetadataDateInput(
                kind="SOURCE_METADATA",
                system="synthetic-source",
                record_id="document-1",
                field="document_date",
            ),
        ),
        (DocumentDateValue(precision="DAY", value="2024-02-29"), verifier.date()),
    ]
    async with services(human_dates=verifier, source_metadata=source) as service:
        for index, (date, basis) in enumerate(inputs):
            candidate = await service.append_candidate(
                actor,
                artifact_id=bundle.key.artifact_id,
                date=date,
                basis=basis,
                supersedes_id=candidates[-1].id if candidates else None,
                idempotency_key=f"candidate-{index}",
                trace_id="date-contract",
            )
            assert candidate.authorization_decision_id != candidate.authorization_audit_event_id
            candidates.append(candidate)
        view = await service.read(
            actor, artifact_id=bundle.key.artifact_id, selection_id=None, trace_id="date-read"
        )
    assert view.selection is None and view.selected_date is None
    assert set(row.id for row in view.candidates) == set(row.id for row in candidates)
    assert [row.date.precision for row in candidates] == ["YEAR", "MONTH", "DAY"]
    assert candidates[2].basis.actor_principal_id == human.id
    assert candidates[2].actor_principal_id == actor.id
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        assert (
            len(
                session.scalars(
                    select(AuditEventRow).where(
                        AuditEventRow.event_type == "document_date_candidate_recorded"
                    )
                ).all()
            )
            == 3
        )


async def test_default_human_verifiers_deny_candidates_selections_and_clears(date_services):
    services, actor, _, bundle, publisher = date_services
    async with services() as service:
        with pytest.raises(HumanBasisUnavailable):
            await service.append_candidate(
                actor,
                artifact_id=bundle.key.artifact_id,
                date=DocumentDateValue(precision="YEAR", value="2024"),
                basis=HumanDateInput(kind="HUMAN", decision_id=uuid4()),
                supersedes_id=None,
                idempotency_key="denied-human",
                trace_id="denied-human",
            )
        for candidate_id in (None, uuid4()):
            with pytest.raises(HumanBasisUnavailable):
                await service.select(
                    actor,
                    artifact_id=bundle.key.artifact_id,
                    candidate_id=candidate_id,
                    expected_selection_id=None,
                    human_decision_id=uuid4(),
                    reason="explicit",
                    idempotency_key=str(uuid4()),
                    trace_id="denied-selection",
                )
    with Session(publisher.queue.engine) as session:
        assert session.execute(select(content_models.document_date_candidate)).first() is None
        assert session.execute(select(content_models.document_date_selection)).first() is None
        audits = session.scalars(
            select(AuditEventRow).where(
                AuditEventRow.trace_id.in_(["denied-human", "denied-selection"])
            )
        ).all()
        assert len(audits) == 3
        assert all(
            row.event_type == "authorization_decision" and row.operation_outcome == "failed"
            for row in audits
        )


async def test_date_idempotency_stale_selection_clear_and_pinned_history(date_services):
    services, actor, human, bundle, publisher = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)
    command = dict(
        artifact_id=bundle.key.artifact_id,
        date=DocumentDateValue(precision="YEAR", value="2024"),
        basis=content_basis(bundle),
        supersedes_id=None,
        idempotency_key="candidate",
        trace_id="date-idempotency",
    )
    async with services(human_selections=verifier) as service:
        candidate = await service.append_candidate(actor, **command)
        assert await service.append_candidate(actor, **command) == candidate
        with pytest.raises(IdempotencyConflict):
            await service.append_candidate(
                actor, **{**command, "date": DocumentDateValue(precision="YEAR", value="2025")}
            )
        select = dict(
            artifact_id=bundle.key.artifact_id,
            candidate_id=candidate.id,
            expected_selection_id=None,
            human_decision_id=verifier.selection(candidate.id),
            reason="reviewed source date",
            idempotency_key="select",
            trace_id="date-selection",
        )
        selected = await service.select(actor, **select)
        assert await service.select(actor, **select) == selected
        assert selected.human_decision.actor_principal_id == human.id
        assert selected.actor_principal_id == actor.id
        with pytest.raises(DateSelectionStale):
            await service.select(actor, **{**select, "idempotency_key": "stale"})
        clear = await service.select(
            actor,
            artifact_id=bundle.key.artifact_id,
            candidate_id=None,
            expected_selection_id=selected.id,
            human_decision_id=verifier.selection(None, selected.id),
            reason="explicitly undated",
            idempotency_key="clear",
            trace_id="date-clear",
        )
        assert clear.sequence == 2 and clear.previous_selection_id == selected.id
        view = await service.read(
            actor, artifact_id=bundle.key.artifact_id, selection_id=None, trace_id="current-date"
        )
        assert view.selected_date is None and view.selection.id == clear.id
        pinned = await service.read(
            actor,
            artifact_id=bundle.key.artifact_id,
            selection_id=selected.id,
            trace_id="pinned-date",
        )
        assert pinned.selected_date == command["date"]
        assert pinned.selection.id == selected.id
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes


async def test_date_read_keeps_selected_candidate_consistent_during_concurrent_write(
    date_services, monkeypatch
):
    services, actor, human, bundle, publisher = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)
    artifact_id = bundle.key.artifact_id
    async with services(human_selections=verifier) as service:
        first = await service.append_candidate(
            actor,
            artifact_id=artifact_id,
            date=DocumentDateValue(precision="DAY", value="2024-02-29"),
            basis=content_basis(bundle),
            supersedes_id=None,
            idempotency_key="race-first",
            trace_id="race-first",
        )
        initial = await service.select(
            actor,
            artifact_id=artifact_id,
            candidate_id=first.id,
            expected_selection_id=None,
            human_decision_id=verifier.selection(first.id),
            reason="initial selection",
            idempotency_key="race-select-first",
            trace_id="race-first",
        )
    application_name = "f0004-date-writer-" + uuid4().hex
    written, errors = {}, []
    triggered = False
    thread = None

    async def write_next():
        engine = create_async_engine(
            publisher.queue.engine.url.set(drivername="postgresql+asyncpg"),
            connect_args={"server_settings": {"application_name": application_name}},
        )
        try:
            async with AsyncSession(engine, expire_on_commit=False) as session:
                service = DocumentDateService(
                    session,
                    AuthorizationExecution(
                        SqlAlchemyAuthorityStore(session),
                        publisher.policy,
                        publisher.policy.release,
                    ),
                    LocalContentArtifactStore(publisher.store.objects),
                    human_dates=verifier,
                    human_selections=verifier,
                )
                candidate = await service.append_candidate(
                    actor,
                    artifact_id=artifact_id,
                    date=DocumentDateValue(precision="DAY", value="2025-03-01"),
                    basis=verifier.date("2025-03-01"),
                    supersedes_id=first.id,
                    idempotency_key="race-next",
                    trace_id="race-next",
                )
                selected = await service.select(
                    actor,
                    artifact_id=artifact_id,
                    candidate_id=candidate.id,
                    expected_selection_id=initial.id,
                    human_decision_id=verifier.selection(candidate.id, initial.id),
                    reason="concurrent selection",
                    idempotency_key="race-select-next",
                    trace_id="race-next",
                )
                written.update(candidate=candidate, selection=selected)
        finally:
            await engine.dispose()

    def write_thread():
        try:
            asyncio.run(write_next())
        except BaseException as exc:
            errors.append(exc)

    original = Session.execute

    def interleave(session, statement, *args, **kwargs):
        nonlocal triggered, thread
        result = original(session, statement, *args, **kwargs)
        if (
            not triggered
            and session.info.get("date_race_reader")
            and content_models.document_date_candidate
            in getattr(statement, "get_final_froms", lambda: [])()
        ):
            triggered = True
            reader_pid = (
                session.connection().exec_driver_sql("SELECT pg_backend_pid()").scalar_one()
            )
            thread = threading.Thread(target=write_thread)
            thread.start()
            # Wait for observed PostgreSQL lock contention, not a timing guess.
            observer_url = publisher.queue.engine.url.set(drivername="postgresql").render_as_string(
                hide_password=False
            )
            with psycopg.connect(observer_url, autocommit=True) as observer:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    blocked = observer.execute(
                        "SELECT 1 FROM pg_stat_activity WHERE application_name = %s "
                        "AND %s = ANY(pg_blocking_pids(pid)) "
                        "AND query LIKE '%%document_version%%FOR UPDATE%%'",
                        (application_name, reader_pid),
                    ).fetchone()
                    if blocked:
                        break
                    assert not errors, errors
                    assert not written, "writer committed between candidate and selection reads"
                    threading.Event().wait(0.01)
                else:
                    pytest.fail("writer did not wait on reader's version lock")
        return result

    async with services() as service:
        service.session.sync_session.info["date_race_reader"] = True
        monkeypatch.setattr(Session, "execute", interleave)
        try:
            view = await service.read(
                actor, artifact_id=artifact_id, selection_id=None, trace_id="race-read"
            )
        finally:
            monkeypatch.setattr(Session, "execute", original)
    assert triggered and thread is not None
    await asyncio.to_thread(thread.join, 10)
    assert not thread.is_alive() and not errors
    assert view.selection.id == initial.id
    assert view.selected_date == first.date
    assert view.selection.candidate_id in {candidate.id for candidate in view.candidates}
    async with services() as service:
        later = await service.read(
            actor, artifact_id=artifact_id, selection_id=None, trace_id="race-later"
        )
    assert later.selection.id == written["selection"].id
    assert later.selected_date == written["candidate"].date
    assert later.selection.candidate_id in {candidate.id for candidate in later.candidates}


async def test_competing_date_selections_have_one_winner(date_services):
    services, actor, human, bundle, _ = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)

    async def choose():
        async with services(human_selections=verifier) as service:
            return await service.select(
                actor,
                artifact_id=bundle.key.artifact_id,
                candidate_id=None,
                expected_selection_id=None,
                human_decision_id=verifier.selection(None),
                reason="explicit clear",
                idempotency_key=str(uuid4()),
                trace_id="competing-date",
            )

    outcomes = await asyncio.gather(choose(), choose(), return_exceptions=True)
    assert sum(isinstance(outcome, DateSelectionStale) for outcome in outcomes) == 1
    assert sum(not isinstance(outcome, Exception) for outcome in outcomes) == 1


async def test_revoked_and_mismatched_human_receipts_cannot_select(date_services):
    services, actor, human, bundle, publisher = date_services
    verifier = ControlledHumanVerifier(human, bundle.manifest.version_id)
    async with services(human_dates=verifier, human_selections=verifier) as service:
        candidate = await service.append_candidate(
            actor,
            artifact_id=bundle.key.artifact_id,
            date=DocumentDateValue(precision="DAY", value="2024-02-29"),
            basis=verifier.date(),
            supersedes_id=None,
            idempotency_key="human-candidate",
            trace_id="human-candidate",
        )
        wrong = verifier.selection(uuid4())
        with pytest.raises(DateBasisInvalid):
            await service.select(
                actor,
                artifact_id=bundle.key.artifact_id,
                candidate_id=candidate.id,
                expected_selection_id=None,
                human_decision_id=wrong,
                reason="tampered selection",
                idempotency_key="wrong-selection",
                trace_id="wrong-selection",
            )
        selection = verifier.selection(candidate.id)
        # Selection receipt remains trusted; the original candidate's human
        # authority is unavailable on revalidation.
        verifier.dates.clear()
        with pytest.raises(HumanBasisUnavailable):
            await service.select(
                actor,
                artifact_id=bundle.key.artifact_id,
                candidate_id=candidate.id,
                expected_selection_id=None,
                human_decision_id=selection,
                reason="revoked date basis",
                idempotency_key="revoked-selection",
                trace_id="revoked-selection",
            )
    with Session(publisher.queue.engine) as session:
        assert session.execute(select(content_models.document_date_selection)).first() is None


async def test_date_mutation_event_failure_rolls_back_candidate_and_success_audit(
    date_services, monkeypatch
):
    services, actor, _, bundle, publisher = date_services

    def fail_event(*_args, **_kwargs):
        raise RuntimeError("synthetic date event failure")

    monkeypatch.setattr(ContentArtifactRepository, "mutation_event", fail_event)
    async with services() as service:
        with pytest.raises(RuntimeError, match="synthetic"):
            await service.append_candidate(
                actor,
                artifact_id=bundle.key.artifact_id,
                date=DocumentDateValue(precision="YEAR", value="2024"),
                basis=content_basis(bundle),
                supersedes_id=None,
                idempotency_key="rollback-candidate",
                trace_id="date-rollback",
            )
    with Session(publisher.queue.engine) as session:
        assert session.execute(select(content_models.document_date_candidate)).first() is None
        audits = session.scalars(
            select(AuditEventRow).where(AuditEventRow.trace_id == "date-rollback")
        ).all()
        assert len(audits) == 1
        assert audits[0].event_type == "authorization_decision"
        assert audits[0].operation_outcome == "failed"


async def test_content_date_quote_and_source_metadata_without_trusted_adapter_fail(date_services):
    services, actor, _, bundle, _ = date_services
    async with services() as service:
        for basis in (
            content_basis(bundle).model_copy(update={"record_sha256": "b" * 64}),
            SourceMetadataDateInput(
                kind="SOURCE_METADATA", system="untrusted", record_id="1", field="document_date"
            ),
        ):
            with pytest.raises(DateBasisInvalid):
                await service.append_candidate(
                    actor,
                    artifact_id=bundle.key.artifact_id,
                    date=DocumentDateValue(precision="YEAR", value="2024"),
                    basis=basis,
                    supersedes_id=None,
                    idempotency_key=str(uuid4()),
                    trace_id="invalid-basis",
                )


def operator_service(publication):
    publisher, lease, bundle, _, clock = publication
    return ContentIntegrityOperations(
        publisher.queue.engine,
        publisher.store,
        publisher.policy,
        actor_id=UUID(lease.payload["actor_id"]),
        tenant_id=bundle.key.tenant_id,
        knowledge_base_id=bundle.key.knowledge_base_id,
        clock=lambda: clock[0],
    )


def test_operator_sweep_and_authorized_repair_preserve_original_content_and_history(publication):
    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    service = operator_service(publication)
    source = publisher.store.objects._root / bundle.key.prefix / "source.pdf"
    source.write_bytes(b"synthetic corruption")
    assert service.inspect_artifact(bundle.key.artifact_id) == "QUARANTINED"
    with Session(publisher.queue.engine) as session:
        assert (
            session.get(ContentArtifact, bundle.key.artifact_id).publication_state == "quarantined"
        )
        repair = session.execute(select(content_models.content_repair_record)).mappings().one()
        assert repair["kind"] == "INTEGRITY_FAILURE"
        states = (
            session.execute(select(content_models.content_artifact_state_event)).mappings().all()
        )
        assert len(states) == 1 and states[0]["trigger"] == "INTEGRITY_SWEEP"
        assert states[0]["repair_record_id"] == repair["id"]
        audit = session.get(AuditEventRow, states[0]["audit_event_id"])
        assert audit.event_type == "content_artifact_quarantined"
        assert audit.decision_id == states[0]["authorization_decision_id"]
    # Controlled restore of the exact original object, never conversion or overwrite by the service.
    source.write_bytes(bundle.files["source.pdf"])
    assert service.repair(bundle.key.artifact_id, repair_record_id=repair["id"]) == "READY"
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        repository = ContentArtifactRepository(session)
        repository.get_metadata(bundle.key.artifact_id).verify_identity(bundle)
        records = session.execute(select(content_models.content_repair_record)).mappings().all()
        assert len(records) == 2
        assert any(
            row["resolves_id"] == repair["id"] and row["resolution"] == "REPAIRED"
            for row in records
        )
        states = (
            session.execute(select(content_models.content_artifact_state_event)).mappings().all()
        )
        assert len(states) == 2 and states[1]["trigger"] == "AUTHORIZED_REPAIR"


def test_operator_failure_rolls_back_quarantine_repair_state_and_success_audit(
    publication, monkeypatch
):
    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    service = operator_service(publication)
    (publisher.store.objects._root / bundle.key.prefix / "source.pdf").write_bytes(b"corrupt")
    original = service._transition

    def fail_after_effects(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("synthetic operator interruption")

    monkeypatch.setattr(service, "_transition", fail_after_effects)
    before = len(publication_events(publisher, bundle.key.artifact_id))
    with pytest.raises(RuntimeError, match="synthetic"):
        service.inspect_artifact(bundle.key.artifact_id)
    with Session(publisher.queue.engine) as session:
        assert session.get(ContentArtifact, bundle.key.artifact_id).publication_state == "ready"
        for table in (
            content_models.content_repair_record,
            content_models.content_artifact_state_event,
        ):
            assert session.execute(select(table)).first() is None
    events = publication_events(publisher, bundle.key.artifact_id)
    assert len(events) == before + 1
    assert events[-1].event_type == "authorization_decision"
    assert events[-1].operation_outcome == "failed"


def test_orphan_marker_uses_pre_record_authority_and_never_infers_owner(publication):
    publisher, _, bundle, _, clock = publication
    publisher.store.publish(bundle.key, bundle.manifest_bytes, bundle.files)
    service = operator_service(publication)
    assert service.record_orphan(bundle.key) == "ORPHAN_MARKER"
    assert service.record_orphan(bundle.key) == "ORPHAN_MARKER"
    with Session(publisher.queue.engine) as session:
        row = session.execute(select(content_models.content_repair_record)).mappings().one()
        assert (
            row["artifact_id"] is None
            and row["storage_key"] == f"{bundle.key.prefix}/manifest.json"
        )
        assert row["kind"] == "ORPHAN_MARKER"
        assert session.get(ContentArtifact, bundle.key.artifact_id) is None
    clock[0] += timedelta(minutes=2)
    with pytest.raises(AuthorizationDenied):
        service.record_orphan(bundle.key)
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes


@pytest.mark.parametrize("publication", [1], indirect=True)
@pytest.mark.parametrize("ambiguous", [False, True])
def test_legacy_backfill_preserves_bytes_and_reports_blocked_metadata(publication, ambiguous):
    publisher, _, bundle, _, _ = publication
    publisher.store.publish(bundle.key, bundle.manifest_bytes, bundle.files)
    with Session(publisher.queue.engine) as session, session.begin():
        _register_artifact(session, bundle.manifest)
        if ambiguous:
            session.execute(update(ContentArtifact).values(recipe_sha256="c" * 64))
    service = operator_service(publication)
    assert service.inspect_artifact(bundle.key.artifact_id, backfill=True) == (
        "BLOCKED" if ambiguous else "READY"
    )
    with Session(publisher.queue.engine) as session:
        metadata = ContentArtifactRepository(session).get_metadata(bundle.key.artifact_id)
        metadata.verify_identity(publisher.store.load_verified(metadata.key))
        if ambiguous:
            assert metadata.publication_state == "legacy_unverified"
            repair = session.execute(select(content_models.content_repair_record)).mappings().one()
            assert repair["kind"] == "LEGACY_BACKFILL_BLOCKED"
            assert (
                session.execute(select(content_models.content_artifact_state_event)).first() is None
            )
        else:
            assert metadata.publication_state == "ready" and metadata.key.contract_version == 1
            assert metadata.manifest_sha256 == bundle.manifest_sha256
            state = (
                session.execute(select(content_models.content_artifact_state_event))
                .mappings()
                .one()
            )
            assert state["trigger"] == "LEGACY_BACKFILL"
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes


def test_operator_cli_runs_scoped_inventory_and_sweep_in_owned_database(
    publication, monkeypatch, capsys
):
    import sys

    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    cli = runpy.run_path(
        str(PRODUCT / "neuron/packages/brain-ingestion/src/brain_ingestion/integrity_sweep.py")
    )
    main = cli["main"]
    config = LocalObjectStoreConfig("filesystem", publisher.store.objects._root, True)
    monkeypatch.setitem(main.__globals__, "load_local_object_store_config", lambda: config)
    monkeypatch.setenv(
        "BRAIN_WORKER_DATABASE_URL",
        publisher.queue.engine.url.render_as_string(hide_password=False),
    )
    monkeypatch.setenv("BRAIN_WORKER_PRINCIPAL_ID", lease.payload["actor_id"])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "brain-content-integrity-sweep",
            "--policy-dir",
            str(PRODUCT / "planning-mds/security/policies"),
            "--tenant",
            str(bundle.key.tenant_id),
            "--knowledge-base",
            str(bundle.key.knowledge_base_id),
            "--action",
            "sweep",
        ],
    )
    assert main() == 0
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["counts"] == {"VERIFIED": 1}


def test_uniqueness_reconciliation_discovers_only_single_version_constraint(publication):
    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    service = operator_service(publication)
    with pytest.raises(ValueError, match="quiesced"):
        service.reconcile_uniqueness(writers_quiesced=False)
    with Session(publisher.queue.engine) as session:
        before = inspect(session.connection()).get_unique_constraints(
            "content_artifact", schema="public"
        )
    assert any(row["column_names"] == ["document_version_id"] for row in before)
    assert service.reconcile_uniqueness(writers_quiesced=True) == "RECONCILED"
    with Session(publisher.queue.engine) as session:
        after = inspect(session.connection()).get_unique_constraints(
            "content_artifact", schema="public"
        )
        assert not any(row["column_names"] == ["document_version_id"] for row in after)
        assert {row["name"] for row in after} == {
            row["name"] for row in before if row["column_names"] != ["document_version_id"]
        }
        ContentArtifactRepository(session).get_metadata(bundle.key.artifact_id).verify_identity(
            bundle
        )


@pytest.mark.parametrize("publication", [1], indirect=True)
def test_uniqueness_reconciliation_refuses_unverified_legacy_inventory(publication):
    publisher, _, bundle, _, _ = publication
    publisher.store.publish(bundle.key, bundle.manifest_bytes, bundle.files)
    with Session(publisher.queue.engine) as session, session.begin():
        _register_artifact(session, bundle.manifest)
    with pytest.raises(ValueError, match="reconciled and ready"):
        operator_service(publication).reconcile_uniqueness(writers_quiesced=True)
    with Session(publisher.queue.engine) as session:
        constraints = inspect(session.connection()).get_unique_constraints(
            "content_artifact", schema="public"
        )
        assert any(row["column_names"] == ["document_version_id"] for row in constraints)


@pytest.mark.parametrize("publication", ["fallback"], indirect=True)
def test_fallback_marker_and_observed_count_survive_readiness_failure_without_conversion(
    publication, monkeypatch
):
    publisher, lease, bundle, _, _ = publication
    original = ContentArtifactRepository.register_ready

    def fail_after_registration(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError("synthetic fallback readiness failure")

    monkeypatch.setattr(ContentArtifactRepository, "register_ready", fail_after_registration)
    with pytest.raises(RuntimeError, match="synthetic"):
        publisher.publish(
            lease,
            bundle.key,
            bundle.manifest_bytes,
            bundle.files,
            writer_fallback_reason="ORIGIN_UNAVAILABLE",
            unattributed_item_count=3,
        )
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        assert session.get(ContentArtifact, bundle.key.artifact_id) is None
    monkeypatch.setattr(ContentArtifactRepository, "register_ready", original)
    # No producer is called again. Count zero explicitly recovers the immutable
    # intent tied to these source/version/recipe/bundle fingerprints.
    retained = publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    assert retained.manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        row = session.get(ContentArtifact, bundle.key.artifact_id)
        assert row.publication_state == "ready" and row.artifact_contract_version == 1
        assert row.writer_fallback_reason == "ORIGIN_UNAVAILABLE"
        assert row.document_version_id == bundle.manifest.version_id
        events = session.scalars(
            select(AuditEventRow).where(AuditEventRow.event_type == "content_artifact_published")
        ).all()
        assert len(events) == 1
        assert events[0].payload["unattributed_item_count"] == 3
        resources = set(
            session.scalars(
                select(AuditEventRow.resource_id).where(
                    AuditEventRow.event_type == "authorization_decision"
                )
            ).all()
        )
        assert resources == {lease.artifact_id, bundle.key.artifact_id}
        assert session.execute(select(content_models.content_block)).first() is None
    assert lease.artifact_id != bundle.key.artifact_id


@pytest.mark.parametrize("publication", ["fallback"], indirect=True)
@pytest.mark.parametrize("fault", ["missing", "tampered"])
def test_fallback_adoption_requires_retained_integrity_checked_intent(publication, fault):
    publisher, lease, bundle, _, _ = publication
    if fault == "missing":
        publisher.store.publish(bundle.key, bundle.manifest_bytes, bundle.files)
    else:
        from brain_worker.publication_intent import retain_fallback_intent

        retain_fallback_intent(
            publisher.objects,
            bundle,
            recipe_sha256=lease.payload["recipe_sha256"],
            observed_count=2,
        )
        path = publisher.objects._root / (
            f"publication-intents/{bundle.key.tenant_id}/{bundle.key.knowledge_base_id}/"
            f"{bundle.key.artifact_id}/fallback.json"
        )
        value = json.loads(path.read_bytes())
        value["unattributed_item_count"] = 9
        path.write_text(json.dumps(value))
    with pytest.raises(ArtifactIntegrityError, match="intent"):
        publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    with Session(publisher.queue.engine) as session:
        assert session.get(ContentArtifact, bundle.key.artifact_id) is None
        assert (
            session.scalars(
                select(AuditEventRow).where(
                    AuditEventRow.event_type == "content_artifact_published"
                )
            ).first()
            is None
        )


@pytest.mark.parametrize("publication", ["june"], indirect=True)
async def test_june_example_retains_issued_date_without_deriving_canonical_time(date_services):
    services, actor, _, bundle, publisher = date_services
    basis = ContentDateBasis(
        kind="CONTENT",
        artifact_id=bundle.key.artifact_id,
        block_id="#/texts/0",
        record_ordinal=0,
        record_sha256=sha256(bundle.files["blocks.jsonl"].splitlines()[0]),
        quote="2026-06-10",
    )
    async with services() as service:
        candidate = await service.append_candidate(
            actor,
            artifact_id=bundle.key.artifact_id,
            date=DocumentDateValue(precision="DAY", value="2026-06-10"),
            basis=basis,
            supersedes_id=None,
            idempotency_key="june-issued",
            trace_id="june-issued",
        )
        view = await service.read(
            actor, artifact_id=bundle.key.artifact_id, selection_id=None, trace_id="june-read"
        )
    assert view.candidates == (candidate,)
    assert candidate.date.value == "2026-06-10" and candidate.basis.quote == "2026-06-10"
    assert view.selected_date is None and view.selection is None
    assert publisher.store.load_verified(bundle.key).manifest_bytes == bundle.manifest_bytes
    with Session(publisher.queue.engine) as session:
        assert (
            session.execute(text("SELECT count(*) FROM canonical_fact_version")).scalar_one() == 0
        )


@pytest.mark.parametrize("publication", ["tables"], indirect=True)
def test_durable_table_cells_headers_and_continuations_round_trip(publication, database):
    publisher, lease, bundle, _, _ = publication
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    publisher.publish(lease, bundle.key, bundle.manifest_bytes, bundle.files)
    with Session(publisher.queue.engine) as session:
        repository = ContentArtifactRepository(session)
        repository.verify_indexes(bundle)
        rows = (
            session.execute(
                select(content_models.content_table).order_by(
                    content_models.content_table.c.record_ordinal
                )
            )
            .mappings()
            .all()
        )
        assert [(row["table_id"], row["continuation_of"], row["header_rows"]) for row in rows] == [
            ("t1", "t0", [0]),
            ("t0", None, [0]),
        ]
        cells = session.execute(select(content_models.content_table_cell)).mappings().all()
        links = session.execute(select(content_models.content_table_cell_block)).mappings().all()
        assert len(cells) == len(links) == 2
        assert {row["cell_id"] for row in cells} == {"cell-0", "cell-1"}
        assert all(row["row_span"] == 2 and row["col_span"] == 1 for row in cells)
        assert all(
            (row["tenant_id"], row["knowledge_base_id"])
            == (bundle.key.tenant_id, bundle.key.knowledge_base_id)
            for row in cells + links
        )
        assert all(row["block_id"] == "#/texts/0" for row in links)
        events = session.scalars(
            select(AuditEventRow).where(AuditEventRow.event_type == "content_artifact_published")
        ).all()
        assert len(events) == 1
    # The database rejects cross-owner links independently of the verifier.
    with psycopg.connect(database, autocommit=True) as connection:
        connection.execute("TRUNCATE content_table_cell_block")
        with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
            connection.execute(
                "INSERT INTO content_table_cell_block "
                "(artifact_id,table_id,cell_id,block_id,tenant_id,knowledge_base_id,created_by) "
                "VALUES (%s,'t0','cell-0','#/texts/0',%s,%s,%s)",
                (
                    bundle.key.artifact_id,
                    bundle.key.tenant_id,
                    uuid4(),
                    UUID(lease.payload["actor_id"]),
                ),
            )
    with (
        Session(publisher.queue.engine) as session,
        pytest.raises(ArtifactIntegrityError, match="links"),
    ):
        ContentArtifactRepository(session).verify_indexes(bundle)
