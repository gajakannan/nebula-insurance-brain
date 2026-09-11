from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB, TSTZRANGE, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from brain_persistence.base import Base

_JSONVariant = JSONB().with_variant(JSON(), "sqlite")
_UUIDVariant = Uuid(as_uuid=True)
# tstzrange has no portable sqlite equivalent; brain-temporal's Postgres-only models
# (FactSlot, CanonicalFactVersion, CanonicalFactChange, OutboxEvent) are exercised
# against the real compose Postgres, not the sqlite fixture the other packages share
# (F0001-S0005 — the exclusion constraint IS the thing being proven).


class SourceDocument(Base):
    """One logical document per (tenant, knowledge base, source hash) — the identity
    the "no reparse" check (F0001-S0003 logic flow step 1) looks up by."""

    __tablename__ = "source_document"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "knowledge_base_id", "source_sha256", name="uq_source_document_identity"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    source_sha256: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    versions: Mapped[list[DocumentVersion]] = relationship(back_populates="source_document")


class DocumentVersion(Base):
    """A parse of `SourceDocument` at a point in time. F0001-S0003 creates exactly one
    version per source; later features (F0009/F0010) add re-upload/replacement versions."""

    __tablename__ = "document_version"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_document.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    source_document: Mapped[SourceDocument] = relationship(back_populates="versions")
    artifact: Mapped[ContentArtifact | None] = relationship(back_populates="document_version")


class ContentArtifact(Base):
    """Metadata row for a bundle persisted through `ContentArtifactStore`
    (`brain_content`); the bundle bytes themselves live in the object store, not here."""

    __tablename__ = "content_artifact"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)  # == artifact_id
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_version.id"), unique=True, nullable=False
    )
    artifact_sha256: Mapped[str] = mapped_column(nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    extraction_status: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document_version: Mapped[DocumentVersion] = relationship(back_populates="artifact")
    runs: Mapped[list[SemanticInterpretationRun]] = relationship(back_populates="artifact")


class SemanticInterpretationRun(Base):
    """Append-only record of one `interpret()` call. Never deleted or overwritten
    (F0001-S0003 logic flow step 5)."""

    __tablename__ = "semantic_interpretation_run"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)  # == run_id
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_artifact.id"), nullable=False
    )
    profile_id: Mapped[str] = mapped_column(nullable=False)
    profile_version: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    counters: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    run_configuration: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    artifact: Mapped[ContentArtifact] = relationship(back_populates="runs")
    assertions: Mapped[list[Assertion]] = relationship(back_populates="run")


class Assertion(Base):
    """One `CandidateAssertion`. Either produced by an interpretation run
    (`origin=MACHINE_EXTRACTION`, `run_id` set) or by a review correction
    (`origin=HUMAN_REVIEW`, `run_id` null, `original_assertion_id` set — ADR-0037:
    corrections append and never rewrite the original, F0001-S0004)."""

    __tablename__ = "assertion"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("semantic_interpretation_run.id"), nullable=True
    )
    origin: Mapped[str] = mapped_column(nullable=False, default="MACHINE_EXTRACTION")
    original_assertion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assertion.id"), nullable=True
    )
    # Proof-scope version counter for the F0001-S0004 staleness check ("the assertion is
    # superseded (version N+1) between batch assembly and submission"). F0007/F0008's
    # bitemporal FactSlot/CanonicalFactVersion model is the real versioning authority;
    # this column is retired when review items route against FactSlots instead.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    subject_type: Mapped[str] = mapped_column(nullable=False)
    slot_type: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    model_confidence: Mapped[float | None] = mapped_column(nullable=True)
    interpretation_basis: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    run: Mapped[SemanticInterpretationRun | None] = relationship(back_populates="assertions")
    evidence: Mapped[list[AssertionEvidence]] = relationship(back_populates="assertion")


class AssertionEvidence(Base):
    """One `EvidenceBinding` for an `Assertion`. An assertion may cite more than one
    evidence locator (F0001-S0003 Data Requirements: amount, currency, limit basis,
    and effective date are stored separately when they occur in different regions)."""

    __tablename__ = "assertion_evidence"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assertion.id"), nullable=False)
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_artifact.id"), nullable=False
    )
    block_id: Mapped[str | None] = mapped_column(nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    precision: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    assertion: Mapped[Assertion] = relationship(back_populates="evidence")


class PrincipalRow(Base):
    """Persistence row for `brain_domain.principal.Principal` (F0001-S0006)."""

    __tablename__ = "principal"
    __table_args__ = (UniqueConstraint("issuer", "subject", name="uq_principal_issuer_subject"),)

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(nullable=False)
    issuer: Mapped[str] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MembershipRow(Base):
    """Persistence row for `brain_domain.principal.Membership` (F0001-S0006)."""

    __tablename__ = "membership"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    grant_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AuditEventRow(Base):
    """Append-only persistence row for `brain_domain.audit.AuditEvent` (F0001-S0006)."""

    __tablename__ = "audit_event"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now())
    actor_principal_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    delegate_principal_id: Mapped[uuid.UUID | None] = mapped_column(_UUIDVariant, nullable=True)
    resource_type: Mapped[str] = mapped_column(nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    action: Mapped[str] = mapped_column(nullable=False)
    decision: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason_code: Mapped[str] = mapped_column(nullable=False)
    policy_hash: Mapped[str] = mapped_column(nullable=False)
    grant_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    trace_id: Mapped[str] = mapped_column(nullable=False)


class ReviewItemRow(Base):
    """Persistence row for `brain_domain.review.ReviewItem` (F0001-S0004)."""

    __tablename__ = "review_item"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assertion.id"), nullable=False)
    assertion_version: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    review_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("review_batch.id"), nullable=True
    )
    evidence: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    decisions: Mapped[list[ReviewDecisionRow]] = relationship(back_populates="review_item")


class ReviewBatchRow(Base):
    """Persistence row for `brain_domain.review.ReviewBatch` (F0001-S0004)."""

    __tablename__ = "review_batch"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    assembled_at: Mapped[datetime] = mapped_column(server_default=func.now())
    assembling_principal_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class ReviewDecisionRow(Base):
    """Persistence row for `brain_domain.review.ReviewDecision` (F0001-S0004). One row
    per review item per submission attempt is prevented at the application layer via
    `event_sha256` uniqueness per review item — never deleted or overwritten."""

    __tablename__ = "review_decision"
    __table_args__ = (
        UniqueConstraint("review_item_id", "event_sha256", name="uq_review_decision_item_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    review_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_item.id"), nullable=False)
    review_batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_batch.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(nullable=False)
    reason_code: Mapped[str | None] = mapped_column(nullable=True)
    corrected_value: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    corrected_assertion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assertion.id"), nullable=True
    )
    evidence: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    reviewer_principal_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    reviewer_comment: Mapped[str | None] = mapped_column(nullable=True)
    decided_at: Mapped[datetime] = mapped_column(server_default=func.now())
    assertion_version: Mapped[int] = mapped_column(Integer, nullable=False)
    stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    event_sha256: Mapped[str] = mapped_column(nullable=False)

    review_item: Mapped[ReviewItemRow] = relationship(back_populates="decisions")


class FactSlotRow(Base):
    """Persistence row for `brain_domain.facts.FactSlot` (F0001-S0005)."""

    __tablename__ = "fact_slot"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    slot_type: Mapped[str] = mapped_column(nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CanonicalFactVersionRow(Base):
    """Persistence row for one bitemporal fact version (F0001-S0005, master
    blueprint section 109.2). The `EXCLUDE USING gist` constraint is the database-
    level temporal-integrity guarantee (ADR-0008) — two rows for the same slot can
    never carry overlapping `valid` AND overlapping `recorded` ranges at once."""

    __tablename__ = "canonical_fact_version"
    __table_args__ = (
        ExcludeConstraint(
            ("slot_id", "="),
            ("valid", "&&"),
            ("recorded", "&&"),
            using="gist",
            name="excl_canonical_fact_version_slot_valid_recorded",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fact_slot.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    value: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    valid = mapped_column(TSTZRANGE, nullable=False)
    recorded = mapped_column(TSTZRANGE, nullable=False)
    change_reason: Mapped[str | None] = mapped_column(nullable=True)
    evidence: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    review_decision_id: Mapped[uuid.UUID | None] = mapped_column(_UUIDVariant, nullable=True)
    commit_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    # Explicit `timezone=True`: these are populated with tz-aware `datetime`s by
    # `CanonicalCommitService`/the API, unlike the `server_default=func.now()`
    # columns elsewhere that never round-trip a Python-side value.
    source_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    artifact_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assertion_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    canonical_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CanonicalFactChangeRow(Base):
    """Persistence row linking a superseded version to the version that replaced
    it, with why (F0001-S0005; ADR-0009: 'every ended fact records why it ended')."""

    __tablename__ = "canonical_fact_change"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    reason: Mapped[str] = mapped_column(nullable=False)
    from_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("canonical_fact_version.id"), nullable=True
    )
    to_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("canonical_fact_version.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class OutboxEventRow(Base):
    """Append-only outbox row written in the same transaction as its commit
    (F0001-S0005 logic flow step 5); `processed_at` is the projector's watermark."""

    __tablename__ = "outbox_event"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    commit_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    payload: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
