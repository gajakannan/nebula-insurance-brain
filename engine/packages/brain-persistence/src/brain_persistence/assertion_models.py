"""F0006 additive assertion tables; migration 0011 owns database backstops."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from brain_persistence.base import Base
from brain_persistence.models import _JSONVariant


class AssertionDocumentReference(Base):
    __tablename__ = "assertion_document_reference"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "document_version_id",
            "tenant_id",
            "knowledge_base_id",
            name="uq_assertion_reference_owner",
        ),
        ForeignKeyConstraint(
            ["document_version_id", "tenant_id", "knowledge_base_id"],
            [
                "document_version.id",
                "document_version.tenant_id",
                "document_version.knowledge_base_id",
            ],
            name="fk_assertion_reference_document",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AssertionNameClaim(Base):
    __tablename__ = "assertion_name_claim"
    __table_args__ = (
        ForeignKeyConstraint(
            ["entity_ref", "document_version_id", "tenant_id", "knowledge_base_id"],
            [
                "assertion_document_reference.id",
                "assertion_document_reference.document_version_id",
                "assertion_document_reference.tenant_id",
                "assertion_document_reference.knowledge_base_id",
            ],
            name="fk_assertion_name_reference",
        ),
    )

    document_version_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    normalized_name: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_ref: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AssertionSemantics(Base):
    __tablename__ = "assertion_semantics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["assertion_id", "tenant_id", "knowledge_base_id"],
            ["assertion.id", "assertion.tenant_id", "assertion.knowledge_base_id"],
            name="fk_assertion_semantics_owner",
        ),
        ForeignKeyConstraint(
            ["document_version_id", "tenant_id", "knowledge_base_id"],
            [
                "document_version.id",
                "document_version.tenant_id",
                "document_version.knowledge_base_id",
            ],
            name="fk_assertion_semantics_document",
        ),
        ForeignKeyConstraint(
            ["subject_ref", "document_version_id", "tenant_id", "knowledge_base_id"],
            [
                "assertion_document_reference.id",
                "assertion_document_reference.document_version_id",
                "assertion_document_reference.tenant_id",
                "assertion_document_reference.knowledge_base_id",
            ],
            name="fk_assertion_semantics_subject",
        ),
        ForeignKeyConstraint(
            ["object_ref", "document_version_id", "tenant_id", "knowledge_base_id"],
            [
                "assertion_document_reference.id",
                "assertion_document_reference.document_version_id",
                "assertion_document_reference.tenant_id",
                "assertion_document_reference.knowledge_base_id",
            ],
            name="fk_assertion_semantics_object",
        ),
        CheckConstraint(
            "assertion_kind IN ('OPEN_STATEMENT','TYPED_ASSERTION')", name="ck_assertion_kind"
        ),
        CheckConstraint("fact_mode IN ('ASSERTED','OBSERVED','DERIVED')", name="ck_assertion_mode"),
        Index("ix_assertion_semantics_subject", "tenant_id", "knowledge_base_id", "subject_ref"),
        Index(
            "ix_assertion_semantics_document",
            "tenant_id",
            "knowledge_base_id",
            "document_version_id",
        ),
    )

    assertion_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    subject_ref: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    object_ref: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    assertion_kind: Mapped[str] = mapped_column(Text, nullable=False)
    fact_mode: Mapped[str] = mapped_column(Text, nullable=False)
    assertion_origin: Mapped[str] = mapped_column(Text, nullable=False)
    predicate_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ontology_release: Mapped[str | None] = mapped_column(Text, nullable=True)
    record: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    entity_snapshots: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    verified_evidence: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    time_reference_snapshot: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    raw_item_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    admission_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
