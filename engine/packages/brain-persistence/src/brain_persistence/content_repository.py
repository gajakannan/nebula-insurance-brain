"""F0004 metadata/index adapter; never commits the caller's unit of work."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4, uuid5

from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.service import ArtifactMetadata
from brain_content.store import ArtifactNotFound
from brain_content.validation import (
    ArtifactConflict,
    ArtifactIntegrityError,
    ArtifactKey,
    VerifiedBundle,
    sha256,
)
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from brain_persistence import content_models as tables
from brain_persistence.models import AuditEventRow, ContentArtifact, DocumentVersion, SourceDocument


def lock_content_identity(
    session: Session, key: ArtifactKey, document_id: UUID, version_id: UUID, source_sha256: str
) -> None:
    """After authority: source, version, then artifact transaction advisory locks."""
    if session.get_bind().dialect.name != "postgresql":
        return
    for identity in (
        f"source:{key.tenant_id}:{key.knowledge_base_id}:{source_sha256}",
        f"version:{document_id}:{version_id}",
        f"artifact:{key.artifact_id}",
    ):
        lock_id = int.from_bytes(bytes.fromhex(sha256(identity.encode()))[:8], signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})


def lock_artifact(session: Session, artifact_id: UUID) -> None:
    """For operators that touch only an orphan artifact, never source/version rows."""
    if session.get_bind().dialect.name == "postgresql":
        lock_id = int.from_bytes(
            bytes.fromhex(sha256(f"artifact:{artifact_id}".encode()))[:8], signed=True
        )
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})


class ContentArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def expanded(self) -> bool:
        names = {
            column["name"]
            for column in inspect(self.session.connection()).get_columns("content_artifact")
        }
        return "artifact_contract_version" in names

    def _row(self, artifact_id: UUID) -> dict[str, Any]:
        table = ContentArtifact.__table__
        expansion = {
            "artifact_contract_version",
            "recipe_sha256",
            "manifest_sha256",
            "supersedes_artifact_id",
            "publication_state",
            "writer_fallback_reason",
        }
        expanded = self.expanded()
        columns = [column for column in table.c if expanded or column.name not in expansion]
        row = (
            self.session.execute(select(*columns).where(table.c.id == artifact_id))
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise ArtifactNotFound(str(artifact_id))
        result = dict(row)
        if not expanded:
            result.update({name: None for name in expansion})
            result["publication_state"] = "legacy_unverified"
        return result

    def get_key(self, artifact_id: UUID) -> ArtifactKey:
        row = self._row(artifact_id)
        version = (
            1 if row["artifact_contract_version"] is None else row["artifact_contract_version"]
        )
        if version not in (1, 2):
            raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")
        return ArtifactKey(
            artifact_id, row["tenant_id"], row["knowledge_base_id"], cast(Literal[1, 2], version)
        )

    def get_metadata(self, artifact_id: UUID) -> ArtifactMetadata:
        row = self._row(artifact_id)
        key = self.get_key(artifact_id)
        parent = self.session.execute(
            select(
                SourceDocument.id,
                SourceDocument.source_sha256,
            )
            .join(DocumentVersion, DocumentVersion.source_document_id == SourceDocument.id)
            .where(
                DocumentVersion.id == row["document_version_id"],
                DocumentVersion.tenant_id == key.tenant_id,
                DocumentVersion.knowledge_base_id == key.knowledge_base_id,
                SourceDocument.tenant_id == key.tenant_id,
                SourceDocument.knowledge_base_id == key.knowledge_base_id,
            )
        ).one_or_none()
        if parent is None or row["publication_state"] not in (
            "legacy_unverified",
            "ready",
            "quarantined",
        ):
            raise ArtifactIntegrityError("artifact ownership metadata is inconsistent")
        return ArtifactMetadata(
            key,
            parent.id,
            row["document_version_id"],
            parent.source_sha256,
            row["artifact_sha256"],
            row["manifest_sha256"],
            row["recipe_sha256"],
            cast(Literal["legacy_unverified", "ready", "quarantined"], row["publication_state"]),
        )

    def find_source(
        self, tenant_id: UUID, knowledge_base_id: UUID, source_sha256: str
    ) -> tuple[UUID, tuple[ArtifactKey, ...]] | None:
        document = self.session.execute(
            select(SourceDocument.id).where(
                SourceDocument.tenant_id == tenant_id,
                SourceDocument.knowledge_base_id == knowledge_base_id,
                SourceDocument.source_sha256 == source_sha256,
            )
        ).scalar_one_or_none()
        if document is None:
            return None
        ids = (
            self.session.execute(
                select(ContentArtifact.id)
                .join(DocumentVersion)
                .where(
                    DocumentVersion.source_document_id == document,
                )
            )
            .scalars()
            .all()
        )
        rows = {artifact_id: self._row(artifact_id) for artifact_id in ids}
        superseded = {
            row["supersedes_artifact_id"]
            for row in rows.values()
            if row["supersedes_artifact_id"] is not None
        }
        keys = []
        for artifact_id, row in rows.items():
            if artifact_id in superseded:
                continue
            # A corrupt/quarantined accepted source is never a conversion miss.
            if row["publication_state"] == "quarantined":
                raise ArtifactIntegrityError("accepted source has a quarantined artifact")
            keys.append(self.get_key(artifact_id))
        return document, tuple(keys)

    def authorization_audit(
        self, decision_id: UUID, actor_id: UUID, key: ArtifactKey
    ) -> AuditEventRow:
        row = self.session.execute(
            select(AuditEventRow).where(
                AuditEventRow.decision_id == decision_id,
                AuditEventRow.event_type == "authorization_decision",
            )
        ).scalar_one_or_none()
        scope = (row.payload or {}).get("scope", {}) if row else {}
        if (
            row is None
            or not row.decision
            or row.operation_outcome != "succeeded"
            or row.actor_principal_id != actor_id
            or row.resource_type != "content_artifact"
            or row.resource_id != key.artifact_id
            or row.action != "ingest"
            or scope.get("tenant_id") != str(key.tenant_id)
            or scope.get("knowledge_base_id") != str(key.knowledge_base_id)
        ):
            raise PermissionError(
                "publication requires its current successful authorization decision"
            )
        return row

    def mutation_event(
        self,
        authorization: AuditEventRow,
        event_type: str,
        payload: dict[str, Any],
        event_id: UUID | None = None,
    ) -> UUID:
        event_id = event_id or uuid4()
        self.session.add(
            AuditEventRow(
                id=event_id,
                occurred_at=datetime.now(UTC).replace(tzinfo=None),
                actor_principal_id=authorization.actor_principal_id,
                delegate_principal_id=authorization.delegate_principal_id,
                resource_type=authorization.resource_type,
                resource_id=authorization.resource_id,
                action=authorization.action,
                decision=True,
                reason_code=authorization.reason_code,
                policy_hash=authorization.policy_hash,
                grant_revision=authorization.grant_revision,
                trace_id=authorization.trace_id,
                decision_id=authorization.decision_id,
                event_type=event_type,
                operation_outcome="succeeded",
                payload=payload,
            )
        )
        self.session.flush()
        return event_id

    def register_ready(
        self,
        bundle: VerifiedBundle,
        *,
        actor_id: UUID,
        authorization_decision_id: UUID,
        supersedes_artifact_id: UUID | None,
        writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"] | None = None,
        unattributed_item_count: int = 0,
    ) -> None:
        if not self.expanded():
            raise RuntimeError("content schema expansion is required before publication")
        manifest, key = bundle.manifest, bundle.key
        authorization = self.authorization_audit(authorization_decision_id, actor_id, key)
        if manifest.extraction_quality.status == "failed":
            raise ArtifactIntegrityError("failed parsing cannot become ready content")
        if writer_fallback_reason and (key.contract_version != 1 or unattributed_item_count < 1):
            raise ValueError("invalid writer fallback metadata")
        source = self.session.get(SourceDocument, manifest.document_id)
        if source is None:
            source = SourceDocument(
                id=manifest.document_id,
                tenant_id=key.tenant_id,
                knowledge_base_id=key.knowledge_base_id,
                source_sha256=manifest.source_sha256,
            )
            self.session.add(source)
            self.session.flush()
        if (source.tenant_id, source.knowledge_base_id, source.source_sha256) != (
            key.tenant_id,
            key.knowledge_base_id,
            manifest.source_sha256,
        ):
            raise ArtifactConflict("source identity conflict")
        version = self.session.get(DocumentVersion, manifest.version_id)
        if version is None:
            version = DocumentVersion(
                id=manifest.version_id,
                source_document_id=source.id,
                tenant_id=key.tenant_id,
                knowledge_base_id=key.knowledge_base_id,
            )
            self.session.add(version)
            self.session.flush()
        if (version.source_document_id, version.tenant_id, version.knowledge_base_id) != (
            source.id,
            key.tenant_id,
            key.knowledge_base_id,
        ):
            raise ArtifactConflict("version identity conflict")
        prior = self.session.get(ContentArtifact, key.artifact_id)
        if prior is not None:
            self.get_metadata(key.artifact_id).verify_identity(bundle)
            self.verify_indexes(bundle)
            return
        if supersedes_artifact_id:
            predecessor = self.get_metadata(supersedes_artifact_id)
            if (
                predecessor.version_id,
                predecessor.key.tenant_id,
                predecessor.key.knowledge_base_id,
            ) != (version.id, key.tenant_id, key.knowledge_base_id):
                raise ArtifactConflict("replacement artifact belongs to another source")
        self.session.add(
            ContentArtifact(
                id=key.artifact_id,
                document_version_id=version.id,
                tenant_id=key.tenant_id,
                knowledge_base_id=key.knowledge_base_id,
                artifact_sha256=manifest.artifact_sha256,
                page_count=manifest.page_count,
                extraction_status=manifest.extraction_quality.status,
                artifact_contract_version=key.contract_version,
                recipe_sha256=getattr(manifest, "recipe_sha256", None),
                manifest_sha256=bundle.manifest_sha256,
                supersedes_artifact_id=supersedes_artifact_id,
                publication_state="ready",
                writer_fallback_reason=writer_fallback_reason,
            )
        )
        self.session.flush()
        self._insert_indexes(bundle, actor_id)
        self.mutation_event(
            authorization,
            "content_artifact_published",
            {
                "artifact_id": str(key.artifact_id),
                "document_id": str(source.id),
                "version_id": str(version.id),
                "artifact_sha256": manifest.artifact_sha256,
                "manifest_sha256": bundle.manifest_sha256,
                "authorization_decision_id": str(authorization_decision_id),
                "writer_fallback_reason": writer_fallback_reason,
                "unattributed_item_count": unattributed_item_count,
            },
            uuid5(key.artifact_id, "content_artifact_published"),
        )

    def _insert_indexes(self, bundle: VerifiedBundle, actor_id: UUID) -> None:
        block_lines = bundle.files["blocks.jsonl"].splitlines()
        table_lines = bundle.files["tables.jsonl"].splitlines()
        owner = {
            "artifact_id": bundle.key.artifact_id,
            "tenant_id": bundle.key.tenant_id,
            "knowledge_base_id": bundle.key.knowledge_base_id,
            "created_by": actor_id,
        }
        for ordinal, block in enumerate(bundle.blocks):
            data = block.model_dump(
                mode="json", exclude={"record_type", "contract_version", "text"}
            )
            self.session.execute(
                tables.content_block.insert().values(
                    **owner,
                    **data,
                    record_ordinal=ordinal,
                    record_sha256=sha256(block_lines[ordinal]),
                )
            )
        by_id = {table.table_id: (ordinal, table) for ordinal, table in enumerate(bundle.tables)}
        inserted: set[str] = set()

        def insert_table(table_id: str) -> None:
            if table_id in inserted:
                return
            ordinal, table = by_id[table_id]
            if table.continuation_of:
                insert_table(table.continuation_of)
            data = table.model_dump(
                mode="json", exclude={"record_type", "contract_version", "cells"}
            )
            self.session.execute(
                tables.content_table.insert().values(
                    **owner,
                    **data,
                    record_ordinal=ordinal,
                    record_sha256=sha256(table_lines[ordinal]),
                )
            )
            inserted.add(table_id)

        for table in bundle.tables:
            insert_table(table.table_id)
            for cell in table.cells:
                data = cell.model_dump(exclude={"text", "block_ids"})
                self.session.execute(
                    tables.content_table_cell.insert().values(
                        **owner,
                        table_id=table.table_id,
                        **data,
                    )
                )
                for block_id in cell.block_ids:
                    self.session.execute(
                        tables.content_table_cell_block.insert().values(
                            **owner,
                            table_id=table.table_id,
                            cell_id=cell.cell_id,
                            block_id=block_id,
                        )
                    )

    def verify_indexes(self, bundle: VerifiedBundle) -> None:
        if not self.expanded():
            if bundle.key.contract_version == 2:
                raise ArtifactIntegrityError("v2 content index schema is missing")
            return
        for model, records, filename in (
            (tables.content_block, bundle.blocks, "blocks.jsonl"),
            (tables.content_table, bundle.tables, "tables.jsonl"),
        ):
            rows = (
                self.session.execute(
                    select(model)
                    .where(model.c.artifact_id == bundle.key.artifact_id)
                    .order_by(model.c.record_ordinal)
                )
                .mappings()
                .all()
            )
            if len(rows) != len(records):
                raise ArtifactIntegrityError("normalized index inventory mismatch")
            record_lines = bundle.files[filename].splitlines()
            for ordinal, (row, record) in enumerate(zip(rows, records, strict=True)):
                fields = record.model_dump(
                    mode="json", exclude={"record_type", "contract_version", "text", "cells"}
                )
                if (
                    row["tenant_id"] != bundle.key.tenant_id
                    or row["knowledge_base_id"] != bundle.key.knowledge_base_id
                    or row["record_ordinal"] != ordinal
                    or row["record_sha256"] != sha256(record_lines[ordinal])
                    or any(row[name] != value for name, value in fields.items())
                ):
                    raise ArtifactIntegrityError("normalized index differs from retained records")
        expected_cells = {
            (table.table_id, cell.cell_id) for table in bundle.tables for cell in table.cells
        }
        cells = (
            self.session.execute(
                select(tables.content_table_cell).where(
                    tables.content_table_cell.c.artifact_id == bundle.key.artifact_id
                )
            )
            .mappings()
            .all()
        )
        if {(row["table_id"], row["cell_id"]) for row in cells} != expected_cells:
            raise ArtifactIntegrityError("normalized cell inventory mismatch")
        expected_by_id = {
            (table.table_id, cell.cell_id): cell for table in bundle.tables for cell in table.cells
        }
        for row in cells:
            cell = expected_by_id[(row["table_id"], row["cell_id"])]
            if (
                row["tenant_id"] != bundle.key.tenant_id
                or row["knowledge_base_id"] != bundle.key.knowledge_base_id
                or any(
                    row[name] != value
                    for name, value in cell.model_dump(exclude={"text", "block_ids"}).items()
                )
            ):
                raise ArtifactIntegrityError("normalized cell differs from retained record")
        expected_links = {
            (table.table_id, cell.cell_id, block)
            for table in bundle.tables
            for cell in table.cells
            for block in cell.block_ids
        }
        links = (
            self.session.execute(
                select(tables.content_table_cell_block).where(
                    tables.content_table_cell_block.c.artifact_id == bundle.key.artifact_id
                )
            )
            .mappings()
            .all()
        )
        if {(row["table_id"], row["cell_id"], row["block_id"]) for row in links} != expected_links:
            raise ArtifactIntegrityError("normalized cell/block links differ from retained records")
        if any(
            row["tenant_id"] != bundle.key.tenant_id
            or row["knowledge_base_id"] != bundle.key.knowledge_base_id
            for row in links
        ):
            raise ArtifactIntegrityError("normalized cell/block owner mismatch")
