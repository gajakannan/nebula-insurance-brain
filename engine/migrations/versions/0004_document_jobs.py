"""Fenced document jobs and a completion outbox.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_job",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("knowledge_base_id", sa.String(36), nullable=False),
        sa.Column("artifact_id", sa.String(36), nullable=False),
        sa.Column("request_key", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.Float(), nullable=False),
        sa.Column("leased_until", sa.Float(), nullable=False),
        sa.Column("result_ref", sa.String(), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "knowledge_base_id", "request_key", name="uq_document_job_request"
        ),
    )
    op.create_table(
        "document_artifact_lease",
        sa.Column("artifact_id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("knowledge_base_id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=True),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("leased_until", sa.Float(), nullable=False),
    )
    op.create_table(
        "document_job_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.Float(), nullable=False),
    )
    op.create_table(
        "document_job_outbox",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("knowledge_base_id", sa.String(36), nullable=False),
        sa.Column("result_ref", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("delivered_at", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    for name in (
        "document_job_outbox",
        "document_job_event",
        "document_artifact_lease",
        "document_job",
    ):
        op.drop_table(name)
