"""Versioned text normalization with conservative original-character mapping."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

NORMALIZATION_VERSION = "f0006-grounding-v1"


@dataclass(frozen=True)
class NormalizedText:
    text: str
    ranges: tuple[tuple[int, int], ...]


def _nfc_units(text: str) -> list[tuple[str, tuple[int, int]]]:
    """Map an NFC combining sequence to its complete original source interval.

    Sharing an interval between composed characters is intentional: a partial
    match of a reordered sequence cannot claim a unique contiguous source span.
    Hangul composition also joins adjacent non-combining Jamo code points.
    """
    result: list[tuple[str, tuple[int, int]]] = []
    cluster = ""
    start = 0
    for index, char in enumerate(text):
        joins = cluster and (
            unicodedata.combining(char) != 0
            or unicodedata.normalize("NFC", cluster + char)
            != unicodedata.normalize("NFC", cluster) + char
        )
        if cluster and not joins:
            result.extend((c, (start, index)) for c in unicodedata.normalize("NFC", cluster))
            cluster = ""
        if not cluster:
            start = index
        cluster += char
    if cluster:
        result.extend((c, (start, len(text))) for c in unicodedata.normalize("NFC", cluster))
    return result


def normalize_with_mapping(text: str) -> NormalizedText:
    units = _nfc_units(text)
    joined: list[tuple[str, tuple[int, int]]] = []
    index = 0
    while index < len(units):
        char, interval = units[index]
        if char in ("-", "\u2010", "\u00ad") and joined and joined[-1][0].isalpha():
            end = index + 1
            while end < len(units) and units[end][0].isspace():
                end += 1
            whitespace = "".join(c for c, _ in units[index + 1 : end])
            if (
                end < len(units)
                and units[end][0].isalpha()
                and any(c in whitespace for c in "\r\n")
            ):
                index = end
                continue
        joined.extend((c, interval) for c in char.casefold())
        index += 1
    collapsed: list[tuple[str, tuple[int, int]]] = []
    for char, interval in joined:
        if char.isspace():
            if collapsed and collapsed[-1][0] == " ":
                collapsed[-1] = (" ", (collapsed[-1][1][0], interval[1]))
            else:
                collapsed.append((" ", interval))
        else:
            collapsed.append((char, interval))
    final = [
        item
        for index, item in enumerate(collapsed)
        if not (
            item[0] == " "
            and (
                (index > 0 and unicodedata.category(collapsed[index - 1][0]) == "Sc")
                or (
                    index + 1 < len(collapsed)
                    and unicodedata.category(collapsed[index + 1][0]) == "Sc"
                )
            )
        )
    ]
    return NormalizedText("".join(c for c, _ in final), tuple(interval for _, interval in final))


def normalize(text: str) -> str:
    return normalize_with_mapping(text).text


def normalize_name(text: str) -> str:
    """Document-local admission key; deliberately excludes grounding rewrites."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).casefold()).strip()


def match_positions(source: str, quote: str) -> tuple[tuple[int, int], ...]:
    haystack, needle = normalize(source), normalize(quote)
    if not needle:
        return ()
    result: list[tuple[int, int]] = []
    start = 0
    while (index := haystack.find(needle, start)) >= 0:
        result.append((index, index + len(needle)))
        start = index + 1
    return tuple(result)


@dataclass(frozen=True)
class GroundedLocation:
    precision: str
    selector: dict[str, Any]


def locate_quote(
    source: str, quote: str, native_selector: Mapping[str, Any]
) -> GroundedLocation | None:
    """Locate in retained text, retaining native coordinates and honest ambiguity."""
    normalized = normalize_with_mapping(source)
    matches = match_positions(source, quote)
    if not matches:
        return None
    selector = dict(native_selector)
    declared = selector.pop("precision", None)
    regions = selector.get("regions", [])
    if selector.get("kind") == "unresolved":
        return GroundedLocation("unresolved", selector)
    if selector.get("cell_id") is not None or declared == "table_cell":
        # A source-verified cell identifies the cell even when its text repeats.
        return GroundedLocation("table_cell", selector)
    if (
        len(matches) == 1
        and declared not in ("page", "document", "unresolved")
        and len(regions) <= 1
    ):
        first, last = matches[0]
        ranges = normalized.ranges[first:last]
        start, end = min(a for a, _ in ranges), max(b for _, b in ranges)
        # Case folding can expand ß→ss, and NFC can reorder combining marks.
        # Only a complete original interval that normalizes exactly may be a span.
        if normalize(source[start:end]) == normalize(quote) and (
            selector.get("native_ref") or selector.get("block_id")
        ):
            base = selector.get("char_start")
            if type(base) is not int:
                base = 0
            selector.update(char_start=base + start, char_end=base + end)
            return GroundedLocation("span", selector)
    selector.pop("char_start", None)
    selector.pop("char_end", None)
    if selector.get("block_id") or selector.get("native_ref"):
        return GroundedLocation("block", selector)
    if type(selector.get("page")) is int:
        return GroundedLocation("page", selector)
    if declared == "document" or selector.get("document_version_id"):
        return GroundedLocation("document", selector)
    return GroundedLocation("unresolved", selector)
