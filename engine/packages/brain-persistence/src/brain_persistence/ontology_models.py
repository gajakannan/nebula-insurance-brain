"""F0012 append-only ontology release rows; migration 0017 owns the database guards.

Composite owner keys are declared here as well as in the migration so a
`metadata.create_all()` schema (recovery suites) accepts the composite FKs. The
`knowledge_base(id, tenant_id)` FKs exist only in the migration.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from brain_persistence.base import Base
from brain_persistence.models import _JSONVariant

_TSZ = DateTime(timezone=True)
# text[] in PostgreSQL; JSON in SQLite create_all schemas (neuron recovery suite).
_TEXT_ARRAY = ARRAY(Text).with_variant(JSON(), "sqlite")


def _owner_fk(columns: list[str], table: str, name: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        [*columns, "tenant_id", "knowledge_base_id"],
        [f"{table}.id", f"{table}.tenant_id", f"{table}.knowledge_base_id"],
        name=name,
    )


class OntologyModuleVersionRow(Base):
    __tablename__ = "ontology_module_version"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "module_id", "version", name="uq_f0012_module_version"
        ),
        UniqueConstraint(
            "id", "tenant_id", "knowledge_base_id", name="uq_f0012_module_version_owner"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    module_id: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_digest: Mapped[str] = mapped_column(Text, nullable=False)
    authoring_schema: Mapped[str] = mapped_column(Text, nullable=False)
    normalized: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TSZ, nullable=False)


class OntologyReleaseRow(Base):
    __tablename__ = "ontology_release"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "release_ref", name="uq_f0012_release_ref"
        ),
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "name", "sequence", name="uq_f0012_release_name_seq"
        ),
        UniqueConstraint("id", "tenant_id", "knowledge_base_id", name="uq_f0012_release_owner"),
        CheckConstraint(
            "release_ref = 'ontrel:sha256-' || manifest_digest", name="ck_f0012_release_ref_digest"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    release_ref: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_digest: Mapped[str] = mapped_column(Text, nullable=False)
    manifest: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    installed_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(_TSZ, nullable=False)


class OntologyReleaseModuleRow(Base):
    __tablename__ = "ontology_release_module"
    __table_args__ = (
        PrimaryKeyConstraint("release_id", "module_id"),
        _owner_fk(["release_id"], "ontology_release", "fk_f0012_rm_release"),
        _owner_fk(["module_version_id"], "ontology_module_version", "fk_f0012_rm_module"),
    )

    release_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    module_version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    module_id: Mapped[str] = mapped_column(Text, nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class OntologyTermRow(Base):
    __tablename__ = "ontology_term"
    __table_args__ = (
        PrimaryKeyConstraint("release_id", "term_iri"),
        UniqueConstraint("release_id", "predicate_key", name="uq_f0012_term_predicate"),
        _owner_fk(["release_id"], "ontology_release", "fk_f0012_term_release"),
    )

    release_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    term_iri: Mapped[str] = mapped_column(Text, nullable=False)
    term_kind: Mapped[str] = mapped_column(Text, nullable=False)
    definition_digest: Mapped[str] = mapped_column(Text, nullable=False)
    normalized: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    predicate_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    cardinality: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    temporal_kind: Mapped[str | None] = mapped_column(Text, nullable=True)


class OntologyChangeRecordRow(Base):
    __tablename__ = "ontology_change_record"
    __table_args__ = (_owner_fk(["release_id"], "ontology_release", "fk_f0012_change_release"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    release_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    change_class: Mapped[str] = mapped_column(Text, nullable=False)
    source_iris: Mapped[list[str]] = mapped_column(_TEXT_ARRAY, nullable=False)
    replacement_iris: Mapped[list[str]] = mapped_column(_TEXT_ARRAY, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)


class OntologyImpactReportRow(Base):
    __tablename__ = "ontology_impact_report"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "report_digest", name="uq_f0012_report_digest"
        ),
        UniqueConstraint("id", "tenant_id", "knowledge_base_id", name="uq_f0012_report_owner"),
        _owner_fk(["predecessor_release_id"], "ontology_release", "fk_f0012_report_pred"),
        _owner_fk(["candidate_release_id"], "ontology_release", "fk_f0012_report_cand"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    predecessor_release_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    candidate_release_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    report_digest: Mapped[str] = mapped_column(Text, nullable=False)
    report: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    generated_by: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(_TSZ, nullable=False)


class OntologyReleaseReviewRow(Base):
    __tablename__ = "ontology_release_review"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", "knowledge_base_id", name="uq_f0012_review_owner"),
        _owner_fk(["report_id"], "ontology_impact_report", "fk_f0012_review_report"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    report_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_principal_id: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    decision_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(_TSZ, nullable=False)


class OntologyReleaseSelectionRow(Base):
    __tablename__ = "ontology_release_selection"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "sequence", name="uq_f0012_selection_seq"
        ),
        CheckConstraint(
            "(action = 'activate') = (review_id IS NOT NULL)", name="ck_f0012_selection_review"
        ),
        _owner_fk(["release_id"], "ontology_release", "fk_f0012_selection_release"),
        _owner_fk(["review_id"], "ontology_release_review", "fk_f0012_selection_review"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    release_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    review_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    actor_principal_id: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    decision_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(_TSZ, nullable=False)
