"""Test-only template with an entity relationship that has no downstream mapping.

A real module (not a test-local or `create_model` class) gives Graph a stable
class identity for its node registry, so the probe reaches the adapter's
unsupported-output check instead of failing inside Graph conversion.
"""

from pydantic import BaseModel, Field


class Insured(BaseModel):
    name: str | None = Field(None, description="Named Insured, verbatim")
    address: str | None = Field(None, description="Mailing address, verbatim")


class RelationshipProbe(BaseModel):
    """Template with an entity relationship that has no downstream mapping."""

    each_occurrence_limit: str | None = Field(None, description="Each Occurrence Limit, verbatim")
    insured: Insured | None = Field(None, description="The named insured party and its address")
