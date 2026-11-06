"""F0006's independently authored PostgreSQL and immutable-source test harness.

Each test owns a new database. The historical development database is used only
as an administrative connection if explicitly configured; it is never changed.
"""

from __future__ import annotations

import io
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import parse_manifest
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_content.validation import ArtifactKey, inventory_hash, sha256, verify_bundle
from brain_content.verified_store import VerifiedBundleStore
from brain_domain.assertions import ProducerContext
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.principal import PrincipalKind
from brain_jobs.queue import DocumentJobQueue
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.models import SemanticInterpretationRun
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationExecution
from brain_testing import fixtures
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from brain_worker.content_publication import AuthorizedContentPublisher

PRODUCT = Path(__file__).resolve().parents[4]
POLICIES = PRODUCT / "planning-mds/security/policies"
NATIVE = json.loads(Path(__file__).with_name("native-sources.json").read_text())


@pytest.fixture(autouse=True)
def _clean_fact_tables():
    # Override integration/conftest.py's cleanup of the shared development DB.
    yield


def configuration():
    path = PRODUCT / "engine/migrations/alembic.ini"
    config = Config(str(path))
    config.set_main_option("script_location", str(path.parent))
    return config


@pytest.fixture
def database(monkeypatch):
    admin = os.environ.get("BRAIN_MIGRATION_ADMIN_URL")
    if not admin:
        pytest.skip("Set BRAIN_MIGRATION_ADMIN_URL for owned F0006 PostgreSQL test databases")
    admin = admin.replace("postgresql+psycopg://", "postgresql://")
    name = "f0006_qe_" + secrets.token_hex(6)
    assert name.startswith("f0006_qe_") and name != "brain"
    with psycopg.connect(admin, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    url = admin.rsplit("/", 1)[0] + "/" + name
    monkeypatch.setenv("BRAIN_DATABASE_URL", url.replace("postgresql://", "postgresql+psycopg://"))
    try:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        yield url
    finally:
        with psycopg.connect(admin, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )


def encoded(record):
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode()


def native_bytes(kind, text):
    if kind == "csv":
        return ('account,limit\nCedar Bridge Roofing,"' + text + '"\n').encode()
    if kind == "pdf":
        return ("%PDF-1.4\n% synthetic retained-source fixture\n" + text + "\n%%EOF\n").encode()
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        if kind == "docx":
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
                + text
                + "</w:t></w:r></w:p></w:body></w:document>",
            )
        else:
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="2"><c r="B2" t="inlineStr"><is><t>'
                + text
                + "</t></is></c></row></sheetData></worksheet>",
            )
    return buffer.getvalue()


def bundle_fixture(*, kind="pdf", text=None, origin="STATED", owner=None, qualified=True):
    text = text or NATIVE["default_text"]
    tenant, kb = owner or (uuid4(), uuid4())
    native = {
        "texts": [
            {
                "self_ref": "#/texts/0",
                "text": text,
                "source_locator": NATIVE["sources"][kind]["locator"],
            }
        ],
        "pages": {"1": {"size": {"width": 612, "height": 792}}},
        "tables": [],
    }
    region = {
        "page": 1,
        "bbox": {"x0": 10.0, "y0": 20.0, "x1": 500.0, "y1": 60.0},
        "char_start": 0,
        "char_end": len(text),
    }
    anchor = {"kind": "native_text", "native_ref": "#/texts/0", "regions": [region]}
    if origin == "OCR":
        anchor = {"kind": "page_region", "regions": [region]}
    elif origin == "TRANSCRIBED":
        anchor = {
            "kind": "time_span",
            "start_ms": 0,
            "end_ms": 5000,
            "speaker": "synthetic-speaker",
        }
    elif origin == "DESCRIBED":
        anchor = {"kind": "figure", "figure_ref": "#/pictures/0", "regions": [region]}
        native["pictures"] = [{"self_ref": "#/pictures/0"}]
    block = {
        "record_type": "block",
        "contract_version": 2,
        "block_id": "#/texts/0",
        "native_ref": "#/texts/0",
        "reading_order": 0,
        "section_path": [],
        "text": text,
        "text_origin": origin,
        "confidence": 0.87 if origin in ("OCR", "TRANSCRIBED") else None,
        "producer": {
            "engine": "independent-synthetic-source",
            "engine_version": "1",
            "model": "synthetic" if origin == "DESCRIBED" else None,
            "model_version": "1" if origin == "DESCRIBED" else None,
        },
        "origin_anchor": anchor,
    }
    # F0004 v2 keeps a PDF source/rendition. Non-PDF synthetic fixtures also
    # retain immutable original assets and format-specific native locators.
    # This does not activate a new content writer or claim conversion proof.
    source_name = "source.pdf"
    if kind != "pdf":
        native["retained_original"] = {"uri": f"assets/source.{kind}"}
    files = {
        "docling-document.json": encoded(native),
        "normalized.md": text.encode(),
        "blocks.jsonl": encoded(block) + b"\n",
        "tables.jsonl": b"",
        "layout.jsonl": encoded(
            {
                "record_type": "layout",
                "contract_version": 2,
                "page": 1,
                "geometry_state": "available",
                "width": 612,
                "height": 792,
                "rotation_degrees": 0,
                "native_to_canonical": [1, 0, 0, 1, 0, 0],
                "unavailable_reason": None,
            }
        )
        + b"\n",
        source_name: native_bytes("pdf", text),
        **({f"assets/source.{kind}": native_bytes(kind, text)} if kind != "pdf" else {}),
    }
    manifest = {
        "tenant_id": str(tenant),
        "knowledge_base_id": str(kb),
        "document_id": str(uuid4()),
        "version_id": str(uuid4()),
        "artifact_id": str(uuid4()),
        "artifact_contract_version": 2,
        "source_sha256": sha256(files[source_name]),
        "artifact_sha256": inventory_hash(files, 2),
        "docling_document": {
            "path": "docling-document.json",
            "schema_version": "synthetic-f0006",
            "sha256": sha256(files["docling-document.json"]),
        },
        "files": [
            {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}
            for path, raw in files.items()
        ],
        "execution": {
            "parser_package_version": "synthetic-retained-snapshot",
            "model_artifact_digests": [],
            "configuration_hash": "a" * 64,
            "environment_digest": "f0006-independent-fixture",
            "parser_name": "docling",
            "projection_version": "synthetic-1",
        },
        "extraction_quality": {"status": "complete", "failed_pages": [], "warnings": []},
        "page_count": 1,
        "coordinate_origin": "top_left",
        "offset_encoding": "unicode_code_points",
        "created_at": datetime.now(UTC).isoformat(),
        "source_file": source_name,
        "recipe_sha256": "b" * 64,
        "bundle_hash_algorithm": "sha256-file-inventory-v2",
        "record_contract_version": 2,
        "page_number_base": 1,
        "coordinate_units": "pdf_points",
        "text_normalization_version": "identity-unicode-v1",
    }
    model = parse_manifest(encoded(manifest))
    key = ArtifactKey(model.artifact_id, tenant, kb, 2)
    return verify_bundle(key, encoded(manifest), files)


class World:
    def __init__(self, database, root, *, kind="pdf", text=None, origin="STATED", owner=None):
        self.url = database
        self.bundle = bundle_fixture(kind=kind, text=text, origin=origin, owner=owner)
        self.text = self.bundle.blocks[0].text
        self.owner = (self.bundle.key.tenant_id, self.bundle.key.knowledge_base_id)
        self.sync_engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
        self.engine = create_async_engine(
            database.replace("postgresql://", "postgresql+asyncpg://")
        )
        self.policy = CasbinAuthorizationAdapter(POLICIES / "model.conf", POLICIES / "policy.csv")
        with Session(self.sync_engine) as session, session.begin():
            fixtures.seed_scope(session, *self.owner)
            self.actor = fixtures.seed_principal(
                session,
                issuer="urn:f0006:independent",
                subject=str(uuid4()),
                kind=PrincipalKind.SERVICE,
            )
            fixtures.seed_grant(session, self.actor.id, *self.owner, "ServicePrincipal")
            fixtures.seed_grant(session, self.actor.id, *self.owner, "TenantMember")
            self.reviewer = fixtures.seed_principal(
                session, issuer="urn:f0006:independent", subject=str(uuid4())
            )
            fixtures.seed_grant(session, self.reviewer.id, *self.owner, "Reviewer")
            fixtures.seed_grant(session, self.reviewer.id, *self.owner, "TenantMember")
            fixtures.activate_policy(session, POLICIES / "model.conf", POLICIES / "policy.csv")
            fixtures.protect(
                session,
                ResourceKey(ResourceType.CONTENT_ARTIFACT, self.bundle.key.artifact_id),
                *self.owner,
                before_record=True,
            )
        self.objects = LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", root, True))
        store = VerifiedBundleStore(self.objects)
        self.content = LocalContentArtifactStore(self.objects)
        queue = DocumentJobQueue(self.sync_engine, lease_seconds=30)
        queue.enqueue(
            tenant_id=self.owner[0],
            knowledge_base_id=self.owner[1],
            artifact_id=self.bundle.key.artifact_id,
            request_key="f0006-source-" + str(self.bundle.key.artifact_id),
            payload={
                "content_contract_version": 2,
                "actor_id": str(self.actor.id),
                "correlation_id": str(uuid4()),
                "document_id": str(self.bundle.manifest.document_id),
                "version_id": str(self.bundle.manifest.version_id),
                "source_sha256": self.bundle.manifest.source_sha256,
                "recipe_sha256": self.bundle.manifest.recipe_sha256,
            },
        )
        publisher = AuthorizedContentPublisher(queue, store, self.policy, objects=self.objects)
        publisher.publish(
            queue.claim(), self.bundle.key, self.bundle.manifest_bytes, self.bundle.files
        )
        self.run_id = uuid4()
        with Session(self.sync_engine) as session, session.begin():
            session.add(
                SemanticInterpretationRun(
                    id=self.run_id,
                    artifact_id=self.bundle.key.artifact_id,
                    profile_id="f0006-independent",
                    profile_version="1",
                    status="complete",
                    counters={},
                    run_configuration={},
                    tenant_id=self.owner[0],
                    knowledge_base_id=self.owner[1],
                )
            )
        self.context = ProducerContext(
            tenant_id=self.owner[0],
            knowledge_base_id=self.owner[1],
            actor_id=self.actor.id,
            artifact_id=self.bundle.key.artifact_id,
            document_version_id=self.bundle.manifest.version_id,
            run_id=self.run_id,
            origin="DOCUMENT_INTERPRETATION",
            model_id="synthetic:no-model-call",
            prompt_hash="independent-f0006-v1",
            trace_id="f0006-integration",
        )
        self.subject_id = uuid4()
        self.entity = {
            "id": str(self.subject_id),
            "entity_type": "Policy",
            "label": "Cedar Bridge Roofing",
            "introducing_evidence": [self.evidence(self.text)],
        }

    def evidence(self, quote):
        return {
            "artifact_id": str(self.bundle.key.artifact_id),
            "block_id": "#/texts/0",
            "quote": quote,
            "model_selector": {"char_start": 99999, "char_end": 100000},
        }

    def candidate(self, **updates):
        record = {
            "id": str(uuid4()),
            "assertion_kind": "TYPED_ASSERTION",
            "subject_ref": str(self.subject_id),
            "object": {"kind": "LITERAL", "value": {"amount": 500000, "currency": "USD"}},
            "predicate_id": "each_occurrence_limit",
            "ontology_release": "synthetic-gl-v1",
            "source_relation": None,
            "qualifiers": {},
            "time_mention_refs": [],
            "valid_time_claim": {"source_words": "Effective 2026-06-01"},
            "mode": "ASSERTED",
            "origin": "DOCUMENT_INTERPRETATION",
            "interpretation_basis": "EXPLICIT",
            "model_confidence": 0.98,
            "evidence": [self.evidence(self.text)],
        }
        record.update(updates)
        return record

    @asynccontextmanager
    async def service(self, *, time_resolver=None):
        from brain_assertions.admission import AssertionAdmissionService
        from brain_assertions.service import AssertionWriteService
        from brain_persistence.assertions import (
            SqlAlchemyAdmissionSources,
            SqlAlchemyAssertionRepository,
        )

        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            repository = SqlAlchemyAssertionRepository(session, content_store=self.content)
            admission = AssertionAdmissionService(
                SqlAlchemyAdmissionSources(session, self.content, time_resolver=time_resolver)
            )
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), self.policy, self.policy.release
            )
            yield AssertionWriteService(repository, admission, execution), repository, session

    async def admit(
        self,
        records,
        *,
        entities=None,
        principal=None,
        context=None,
        delivery_key="independent-delivery",
        time_resolver=None,
        **issues,
    ):
        async with self.service(time_resolver=time_resolver) as (service, _, _):
            return await service.admit(
                principal or self.actor,
                context or self.context,
                entities=entities or [self.entity],
                items=[encoded(row) if not isinstance(row, bytes) else row for row in records],
                delivery_key=delivery_key,
                **issues,
            )

    async def close(self):
        await self.engine.dispose()
        self.sync_engine.dispose()


@pytest.fixture
async def world_factory(database, tmp_path):
    command.upgrade(configuration(), "head")
    worlds = []

    def create(**kwargs):
        world = World(database, tmp_path / str(len(worlds)), **kwargs)
        worlds.append(world)
        return world

    try:
        yield create
    finally:
        for world in worlds:
            await world.close()


@pytest.fixture
async def world(world_factory):
    return world_factory()


def counts(database):
    with psycopg.connect(database) as connection:
        return {
            table: connection.execute(
                sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
            ).fetchone()[0]
            for table in (
                "assertion",
                "assertion_evidence",
                "assertion_semantics",
                "assertion_document_reference",
                "assertion_name_claim",
                "review_item",
                "canonical_commit",
                "canonical_fact_version",
            )
        }
