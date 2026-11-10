"""F0007 `fact_slot_qualifier` mapping (migration 0012, ADR-0077 D1/D8).

Normalized qualifier rows are the authoritative slot identity; the fingerprint on
`fact_slot` only accelerates lookup. Rows are append-only and bound to their slot's
owner through a composite foreign key.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, PrimaryKeyConstraint, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from brain_persistence.base import Base

_UUID = Uuid(as_uuid=True)


class FactSlotQualifierRow(Base):
    __tablename__ = "fact_slot_qualifier"
    __table_args__ = (
        PrimaryKeyConstraint("slot_id", "qualifier_name", name="pk_fact_slot_qualifier"),
        ForeignKeyConstraint(
            ["slot_id", "tenant_id", "knowledge_base_id"],
            ["fact_slot.id", "fact_slot.tenant_id", "fact_slot.knowledge_base_id"],
            name="fk_fact_slot_qualifier_owner",
        ),
    )

    slot_id: Mapped[uuid.UUID] = mapped_column(_UUID, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(_UUID, nullable=False)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(_UUID, nullable=False)
    qualifier_name: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
