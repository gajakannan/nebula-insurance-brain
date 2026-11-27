"""F0008 `fact-temporal/v1` domain contract (Proposed ADR-0078).

Pure value types only: no I/O and no clock. Zone-aware arithmetic lives in
`brain_temporal.bounds`; this module defines the shapes the commit service,
the repository and the reader exchange.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

TEMPORAL_CONTRACT = "fact-temporal/v1"
TEMPORAL_CONTRACT_VERSION = 1


class Granularity(StrEnum):
    YEAR = "YEAR"
    QUARTER = "QUARTER"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"


class EndState(StrEnum):
    OPEN = "OPEN"
    BOUNDED = "BOUNDED"
    UNKNOWN = "UNKNOWN"


class StartBasis(StrEnum):
    TEMPLATE_FIELD = "TEMPLATE_FIELD"
    HUMAN = "HUMAN"
    MENTION_A = "MENTION_A"
    MENTION_B = "MENTION_B"
    MENTION_C = "MENTION_C"
    ATTESTATION_FLOOR = "ATTESTATION_FLOOR"


# G1 decision 1 and ADR-0064 §7: these starts may not close or split a predecessor.
UNANCHORED_BASES = frozenset({StartBasis.MENTION_C, StartBasis.ATTESTATION_FLOOR})
CALLER_BASES = frozenset(StartBasis) - {StartBasis.ATTESTATION_FLOOR}


class TemporalKind(StrEnum):
    STATE = "STATE"
    EVENT = "EVENT"
    ETERNAL = "ETERNAL"


class DatePrecision(StrEnum):
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"


class TemporalReason(StrEnum):
    """Wire forms of the ADR-0078 refusal codes (422 problem `code`)."""

    TEMPORAL_FIELDS_REQUIRED = "temporal_fields_required"
    GRANULARITY_INVALID = "granularity_invalid"
    TIME_ZONE_INVALID = "time_zone_invalid"
    BOUND_NOT_TRUNCATED = "bound_not_truncated"
    END_STATE_INVALID = "end_state_invalid"
    START_UNATTESTED = "start_unattested"
    ATTESTATION_MISMATCH = "attestation_mismatch"
    START_BASIS_INVALID = "start_basis_invalid"
    SUCCESSION_START_UNANCHORED = "succession_start_unanchored"
    STATE_SUPERSESSION_REFUSED = "state_supersession_refused"
    # F0012 (ADR-0081 D7): the request shape does not match the predicate's kind,
    # or a SINGLE ETERNAL slot already holds another value.
    KIND_SHAPE_MISMATCH = "kind_shape_mismatch"
    ETERNAL_CONFLICT = "eternal_conflict"


class TemporalRejected(Exception):
    """A temporal refusal. It is raised before any effect, carries no detail
    text, and the API returns it as a 422 with `code` only."""

    def __init__(self, code: TemporalReason) -> None:
        super().__init__(code.value)
        self.code = code


@dataclass(frozen=True, slots=True)
class Bound:
    """One valid-time bound: an instant, its granularity, and the IANA zone the
    granularity is truncated in (ADR-0078 D2)."""

    instant: datetime
    granularity: Granularity
    zone: str

    def __post_init__(self) -> None:
        if self.instant.tzinfo is None:
            raise ValueError("a bound instant must be timezone-aware")


@dataclass(frozen=True, slots=True, order=True)
class DocumentDate:
    """An F0004 document date at its own precision (`YYYY`, `YYYY-MM` or
    `YYYY-MM-DD`). Its period is the calendar year, month or day it names."""

    value: str
    precision: DatePrecision

    def __post_init__(self) -> None:
        object.__setattr__(self, "precision", DatePrecision(self.precision))
        expected = {DatePrecision.YEAR: 4, DatePrecision.MONTH: 7, DatePrecision.DAY: 10}
        if len(self.value) != expected[self.precision]:
            raise ValueError(f"document date {self.value!r} does not match {self.precision}")
        self.first_day()  # validates the calendar value

    def first_day(self) -> date:
        parts = [int(p) for p in self.value.split("-")]
        return date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)

    def next_first_day(self) -> date:
        """The first calendar day after this date's period (exclusive end)."""
        start = self.first_day()
        if self.precision is DatePrecision.YEAR:
            return date(start.year + 1, 1, 1)
        if self.precision is DatePrecision.MONTH:
            return date(start.year + (start.month == 12), start.month % 12 + 1, 1)
        return date.fromordinal(start.toordinal() + 1)

    @property
    def granularity(self) -> Granularity:
        return Granularity(self.precision.value)

    def to_json(self) -> dict[str, str]:
        return {"value": self.value, "precision": self.precision.value}


@dataclass(frozen=True, slots=True)
class ExpectedAttestation:
    """The caller's optional echo of the derived attestation (S0002 AC6). Only
    the keys the caller sent are compared."""

    values: Mapping[str, DocumentDate | None]


@dataclass(frozen=True, slots=True)
class TemporalProposal:
    """A parsed `fact-temporal/v1` commit block."""

    valid_from: Bound | None
    valid_from_basis: StartBasis | None
    valid_to_state: EndState
    valid_to: Bound | None
    attestation_zone: str | None
    ending_evidence_refs: tuple[UUID, ...]
    expected_attestation: ExpectedAttestation | None


@dataclass(frozen=True, slots=True)
class VersionTemporal:
    """The temporal columns of one temporal-v1 version row."""

    kind: TemporalKind
    valid_from: Bound | None
    valid_from_basis: StartBasis | None
    valid_to_state: EndState
    valid_to: Bound | None
    attested_from: DocumentDate | None
    attested_through: DocumentDate | None
    attested_to: DocumentDate | None
    validity_unknown_from: datetime | None
    split_of_version_id: UUID | None

    def to_json(self) -> dict[str, object]:
        def bound(b: Bound | None) -> dict[str, str] | None:
            if b is None:
                return None
            return {
                "instant": b.instant.isoformat(),
                "granularity": b.granularity.value,
                "zone": b.zone,
            }

        def doc(d: DocumentDate | None) -> dict[str, str] | None:
            return d.to_json() if d is not None else None

        return {
            "contract": TEMPORAL_CONTRACT,
            "temporal_kind": self.kind.value,
            "valid_from": bound(self.valid_from),
            "valid_from_basis": self.valid_from_basis.value if self.valid_from_basis else None,
            "valid_to_state": self.valid_to_state.value,
            "valid_to": bound(self.valid_to),
            "attested_from": doc(self.attested_from),
            "attested_through": doc(self.attested_through),
            "attested_to": doc(self.attested_to),
            "validity_unknown_from": (
                self.validity_unknown_from.isoformat() if self.validity_unknown_from else None
            ),
            "split_of_version_id": (
                str(self.split_of_version_id) if self.split_of_version_id else None
            ),
        }
