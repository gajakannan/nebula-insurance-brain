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
class OcrObservation:
    """What the OCR engine actually did during one conversion (F0005-S0001-AC2).

    `pages` are the 1-based pages on which the engine produced at least one text
    cell. `engine` is None when OCR is configured but its engine or model assets
    cannot be identified; it is never guessed.
    """

    pages: tuple[int, ...]
    engine: ProducerIdentity | None


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
    # `<asset-name>@<revision>:sha256:<hex>` for each OCR model file the
    # configured pipeline loaded, hashed at conversion time (F0005-S0005).
    model_artifact_digests: tuple[str, ...] = ()
    # None when the producer did not observe OCR (historical or recorded fixtures).
    ocr: OcrObservation | None = None
