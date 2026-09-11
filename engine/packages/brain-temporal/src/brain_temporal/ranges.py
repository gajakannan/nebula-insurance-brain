from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class InvalidRangeError(Exception):
    """Empty or null range (F0001-S0005 acceptance criterion: 'a commit supplies an
    empty or null range -> rejected with a validation error before any write')."""


@dataclass(frozen=True, slots=True)
class TimeRange:
    """A half-open `[start, end)` interval; `end=None` means open/unbounded — used for
    both `valid` and `recorded` on `canonical_fact_version` (ADR-0007)."""

    start: datetime
    end: datetime | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end <= self.start:
            raise InvalidRangeError(f"empty or inverted range: [{self.start}, {self.end})")

    def overlaps(self, other: TimeRange) -> bool:
        """Two half-open ranges overlap iff each starts before the other ends.
        An unbounded end never blocks an overlap."""
        self_before_other_end = other.end is None or self.start < other.end
        other_before_self_end = self.end is None or other.start < self.end
        return self_before_other_end and other_before_self_end

    def close(self, at: datetime) -> TimeRange:
        """Returns a copy with `end` set to `at` — used to close a version's
        `recorded` upper bound when it stops being current."""
        return TimeRange(start=self.start, end=at)


def split_remainder(old: TimeRange, new: TimeRange) -> list[TimeRange]:
    """The portion(s) of `old`'s valid range not covered by `new`'s — 0, 1, or 2
    pieces, inserted as `change_reason=SPLIT` versions carrying `old`'s value
    (F0001-S0005 logic flow step 4: 'insert the split remainders (before and
    after) as new versions'). Assumes `old.overlaps(new)`."""
    remainders: list[TimeRange] = []
    if old.start < new.start:
        remainders.append(TimeRange(old.start, new.start))
    if new.end is not None:
        if old.end is None:
            remainders.append(TimeRange(new.end, None))
        elif new.end < old.end:
            remainders.append(TimeRange(new.end, old.end))
    return remainders
