"""Typed v2 records; JSON Schema remains the authority for their wire shape."""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from brain_content.contracts import validate_contract, wire_value

Origin = Literal["STATED", "OCR", "TRANSCRIBED", "DESCRIBED"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class Producer(StrictModel):
    engine: str
    engine_version: str
    model: str | None
    model_version: str | None


class Box(StrictModel):
    x0: float
    y0: float
    x1: float
    y1: float


class Region(StrictModel):
    page: StrictInt
    bbox: Box | None
    char_start: StrictInt | None
    char_end: StrictInt | None


class NativeTextAnchor(StrictModel):
    kind: Literal["native_text"]
    native_ref: str
    regions: list[Region]


class PageRegionAnchor(StrictModel):
    kind: Literal["page_region"]
    regions: list[Region]


class TimeSpanAnchor(StrictModel):
    kind: Literal["time_span"]
    start_ms: StrictInt
    end_ms: StrictInt
    speaker: str | None


class FigureAnchor(StrictModel):
    kind: Literal["figure"]
    figure_ref: str
    regions: list[Region]


class UnresolvedAnchor(StrictModel):
    kind: Literal["unresolved"]
    reason: str


OriginAnchor = Annotated[
    NativeTextAnchor | PageRegionAnchor | TimeSpanAnchor | FigureAnchor | UnresolvedAnchor,
    Field(discriminator="kind"),
]


class Record(StrictModel):
    definition: ClassVar[str]

    @model_validator(mode="before")
    @classmethod
    def input_contract(cls, value: Any) -> Any:
        validate_contract("content-records-v2.schema.json", wire_value(value), cls.definition)
        return value

    @model_validator(mode="after")
    def contract(self) -> Self:
        validate_contract(
            "content-records-v2.schema.json", self.model_dump(mode="json"), self.definition
        )
        return self


class ContentBlockV2(Record):
    definition = "block"
    record_type: Literal["block"]
    contract_version: Literal[2]
    block_id: str
    native_ref: str
    reading_order: StrictInt
    section_path: list[str]
    text: str
    text_origin: Origin
    producer: Producer
    origin_anchor: OriginAnchor
    confidence: float | None


class TableCell(StrictModel):
    cell_id: str
    row_start: StrictInt
    col_start: StrictInt
    row_span: StrictInt
    col_span: StrictInt
    text: str
    block_ids: list[str]


class ContentTableV2(Record):
    definition = "table"
    record_type: Literal["table"]
    contract_version: Literal[2]
    table_id: str
    native_ref: str
    num_rows: StrictInt
    num_cols: StrictInt
    header_rows: list[StrictInt]
    continuation_of: str | None
    cells: list[TableCell]


class ContentLayoutV2(Record):
    definition = "layout"
    record_type: Literal["layout"]
    contract_version: Literal[2]
    page: StrictInt
    geometry_state: Literal["available", "unavailable"]
    width: float | None
    height: float | None
    rotation_degrees: Literal[0, 90, 180, 270] | None
    native_to_canonical: list[float] | None
    unavailable_reason: str | None
