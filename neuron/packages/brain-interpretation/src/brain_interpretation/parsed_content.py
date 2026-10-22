from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

ParseStatus = Literal["complete", "partial", "failed"]


@dataclass(frozen=True, slots=True)
class ProducerIdentity:
    engine: str
    engine_version: str
    model: str | None
    model_version: str | None


@dataclass(frozen=True, slots=True)
class BlockOriginInput:
    native_ref: str
    text: str
    text_origin: Literal["STATED", "OCR", "TRANSCRIBED", "DESCRIBED"]
    producer: ProducerIdentity
    origin_anchor: dict[str, Any]
    confidence: float | None


@dataclass(frozen=True, slots=True)
class ParseResult[DocumentT]:
    """Conversion checkpoint shared by pipeline and bundle adapters.

    The document type is supplied by the adapter; this contract does not import
    a converter or couple the interpretation package to a concrete parser.
    """

    document: DocumentT
    page_count: int
    failed_pages: list[int]
    ocr_page_count: int
    status: ParseStatus
    warnings: list[str]
    projection_version: int | None = None
    provenance: Mapping[str, tuple[BlockOriginInput, ...]] = field(default_factory=dict)
    origin_unavailable: tuple[str, ...] = ()
    page_rotations: Mapping[int, int] = field(default_factory=dict)
