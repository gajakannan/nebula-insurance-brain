"""Core metadata for F0004 indexes/history; PostgreSQL revision 0008 owns guards."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from brain_persistence.base import Base

J = JSONB().with_variant(JSON(), "sqlite")


def _owner() -> list[Column[Any]]:
    return [
        Column("tenant_id", Uuid, nullable=False),
        Column("knowledge_base_id", Uuid, nullable=False),
    ]


def _created() -> list[Column[Any]]:
    return [
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("created_by", Uuid, ForeignKey("principal.id"), nullable=False),
    ]


def _artifact_fk() -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["artifact_id", "tenant_id", "knowledge_base_id"],
        ["content_artifact.id", "content_artifact.tenant_id", "content_artifact.knowledge_base_id"],
    )


content_block = Table(
    "content_block",
    Base.metadata,
    Column("artifact_id", Uuid, primary_key=True),
    Column("block_id", Text, primary_key=True),
    *_owner(),
    Column("native_ref", Text, nullable=False),
    Column("reading_order", Integer, nullable=False),
    Column("section_path", J, nullable=False),
    Column("text_origin", String, nullable=False),
    Column("producer", J, nullable=False),
    Column("origin_anchor", J, nullable=False),
    Column("confidence", Float),
    Column("record_ordinal", Integer, nullable=False),
    Column("record_sha256", String(64), nullable=False),
    *_created(),
    _artifact_fk(),
    UniqueConstraint("artifact_id", "block_id", "tenant_id", "knowledge_base_id"),
    UniqueConstraint("artifact_id", "record_ordinal"),
)

content_table = Table(
    "content_table",
    Base.metadata,
    Column("artifact_id", Uuid, primary_key=True),
    Column("table_id", Text, primary_key=True),
    *_owner(),
    Column("native_ref", Text, nullable=False),
    Column("num_rows", Integer, nullable=False),
    Column("num_cols", Integer, nullable=False),
    Column("header_rows", J, nullable=False),
    Column("continuation_of", Text),
    Column("record_ordinal", Integer, nullable=False),
    Column("record_sha256", String(64), nullable=False),
    *_created(),
    _artifact_fk(),
    UniqueConstraint("artifact_id", "table_id", "tenant_id", "knowledge_base_id"),
    UniqueConstraint("artifact_id", "record_ordinal"),
)

content_table_cell = Table(
    "content_table_cell",
    Base.metadata,
    Column("artifact_id", Uuid, primary_key=True),
    Column("table_id", Text, primary_key=True),
    Column("cell_id", Text, primary_key=True),
    *_owner(),
    Column("row_start", Integer, nullable=False),
    Column("col_start", Integer, nullable=False),
    Column("row_span", Integer, nullable=False),
    Column("col_span", Integer, nullable=False),
    *_created(),
    ForeignKeyConstraint(
        ["artifact_id", "table_id", "tenant_id", "knowledge_base_id"],
        [
            "content_table.artifact_id",
            "content_table.table_id",
            "content_table.tenant_id",
            "content_table.knowledge_base_id",
        ],
    ),
    UniqueConstraint("artifact_id", "table_id", "cell_id", "tenant_id", "knowledge_base_id"),
)

content_table_cell_block = Table(
    "content_table_cell_block",
    Base.metadata,
    Column("artifact_id", Uuid, primary_key=True),
    Column("table_id", Text, primary_key=True),
    Column("cell_id", Text, primary_key=True),
    Column("block_id", Text, primary_key=True),
    *_owner(),
    *_created(),
    ForeignKeyConstraint(
        ["artifact_id", "table_id", "cell_id", "tenant_id", "knowledge_base_id"],
        [
            "content_table_cell.artifact_id",
            "content_table_cell.table_id",
            "content_table_cell.cell_id",
            "content_table_cell.tenant_id",
            "content_table_cell.knowledge_base_id",
        ],
    ),
    ForeignKeyConstraint(
        ["artifact_id", "block_id", "tenant_id", "knowledge_base_id"],
        [
            "content_block.artifact_id",
            "content_block.block_id",
            "content_block.tenant_id",
            "content_block.knowledge_base_id",
        ],
    ),
)


def _date_columns() -> list[Column[Any]]:
    return [
        Column("id", Uuid, primary_key=True),
        Column("document_version_id", Uuid, nullable=False),
        *_owner(),
        Column("idempotency_key", Text, nullable=False),
        Column("request_sha256", String(64), nullable=False),
        Column("actor_principal_id", Uuid, ForeignKey("principal.id"), nullable=False),
        Column("authorization_decision_id", Uuid, nullable=False),
        Column("authorization_audit_event_id", Uuid, ForeignKey("audit_event.id"), nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    ]


document_date_candidate = Table(
    "document_date_candidate",
    Base.metadata,
    *_date_columns(),
    Column("date_value", String(10), nullable=False),
    Column("date_precision", String, nullable=False),
    Column("basis_kind", String, nullable=False),
    Column("basis", J, nullable=False),
    Column("content_artifact_id", Uuid),
    Column("content_block_id", Text),
    Column("supersedes_id", Uuid),
    UniqueConstraint("document_version_id", "idempotency_key"),
    UniqueConstraint("id", "document_version_id", "tenant_id", "knowledge_base_id"),
)

document_date_selection = Table(
    "document_date_selection",
    Base.metadata,
    *_date_columns(),
    Column("candidate_id", Uuid),
    Column("previous_selection_id", Uuid),
    Column("human_decision_id", Uuid, nullable=False),
    Column("human_actor_principal_id", Uuid, ForeignKey("principal.id"), nullable=False),
    Column("human_authorization_decision_id", Uuid, nullable=False),
    Column("human_decided_at", DateTime(timezone=True), nullable=False),
    Column("human_receipt_sha256", String(64), nullable=False),
    Column("sequence", BigInteger, nullable=False),
    Column("reason", Text, nullable=False),
    UniqueConstraint("document_version_id", "idempotency_key"),
    UniqueConstraint("document_version_id", "sequence"),
    UniqueConstraint("id", "document_version_id", "tenant_id", "knowledge_base_id"),
)

content_repair_record = Table(
    "content_repair_record",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    *_owner(),
    Column("artifact_id", Uuid),
    Column("storage_key", Text),
    Column("kind", String, nullable=False),
    Column("detail", J, nullable=False),
    Column("resolves_id", Uuid),
    Column("resolution", String),
    Column("recorded_by", Uuid, ForeignKey("principal.id"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

content_artifact_state_event = Table(
    "content_artifact_state_event",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    *_owner(),
    Column("artifact_id", Uuid, nullable=False),
    Column("from_state", String, nullable=False),
    Column("to_state", String, nullable=False),
    Column("trigger", String, nullable=False),
    Column("reason_code", String, nullable=False),
    Column("actor_principal_id", Uuid, ForeignKey("principal.id"), nullable=False),
    Column("authorization_decision_id", Uuid, nullable=False),
    Column("audit_event_id", Uuid, ForeignKey("audit_event.id"), nullable=False),
    Column("repair_record_id", Uuid, ForeignKey("content_repair_record.id")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    _artifact_fk(),
)
