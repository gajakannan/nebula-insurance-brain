"""Attestation derivation and placement (ADR-0078 D3/D4).

Dates come only from the current F0004 date selection of each evidence
document version. Upload, receipt, artifact, assertion and acceptance times are
never consulted (ADR-0064 §8).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from brain_domain.temporal import (
    Bound,
    DocumentDate,
    EndState,
    StartBasis,
    TemporalProposal,
    TemporalReason,
    TemporalRejected,
)

from brain_temporal.bounds import date_period_end, date_period_start, period_end


@dataclass(frozen=True, slots=True)
class Attestation:
    attested_from: DocumentDate | None
    attested_through: DocumentDate | None
    attested_to: DocumentDate | None

    def as_mapping(self) -> dict[str, DocumentDate | None]:
        return {
            "attested_from": self.attested_from,
            "attested_through": self.attested_through,
            "attested_to": self.attested_to,
        }


def _period_key(value: DocumentDate) -> tuple[object, object]:
    return (value.first_day(), value.next_first_day())


def derive_attestation(
    positive: Iterable[DocumentDate | None], ending: Iterable[DocumentDate | None]
) -> Attestation:
    """`attested_from` is the date whose period starts earliest among the
    positive evidence, `attested_through` the one whose period ends latest, and
    `attested_to` the earliest among the ending evidence. Undated documents
    contribute nothing."""
    dated = [d for d in positive if d is not None]
    ended = [d for d in ending if d is not None]
    return Attestation(
        attested_from=min(dated, key=lambda d: (d.first_day(), d.next_first_day()))
        if dated
        else None,
        attested_through=max(dated, key=lambda d: (d.next_first_day(), d.first_day()))
        if dated
        else None,
        attested_to=min(ended, key=_period_key) if ended else None,
    )


def check_expected(proposal: TemporalProposal, derived: Attestation) -> None:
    """S0002 AC6: a caller-supplied value that disagrees is refused."""
    if proposal.expected_attestation is None:
        return
    actual: Mapping[str, DocumentDate | None] = derived.as_mapping()
    for key, expected in proposal.expected_attestation.values.items():
        if actual[key] != expected:
            raise TemporalRejected(TemporalReason.ATTESTATION_MISMATCH)


@dataclass(frozen=True, slots=True)
class Placement:
    """The integrity range of a new temporal-v1 version and its stored bounds."""

    start: Bound
    basis: StartBasis
    end_state: EndState
    end: Bound | None
    validity_unknown_from: datetime | None


def place(proposal: TemporalProposal, attestation: Attestation) -> Placement:
    """Resolve the unknown start (S0002 AC4/AC5) and the unknown end (D3)."""
    if proposal.valid_from is not None:
        assert proposal.valid_from_basis is not None
        start, basis = proposal.valid_from, proposal.valid_from_basis
    else:
        if attestation.attested_from is None or proposal.attestation_zone is None:
            raise TemporalRejected(TemporalReason.START_UNATTESTED)
        floor = attestation.attested_from
        start = Bound(
            date_period_start(floor, proposal.attestation_zone),
            floor.granularity,
            proposal.attestation_zone,
        )
        basis = StartBasis.ATTESTATION_FLOOR

    match proposal.valid_to_state:
        case EndState.OPEN:
            return Placement(start, basis, EndState.OPEN, None, None)
        case EndState.BOUNDED:
            assert proposal.valid_to is not None
            if proposal.valid_to.instant <= start.instant:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
            return Placement(start, basis, EndState.BOUNDED, proposal.valid_to, None)
        case EndState.UNKNOWN:
            zone = proposal.attestation_zone
            if attestation.attested_to is None or zone is None:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
            ended = attestation.attested_to
            end = Bound(date_period_end(ended, zone), ended.granularity, zone)
            unknown_from = period_end(start.instant, start.granularity, start.zone)
            if attestation.attested_through is not None:
                unknown_from = max(
                    unknown_from, date_period_end(attestation.attested_through, zone)
                )
            if unknown_from >= end.instant:
                # The latest positive evidence postdates the ending document.
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
            return Placement(start, basis, EndState.UNKNOWN, end, unknown_from)


def ordered_refs(*groups: Iterable[UUID]) -> tuple[UUID, ...]:
    return tuple(dict.fromkeys(ref for group in groups for ref in group))
