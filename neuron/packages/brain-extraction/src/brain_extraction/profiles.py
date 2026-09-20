from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pydantic import BaseModel, Field


class GLLimitsA(BaseModel):
    """Extraction template for `gl-limits-a` — the two headline GL limits."""

    each_occurrence_limit: str | None = Field(
        None,
        description="Each Occurrence Limit dollar amount, verbatim as printed, e.g. '$1,000,000'",
    )
    general_aggregate_limit: str | None = Field(
        None,
        description=(
            "General Aggregate Limit (Other Than Products-Completed Operations) "
            "dollar amount, verbatim"
        ),
    )


class GLLimitsB(BaseModel):
    """Extraction template for `gl-limits-b` — named insured and policy period, proving
    the same persisted artifact supports a second, independently-scoped profile."""

    named_insured: str | None = Field(
        None, description="The Named Insured on the declarations page, verbatim"
    )
    policy_period_start: str | None = Field(None, description="Policy period start date, verbatim")
    policy_period_end: str | None = Field(None, description="Policy period end date, verbatim")


@dataclass(frozen=True, slots=True)
class ExtractionProfile:
    profile_id: str
    profile_version: str
    template: type[BaseModel]
    declaration_path: str

    @property
    def schema_sha256(self) -> str:
        return hashlib.sha256(
            json.dumps(self.template.model_json_schema(), sort_keys=True).encode()
        ).hexdigest()


PROFILES: dict[str, ExtractionProfile] = {
    "gl-limits-a": ExtractionProfile(
        "gl-limits-a", "1", GLLimitsA, "profiles/extraction/gl-limits-a.yaml"
    ),
    "gl-limits-b": ExtractionProfile(
        "gl-limits-b", "1", GLLimitsB, "profiles/extraction/gl-limits-b.yaml"
    ),
}


def load_profile(profile_id: str) -> ExtractionProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown extraction profile: {profile_id!r}") from exc
