"""Stable authoring/compile error codes and the sorted issue list (S0001 AC7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Code(StrEnum):
    YAML_INVALID = "YAML_INVALID"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    AUTHORING_FIELD_RETIRED = "AUTHORING_FIELD_RETIRED"
    UNSUPPORTED_CONSTRUCT = "UNSUPPORTED_CONSTRUCT"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    TERM_ID_INVALID = "TERM_ID_INVALID"
    DEFINITION_REQUIRED = "DEFINITION_REQUIRED"
    EXAMPLE_REQUIRED = "EXAMPLE_REQUIRED"
    REGRESSION_CASE_REQUIRED = "REGRESSION_CASE_REQUIRED"
    REFERENCE_UNRESOLVED = "REFERENCE_UNRESOLVED"
    LABEL_EN_US_REQUIRED = "LABEL_EN_US_REQUIRED"
    LABEL_TAG_INVALID = "LABEL_TAG_INVALID"
    LABEL_PREFERRED_DUPLICATE = "LABEL_PREFERRED_DUPLICATE"
    TEMPORAL_KIND_INVALID = "TEMPORAL_KIND_INVALID"
    CONSTRAINT_CONTEXT_INCOMPLETE = "CONSTRAINT_CONTEXT_INCOMPLETE"
    PREDICATE_KEY_INVALID = "PREDICATE_KEY_INVALID"
    PREDICATE_KEY_DUPLICATE = "PREDICATE_KEY_DUPLICATE"
    TENANT_NAMESPACE_RESERVED = "TENANT_NAMESPACE_RESERVED"
    IRI_COLLISION = "IRI_COLLISION"
    IDENTITY_REUSE_REJECTED = "IDENTITY_REUSE_REJECTED"
    TERM_REMOVED_WITHOUT_RETIREMENT = "TERM_REMOVED_WITHOUT_RETIREMENT"
    CHANGE_RECORD_INVALID = "CHANGE_RECORD_INVALID"
    DEPENDENCY_UNRESOLVED = "DEPENDENCY_UNRESOLVED"
    PROJECTION_UNCOVERED = "PROJECTION_UNCOVERED"
    AUTHORING_CONSTRAINT_VIOLATED = "AUTHORING_CONSTRAINT_VIOLATED"
    RELEASE_REQUEST_INVALID = "RELEASE_REQUEST_INVALID"
    OUTPUT_STALE = "OUTPUT_STALE"


@dataclass(frozen=True, slots=True, order=True)
class Issue:
    """One error. Field order is the report order: file, JSON path, code."""

    file: str
    path: str
    code: str
    message: str

    def to_json(self) -> dict[str, str]:
        return {"file": self.file, "path": self.path, "code": self.code, "message": self.message}


class CompileFailed(Exception):
    def __init__(self, issues: list[Issue]) -> None:
        self.issues = sorted(set(issues))
        super().__init__(f"{len(self.issues)} error(s)")


def json_path(parts: tuple[object, ...] | list[object]) -> str:
    """`$.terms[3].labels` style path; deterministic for sorting."""
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out
