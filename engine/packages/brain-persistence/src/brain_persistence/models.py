from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
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
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # F0002 complete grant slice. No defaults: restrictions come only from trusted
    # provisioning or a reviewed reconciliation mapping (0006 enforces NOT NULL).
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    selectors: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    classifications: Mapped[object] = mapped_column(_JSONVariant, nullable=False)
    source_acl_ids: Mapped[object] = mapped_column(_JSONVariant, nullable=False)


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
    # F0002 v1 additions; null on every pre-existing (never rewritten) row.
    decision_id: Mapped[uuid.UUID | None] = mapped_column(_UUIDVariant, nullable=True)
    event_type: Mapped[str | None] = mapped_column(nullable=True)
    operation_outcome: Mapped[str | None] = mapped_column(nullable=True)
    payload: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)


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
    # Review batches are single-KB in v1 (assembly plan Step 1); an existing
    # mixed-KB batch blocks backfill rather than being split silently.
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)

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
    # Explicit structural ownership (F0002-S0001, ADR-0061). The composite
    # foreign keys to the parent's (id, tenant_id, knowledge_base_id) live in
    # migrations 0005/0006 — the database is the enforcement point.
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class OutboxEventRow(Base):
    """Append-only outbox row written in the same transaction as its commit
    (F0001-S0005 logic flow step 5); `processed_at` is the projector's watermark."""

    __tablename__ = "outbox_event"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True, default=uuid.uuid4)
    # Ownership comes from the commit's registry row (canonical_commit); existing
    # outbox IDs and payloads are preserved unchanged.
    commit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("canonical_commit.id"), nullable=False)
    payload: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- F0002 structural registries and security substrate (ADR-0061/0062) -------------
#
# Composite ownership keys (`unique(id, tenant_id[, knowledge_base_id])`) and the
# composite foreign keys that use them are declared in migrations 0005/0006 only;
# the ORM keeps single-column relationships so relationship() paths stay
# unambiguous. Every timestamp below is written from the injected trusted clock.

_TS = DateTime(timezone=True)


class TenantRow(Base):
    __tablename__ = "tenant"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class WorkspaceRow(Base):
    __tablename__ = "workspace"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class KnowledgeBaseRow(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspace.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class EntityIdentityRow(Base):
    """Tenant-scoped entity identity. `(namespace, external_key)` is unique only
    within a tenant, so an identical external identifier in another tenant can
    neither select nor reveal this entity (S0001 AC4). Full resolution is F0017."""

    __tablename__ = "entity_identity"
    __table_args__ = (
        PrimaryKeyConstraint("id", "tenant_id", name="pk_entity_identity"),
        UniqueConstraint(
            "tenant_id", "external_namespace", "external_key", name="uq_entity_external_key"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant.id"))
    external_namespace: Mapped[str | None] = mapped_column(nullable=True)
    external_key: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class EntityKnowledgeBaseRow(Base):
    """An explicit entity-to-KB association. It is identity, never a grant."""

    __tablename__ = "entity_knowledge_base"
    __table_args__ = (
        PrimaryKeyConstraint(
            "entity_id", "tenant_id", "knowledge_base_id", name="pk_entity_knowledge_base"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class ExternalIdentityRow(Base):
    """Authoritative verified `(issuer, subject)` alias of a stable principal.
    `linked_by`/`approval_ref` are null only for first verified self-provisioning."""

    __tablename__ = "external_identity"
    __table_args__ = (PrimaryKeyConstraint("issuer", "subject", name="pk_external_identity"),)

    issuer: Mapped[str] = mapped_column()
    subject: Mapped[str] = mapped_column()
    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    linked_by: Mapped[uuid.UUID | None] = mapped_column(_UUIDVariant, nullable=True)
    approval_ref: Mapped[str | None] = mapped_column(nullable=True)


class PrincipalAuthorityRow(Base):
    """Monotonic authority revision. Grant, status and restriction changes lock
    this row FOR UPDATE; evaluation locks it FOR SHARE."""

    __tablename__ = "principal_authority"
    __table_args__ = (CheckConstraint("revision >= 1", name="ck_principal_authority_revision"),)

    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principal.id"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)


class ResourceAccessRow(Base):
    """Security control metadata for one protected semantic record — not alternate
    semantic truth. Hydration verifies it against the record's own ownership."""

    __tablename__ = "resource_access"
    __table_args__ = (
        PrimaryKeyConstraint("resource_type", "resource_id", name="pk_resource_access"),
        CheckConstraint("revision >= 1", name="ck_resource_access_revision"),
    )

    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    parent_chain: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    classifications: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    source_acl_ids: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    dependency_keys: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class DelegationRow(Base):
    __tablename__ = "delegation"
    __table_args__ = (
        CheckConstraint("expires_at > not_before", name="ck_delegation_window"),
        CheckConstraint("revision >= 1", name="ck_delegation_revision"),
        CheckConstraint("acting_principal_id <> executor_principal_id", name="ck_delegation_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    acting_principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principal.id"), nullable=False
    )
    executor_principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principal.id"), nullable=False
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    not_before: Mapped[datetime] = mapped_column(_TS, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(_TS, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    ceilings: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    approval_ref: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)


class PolicyReleaseRow(Base):
    """Immutable identity of one model+policy+contract-version release."""

    __tablename__ = "policy_release"

    release_id: Mapped[str] = mapped_column(primary_key=True)
    release_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    model_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    contract_version: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)


class PolicyReleasePointerRow(Base):
    """Singleton current-release pointer; evaluation reads it FOR SHARE and a
    switch takes it FOR UPDATE (same lock protocol as grant changes)."""

    __tablename__ = "policy_release_pointer"
    __table_args__ = (CheckConstraint("id = 1", name="ck_policy_release_pointer_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    release_id: Mapped[str] = mapped_column(ForeignKey("policy_release.release_id"), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    activated_by: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)


class AuthenticationEventRow(Base):
    """Write-only sink for rejected credentials: no principal, no token, no payload."""

    __tablename__ = "authentication_event"

    event_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    reason_code: Mapped[str] = mapped_column(nullable=False)
    route_template: Mapped[str] = mapped_column(nullable=False)
    trace_id: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)


class CanonicalCommitRow(Base):
    """Commit ownership registry: links a commit (and its outbox rows) to one
    tenant/KB and to the authorization decision that permitted it."""

    __tablename__ = "canonical_commit"

    id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUIDVariant, nullable=False)
    authorization_decision_id: Mapped[uuid.UUID | None] = mapped_column(_UUIDVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
