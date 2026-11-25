"""Application ports for the F0009 provenance reader (no SQL, content or model I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from brain_domain.authx import ResourceKey
from brain_domain.provenance import ProvenanceQuery, ProvenanceResult, RecordRef


@dataclass(frozen=True, slots=True)
class ProvenancePlan:
    """Metadata-only closure of one exact root: identities, ownership, the READ
    requirements of every linked resource and a topology fingerprint. It holds no
    protected payload (assembly plan Step 4.2)."""

    root: RecordRef
    anchor: ResourceKey
    tenant_id: UUID
    knowledge_base_id: UUID
    record_refs: tuple[RecordRef, ...]
    source_keys: tuple[ResourceKey, ...]
    metadata_fingerprint: str


class ProvenanceRepository(Protocol):
    async def discover(self, query: ProvenanceQuery) -> ProvenancePlan:
        """Column-only discovery. Raises LineageNotFound for a bad association,
        dangling protected target or owner mismatch, and LineageUnavailable for a
        cycle or exceeded limit. Never commits."""
        ...

    async def materialize(self, plan: ProvenancePlan) -> ProvenanceResult:
        """Re-discover under share locks, refuse a changed topology, then load
        exactly the planned rows. Never commits, parses or calls a model."""
        ...
