"""F0009 append-only lineage rows; migration 0016 owns the database guards."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from brain_persistence.base import Base
from brain_persistence.models import _JSONVariant


class LearningCandidateReservationRow(Base):
    """One reserved future-learning identity per new effective correction (S0005)."""

    __tablename__ = "learning_candidate_reservation"
    __table_args__ = (
        UniqueConstraint("review_decision_id", name="uq_f0009_reservation_decision"),
        UniqueConstraint("corrected_assertion_id", name="uq_f0009_reservation_child"),
        UniqueConstraint("id", "tenant_id", "knowledge_base_id", name="uq_f0009_reservation_owner"),
        ForeignKeyConstraint(
            ["review_decision_id", "tenant_id", "knowledge_base_id"],
            [
                "review_decision.id",
                "review_decision.tenant_id",
                "review_decision.knowledge_base_id",
            ],
            name="fk_f0009_reservation_decision",
        ),
        ForeignKeyConstraint(
            ["original_assertion_id", "tenant_id", "knowledge_base_id"],
            ["assertion.id", "assertion.tenant_id", "assertion.knowledge_base_id"],
            name="fk_f0009_reservation_original",
        ),
        ForeignKeyConstraint(
            ["corrected_assertion_id", "tenant_id", "knowledge_base_id"],
            ["assertion.id", "assertion.tenant_id", "assertion.knowledge_base_id"],
            name="fk_f0009_reservation_child",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    review_decision_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_assertion_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    corrected_assertion_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    reviewer_principal_id: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReviewSubmissionAttemptRow(Base):
    """Protected, non-applied review submission (S0002 AC6). Never an accepted decision."""

    __tablename__ = "review_submission_attempt"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", "knowledge_base_id", name="uq_f0009_attempt_owner"),
        UniqueConstraint(
            "review_item_id", "event_sha256", "outcome", name="uq_f0009_attempt_event_outcome"
        ),
        ForeignKeyConstraint(
            ["review_item_id", "tenant_id", "knowledge_base_id"],
            ["review_item.id", "review_item.tenant_id", "review_item.knowledge_base_id"],
            name="fk_f0009_attempt_item",
        ),
        ForeignKeyConstraint(
            ["review_batch_id", "tenant_id", "knowledge_base_id"],
            ["review_batch.id", "review_batch.tenant_id", "review_batch.knowledge_base_id"],
            name="fk_f0009_attempt_batch",
        ),
        ForeignKeyConstraint(
            ["original_assertion_id", "tenant_id", "knowledge_base_id"],
            ["assertion.id", "assertion.tenant_id", "assertion.knowledge_base_id"],
            name="fk_f0009_attempt_original",
        ),
        CheckConstraint("assertion_version > 0", name="ck_f0009_attempt_version"),
        CheckConstraint(
            "outcome IN ('ALREADY_DECIDED','BATCH_REFUSED')", name="ck_f0009_attempt_outcome"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    knowledge_base_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    review_item_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    review_batch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_assertion_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    reviewer_principal_id: Mapped[UUID] = mapped_column(ForeignKey("principal.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    assertion_version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    reason_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    authorization_decision_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
