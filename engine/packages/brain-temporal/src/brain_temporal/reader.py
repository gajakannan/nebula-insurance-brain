"""Two-coordinate fact resolution (ADR-0078 D9, F0008-S0006).

Authorization is not decided here. The GET route runs `resolve` as the `load`
of `AuthorizationExecution.read`, under current grants (ADR-0053).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from brain_domain.facts import FactVersion
from brain_domain.temporal import EndState, StartBasis, VersionTemporal


@dataclass(frozen=True, slots=True)
class Resolved:
    version: FactVersion


@dataclass(frozen=True, slots=True)
class ValidityUnknown:
    """No value is disclosed: the coordinate is inside an unknown-end window or
    before an attestation-floor start (S0006 AC3)."""

    version: FactVersion
    reason: Literal["UNKNOWN_END_WINDOW", "BEFORE_ATTESTATION_FLOOR"]

    @property
    def version_id(self) -> UUID:
        return self.version.id

    @property
    def temporal(self) -> VersionTemporal:
        assert self.version.temporal is not None
        return self.version.temporal


@dataclass(frozen=True, slots=True)
class NotProcessed:
    """Identity-v1 slot with no recorded version at the coordinate (S0006 AC2)."""


Resolution = Resolved | ValidityUnknown | NotProcessed | None


class TemporalReadRepository(Protocol):
    async def slot_identity_version(self, slot_id: UUID) -> int | None: ...

    async def resolve_at(
        self, slot_id: UUID, *, valid_as_of: datetime, known_as_of: datetime
    ) -> FactVersion | None: ...

    async def next_version_after(
        self, slot_id: UUID, *, valid_after: datetime, known_as_of: datetime
    ) -> FactVersion | None:
        """The version visible at `known_as_of` with the smallest `lower(valid)`
        strictly greater than `valid_after`."""
        ...


class TemporalFactReader:
    def __init__(self, repository: TemporalReadRepository) -> None:
        self._repository = repository

    async def resolve(self, slot_id: UUID, *, valid_at: datetime, known_at: datetime) -> Resolution:
        version = await self._repository.resolve_at(
            slot_id, valid_as_of=valid_at, known_as_of=known_at
        )
        if version is not None:
            temporal = version.temporal
            if (
                temporal is not None
                and temporal.valid_to_state is EndState.UNKNOWN
                and temporal.validity_unknown_from is not None
                and valid_at >= temporal.validity_unknown_from
            ):
                return ValidityUnknown(version, "UNKNOWN_END_WINDOW")
            return Resolved(version)

        later = await self._repository.next_version_after(
            slot_id, valid_after=valid_at, known_as_of=known_at
        )
        if (
            later is not None
            and later.temporal is not None
            and later.temporal.valid_from_basis is StartBasis.ATTESTATION_FLOOR
        ):
            return ValidityUnknown(later, "BEFORE_ATTESTATION_FLOOR")

        if await self._repository.slot_identity_version(slot_id) is not None:
            return NotProcessed()
        return None
