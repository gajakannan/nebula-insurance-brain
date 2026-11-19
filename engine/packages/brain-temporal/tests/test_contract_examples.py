"""The 20 F0008 design cases (`contract-examples.json`) against the design
schemas and against the runtime parser, so the schemas and the code cannot
drift apart (assembly plan step 7).

Schema validity alone does not prove truncation in zone, attestation, guards
or persistence; those are the PostgreSQL suites."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import jsonschema
import pytest
from brain_domain.temporal import (
    Bound,
    DocumentDate,
    EndState,
    Granularity,
    StartBasis,
    TemporalKind,
    TemporalReason,
    TemporalRejected,
    VersionTemporal,
)
from brain_temporal.bounds import parse_commit_temporal
from referencing import Registry, Resource

PLANNING = next(
    p / "planning-mds" for p in Path(__file__).resolve().parents if (p / "planning-mds").is_dir()
)
EXAMPLES = next(PLANNING.glob("features/**/F0008-*/contract-examples.json"))
SCHEMAS = PLANNING / "schemas"
CASES = json.loads(EXAMPLES.read_text())["cases"]

# Expected runtime refusal for each invalid commit case, from the story ACs.
EXPECTED_CODE = {
    "N01": TemporalReason.GRANULARITY_INVALID,
    "N02": TemporalReason.GRANULARITY_INVALID,
    "N03": TemporalReason.END_STATE_INVALID,
    "N04": TemporalReason.END_STATE_INVALID,
    "N05": TemporalReason.END_STATE_INVALID,
    "N06": TemporalReason.START_BASIS_INVALID,
    "N07": TemporalReason.START_BASIS_INVALID,
    "N08": TemporalReason.TIME_ZONE_INVALID,
    "N09": TemporalReason.TEMPORAL_FIELDS_REQUIRED,
}


def _registry() -> Registry:
    resources = []
    for name in (
        "fact-temporal-v1",
        "canonical-commit-request",
        "fact-answer-v1",
    ):
        schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
        resource = Resource.from_contents(schema)
        resources += [(schema["$id"], resource), (f"{name}.schema.json", resource)]
    return Registry().with_resources(resources)


REGISTRY = _registry()
TEMPORAL = json.loads((SCHEMAS / "fact-temporal-v1.schema.json").read_text())
REQUEST = json.loads((SCHEMAS / "canonical-commit-request.schema.json").read_text())


def _validator(target: str) -> jsonschema.Draft202012Validator:
    if target == "commit_request":
        return jsonschema.Draft202012Validator(REQUEST, registry=REGISTRY)
    schema = {"$ref": f"fact-temporal-v1.schema.json#/$defs/{target}"}
    return jsonschema.Draft202012Validator(schema, registry=REGISTRY)


def test_twenty_cases_are_present() -> None:
    assert len(CASES) == 20


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_schema_agrees_with_the_case(case: dict) -> None:
    errors = list(_validator(case["target"]).iter_errors(case["instance"]))
    assert (not errors) is case["valid"], [e.message for e in errors]


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c["target"] == "commit_request"],
    ids=[c["id"] for c in CASES if c["target"] == "commit_request"],
)
def test_runtime_parser_agrees_with_the_case(case: dict) -> None:
    instance = case["instance"]
    temporal = instance.get("temporal")
    if case["id"] == "N10":
        # The temporal block is well formed; the request also sends valid_from,
        # which the API model refuses before the service runs (ADR-0078 D1).
        from brain_api.schemas.facts import CommitProposalIn

        with pytest.raises(ValueError):
            CommitProposalIn.model_validate(instance)
        return
    if temporal is None:
        assert case["valid"] and "valid_from" in instance  # C07: legacy pilot shape
        return
    if case["valid"]:
        proposal = parse_commit_temporal(temporal)
        assert proposal.valid_to_state is EndState(temporal["valid_to_state"])
        return
    with pytest.raises(TemporalRejected) as refused:
        parse_commit_temporal(temporal)
    assert refused.value.code is EXPECTED_CODE[case["id"]]


def test_runtime_read_shapes_validate_against_the_schema() -> None:
    chicago = "America/Chicago"
    temporal = VersionTemporal(
        kind=TemporalKind.STATE,
        valid_from=Bound(datetime(2026, 1, 1, 6, tzinfo=UTC), Granularity.DAY, chicago),
        valid_from_basis=StartBasis.TEMPLATE_FIELD,
        valid_to_state=EndState.UNKNOWN,
        valid_to=Bound(datetime(2026, 8, 3, 5, tzinfo=UTC), Granularity.DAY, chicago),
        attested_from=DocumentDate("2026-06-01", "DAY"),  # type: ignore[arg-type]
        attested_through=DocumentDate("2026-06-01", "DAY"),  # type: ignore[arg-type]
        attested_to=DocumentDate("2026-08-02", "DAY"),  # type: ignore[arg-type]
        validity_unknown_from=datetime(2026, 6, 2, 5, tzinfo=UTC),
        split_of_version_id=uuid4(),
    )
    assert not list(_validator("version_temporal").iter_errors(temporal.to_json()))
    read = {
        "fact_slot_id": str(uuid4()),
        "validity": "UNKNOWN",
        "reason": "UNKNOWN_END_WINDOW",
        "version_id": str(uuid4()),
        "temporal": temporal.to_json(),
    }
    assert not list(_validator("validity_unknown_read").iter_errors(read))
