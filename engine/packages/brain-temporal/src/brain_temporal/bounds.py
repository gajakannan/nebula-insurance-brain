"""Zone-aware bound validation and parsing for `fact-temporal/v1` (ADR-0078 D2).

The service runs these checks to return reason codes early. The insert trigger
in migration 0014 repeats them against `pg_timezone_names` and `date_trunc`, and
the database is authoritative. The tzdata versions of both are recorded in the
feature run evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from brain_domain.temporal import (
    CALLER_BASES,
    TEMPORAL_CONTRACT,
    Bound,
    DatePrecision,
    DocumentDate,
    EndState,
    ExpectedAttestation,
    Granularity,
    StartBasis,
    TemporalProposal,
    TemporalReason,
    TemporalRejected,
)

from brain_temporal.ranges import InvalidRangeError

_ZONE_NAME_MAX = 64


def zone_info(name: object) -> ZoneInfo:
    """Return the zone, or refuse with `time_zone_invalid`. Only real IANA keys
    are accepted, never a file path or an abbreviation."""
    if not isinstance(name, str) or not name or len(name) > _ZONE_NAME_MAX:
        raise TemporalRejected(TemporalReason.TIME_ZONE_INVALID)
    if name not in _known_zones():
        raise TemporalRejected(TemporalReason.TIME_ZONE_INVALID)
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise TemporalRejected(TemporalReason.TIME_ZONE_INVALID) from exc


_ZONES: frozenset[str] | None = None


def _known_zones() -> frozenset[str]:
    global _ZONES
    if _ZONES is None:
        _ZONES = frozenset(available_timezones() | {"UTC"})
    return _ZONES


def _local_start(local: datetime, granularity: Granularity) -> datetime:
    match granularity:
        case Granularity.YEAR:
            return local.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        case Granularity.QUARTER:
            month = 3 * ((local.month - 1) // 3) + 1
            return local.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        case Granularity.MONTH:
            return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        case Granularity.DAY:
            return local.replace(hour=0, minute=0, second=0, microsecond=0)
        case Granularity.HOUR:
            return local.replace(minute=0, second=0, microsecond=0)
        case Granularity.MINUTE:
            return local.replace(second=0, microsecond=0)
        case Granularity.SECOND:
            return local.replace(microsecond=0)


def truncate(instant: datetime, granularity: Granularity, zone: str) -> datetime:
    """The start of the granularity period containing `instant`, computed on the
    zone's wall clock, as PostgreSQL `date_trunc(field, ts, zone)` does."""
    tz = zone_info(zone)
    local = instant.astimezone(tz).replace(tzinfo=None)
    start = _local_start(local, granularity)
    if granularity in (Granularity.HOUR, Granularity.MINUTE, Granularity.SECOND):
        # Sub-day truncation keeps the instant's own UTC offset, so the second
        # 01:30 of a DST fall-back hour stays distinct (date_trunc does the same).
        offset = instant.astimezone(tz).utcoffset()
        assert offset is not None
        return (start - offset).replace(tzinfo=UTC)
    return start.replace(tzinfo=tz).astimezone(UTC)


def period_end(instant: datetime, granularity: Granularity, zone: str) -> datetime:
    """The exclusive end of the granularity period that starts at `instant`."""
    tz = zone_info(zone)
    if granularity in (Granularity.HOUR, Granularity.MINUTE, Granularity.SECOND):
        step = {
            Granularity.HOUR: timedelta(hours=1),
            Granularity.MINUTE: timedelta(minutes=1),
            Granularity.SECOND: timedelta(seconds=1),
        }[granularity]
        return instant.astimezone(UTC) + step
    local = instant.astimezone(tz).replace(tzinfo=None)
    match granularity:
        case Granularity.YEAR:
            nxt = local.replace(year=local.year + 1)
        case Granularity.QUARTER | Granularity.MONTH:
            months = 3 if granularity is Granularity.QUARTER else 1
            index = local.month - 1 + months
            nxt = local.replace(year=local.year + index // 12, month=index % 12 + 1)
        case _:
            nxt = local + timedelta(days=1)
    return nxt.replace(tzinfo=tz).astimezone(UTC)


def validate_bound(bound: Bound) -> Bound:
    """S0001 AC1/AC2: a known zone and an instant truncated to its granularity."""
    zone_info(bound.zone)
    if truncate(bound.instant, bound.granularity, bound.zone) != bound.instant:
        raise TemporalRejected(TemporalReason.BOUND_NOT_TRUNCATED)
    return bound


def day_start(day: date, zone: str) -> datetime:
    return datetime.combine(day, time.min).replace(tzinfo=zone_info(zone)).astimezone(UTC)


def date_period_start(value: DocumentDate, zone: str) -> datetime:
    return day_start(value.first_day(), zone)


def date_period_end(value: DocumentDate, zone: str) -> datetime:
    return day_start(value.next_first_day(), zone)


# --- parsing ---------------------------------------------------------------


def _granularity(raw: object) -> Granularity:
    try:
        return Granularity(raw)  # type: ignore[arg-type]
    except ValueError as exc:
        raise TemporalRejected(TemporalReason.GRANULARITY_INVALID) from exc


def _instant(raw: object) -> datetime:
    """A malformed instant is a structural fault, not a temporal reason: it is the
    pilot's 400 `invalid_range`. A naive instant has no zone (S0001 AC1)."""
    if isinstance(raw, datetime):
        value = raw
    elif isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidRangeError("malformed bound instant") from exc
    else:
        raise InvalidRangeError("a bound instant must be an ISO 8601 string")
    if value.tzinfo is None:
        raise TemporalRejected(TemporalReason.TIME_ZONE_INVALID)
    return value.astimezone(UTC)


def parse_bound(raw: object) -> Bound:
    """Granularity is checked before the zone, so a bound with both wrong
    reports `granularity_invalid`."""
    if not isinstance(raw, Mapping) or set(raw) - {"instant", "granularity", "zone"}:
        raise InvalidRangeError("a bound has exactly instant, granularity and zone")
    granularity = _granularity(raw.get("granularity"))
    zone = raw.get("zone")
    zone_info(zone)
    assert isinstance(zone, str)
    return validate_bound(Bound(_instant(raw.get("instant")), granularity, zone))


def _document_date(raw: object) -> DocumentDate | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise TemporalRejected(TemporalReason.ATTESTATION_MISMATCH)
    try:
        return DocumentDate(str(raw.get("value")), DatePrecision(str(raw.get("precision"))))
    except (ValueError, TypeError) as exc:
        raise TemporalRejected(TemporalReason.ATTESTATION_MISMATCH) from exc


_ALLOWED_KEYS = frozenset(
    {
        "contract",
        "valid_from",
        "valid_from_basis",
        "valid_to_state",
        "valid_to",
        "attestation_zone",
        "ending_evidence_refs",
        "expected_attestation",
    }
)
_ATTESTATION_KEYS = frozenset({"attested_from", "attested_through", "attested_to"})


def parse_expected_attestation(raw_expected: object) -> ExpectedAttestation | None:
    """The caller's optional attestation echo (S0002 AC6)."""
    if raw_expected is None:
        return None
    if not isinstance(raw_expected, Mapping) or set(raw_expected) - _ATTESTATION_KEYS:
        raise TemporalRejected(TemporalReason.ATTESTATION_MISMATCH)
    return ExpectedAttestation({key: _document_date(value) for key, value in raw_expected.items()})


ETERNAL_KEYS = frozenset({"contract", "valid_to_state", "attestation_zone", "expected_attestation"})


def eternal_shape_ok(raw: Mapping[str, Any]) -> bool:
    """F0012 (ADR-0081 D7): an ETERNAL commit states no valid-time bound. The block
    is the contract, `valid_to_state: OPEN` and optionally the attestation echo."""
    return (
        raw.get("contract") == TEMPORAL_CONTRACT
        and set(raw) <= ETERNAL_KEYS
        and raw.get("valid_to_state") == EndState.OPEN.value
    )


def parse_commit_temporal(raw: Mapping[str, Any]) -> TemporalProposal:
    """Parse `fact-temporal-v1#/$defs/commit_temporal` into a proposal. Every
    structural fault is refused with the story's reason code, before any effect.

    The checks run in order: contract, end state, start basis, bounds, then the
    end-state combinations (S0002 AC1). Truncation in zone is checked inside
    `parse_bound`."""
    if raw.get("contract") != TEMPORAL_CONTRACT or set(raw) - _ALLOWED_KEYS:
        raise TemporalRejected(TemporalReason.TEMPORAL_FIELDS_REQUIRED)
    try:
        end_state = EndState(str(raw.get("valid_to_state")))
    except ValueError as exc:
        raise TemporalRejected(TemporalReason.END_STATE_INVALID) from exc

    raw_start = raw.get("valid_from")
    raw_basis = raw.get("valid_from_basis")
    basis: StartBasis | None = None
    if raw_start is not None:
        try:
            basis = StartBasis(str(raw_basis))
        except ValueError as exc:
            raise TemporalRejected(TemporalReason.START_BASIS_INVALID) from exc
        if basis not in CALLER_BASES:
            raise TemporalRejected(TemporalReason.START_BASIS_INVALID)
    elif raw_basis is not None:
        # ATTESTATION_FLOOR is server-assigned; a basis with no start is refused.
        raise TemporalRejected(TemporalReason.START_BASIS_INVALID)
    valid_from = parse_bound(raw_start) if raw_start is not None else None

    attestation_zone = raw.get("attestation_zone")
    if attestation_zone is not None:
        zone_info(attestation_zone)

    raw_end = raw.get("valid_to")
    raw_ending = raw.get("ending_evidence_refs")
    ending: tuple[UUID, ...] = ()
    if raw_ending is not None:
        if not isinstance(raw_ending, list) or not raw_ending:
            raise TemporalRejected(TemporalReason.END_STATE_INVALID)
        try:
            ending = tuple(dict.fromkeys(UUID(str(r)) for r in raw_ending))
        except ValueError as exc:
            raise TemporalRejected(TemporalReason.END_STATE_INVALID) from exc
        if len(ending) != len(raw_ending):
            raise TemporalRejected(TemporalReason.END_STATE_INVALID)

    valid_to: Bound | None = None
    match end_state:
        case EndState.OPEN:
            if raw_end is not None or ending:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
        case EndState.BOUNDED:
            if raw_end is None or ending:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
            valid_to = parse_bound(raw_end)
            if valid_from is not None and valid_to.instant <= valid_from.instant:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
        case EndState.UNKNOWN:
            if raw_end is not None or not ending or attestation_zone is None:
                raise TemporalRejected(TemporalReason.END_STATE_INVALID)
    if valid_from is None and attestation_zone is None:
        # An unknown start is placed in the attestation zone; without one the
        # zone is missing (S0001 AC1).
        raise TemporalRejected(TemporalReason.TIME_ZONE_INVALID)

    expected = parse_expected_attestation(raw.get("expected_attestation"))

    return TemporalProposal(
        valid_from=valid_from,
        valid_from_basis=basis,
        valid_to_state=end_state,
        valid_to=valid_to,
        attestation_zone=attestation_zone if isinstance(attestation_zone, str) else None,
        ending_evidence_refs=ending,
        expected_attestation=expected,
    )
