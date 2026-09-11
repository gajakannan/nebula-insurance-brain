from __future__ import annotations

from datetime import UTC, datetime

import pytest
from brain_temporal.ranges import InvalidRangeError, TimeRange, split_remainder


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_inverted_range_is_rejected() -> None:
    with pytest.raises(InvalidRangeError):
        TimeRange(dt("2026-06-01"), dt("2026-01-01"))


def test_empty_range_is_rejected() -> None:
    with pytest.raises(InvalidRangeError):
        TimeRange(dt("2026-06-01"), dt("2026-06-01"))


def test_open_ended_range_is_valid() -> None:
    r = TimeRange(dt("2026-06-01"), None)
    assert r.end is None


def test_disjoint_ranges_do_not_overlap() -> None:
    a = TimeRange(dt("2026-01-01"), dt("2026-02-01"))
    b = TimeRange(dt("2026-03-01"), dt("2026-04-01"))
    assert not a.overlaps(b)
    assert not b.overlaps(a)


def test_touching_ranges_do_not_overlap_half_open() -> None:
    a = TimeRange(dt("2026-01-01"), dt("2026-02-01"))
    b = TimeRange(dt("2026-02-01"), dt("2026-03-01"))
    assert not a.overlaps(b)


def test_overlapping_ranges_overlap() -> None:
    a = TimeRange(dt("2026-01-01"), dt("2026-03-01"))
    b = TimeRange(dt("2026-02-01"), dt("2026-04-01"))
    assert a.overlaps(b)
    assert b.overlaps(a)


def test_open_ended_range_overlaps_anything_after_its_start() -> None:
    a = TimeRange(dt("2026-01-01"), None)
    b = TimeRange(dt("2030-01-01"), dt("2031-01-01"))
    assert a.overlaps(b)


def test_split_remainder_new_fully_covers_old_leaves_nothing() -> None:
    old = TimeRange(dt("2026-01-01"), dt("2026-06-01"))
    new = TimeRange(dt("2025-01-01"), dt("2027-01-01"))
    assert split_remainder(old, new) == []


def test_split_remainder_new_in_the_middle_leaves_two_pieces() -> None:
    old = TimeRange(dt("2026-01-01"), None)
    new = TimeRange(dt("2026-06-01"), dt("2026-06-03"))

    remainders = split_remainder(old, new)

    assert remainders == [
        TimeRange(dt("2026-01-01"), dt("2026-06-01")),
        TimeRange(dt("2026-06-03"), None),
    ]


def test_split_remainder_new_at_the_start_leaves_one_trailing_piece() -> None:
    old = TimeRange(dt("2026-01-01"), dt("2026-12-01"))
    new = TimeRange(dt("2026-01-01"), dt("2026-06-01"))

    assert split_remainder(old, new) == [TimeRange(dt("2026-06-01"), dt("2026-12-01"))]


def test_split_remainder_new_at_the_open_end_leaves_one_leading_piece() -> None:
    old = TimeRange(dt("2026-01-01"), None)
    new = TimeRange(dt("2026-06-01"), None)

    assert split_remainder(old, new) == [TimeRange(dt("2026-01-01"), dt("2026-06-01"))]
