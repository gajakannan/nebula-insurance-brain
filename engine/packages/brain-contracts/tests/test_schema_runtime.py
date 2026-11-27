"""Adversarial admission/portability proof for the closed contract runtime."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest
from brain_contracts.schema_runtime import (
    DIALECT,
    MAX_BYTES,
    ContractBundle,
    ContractError,
    ContractRef,
    decode_json,
    portable_json_bytes,
)

TOOLS = {
    name: "test"
    for name in (
        "builder",
        "python",
        "jsonschema",
        "referencing",
        "pydantic",
        "datamodel_code_generator",
        "ajv",
        "ajv_formats",
        "jsonc_parser",
    )
}


def bundle_for(schema: dict, other: dict | None = None, mutate=None) -> ContractBundle:
    schemas = {
        "test.schema.json": {
            "$schema": DIALECT,
            "$id": "https://nebula.local/schemas/test.schema.json",
            **schema,
        }
    }
    if other is not None:
        schemas["other.schema.json"] = {
            "$schema": DIALECT,
            "$id": "https://nebula.local/schemas/other.schema.json",
            **other,
        }
    raw = {name: json.dumps(value).encode() for name, value in schemas.items()}
    manifest = {
        "bundle": "brain-contracts/v1",
        "profile": "nebula-json-schema/1",
        "toolchain": TOOLS,
        "resources": [
            {
                "id": schema["$id"],
                "version": "1",
                "path": name,
                "sha256": hashlib.sha256(raw[name]).hexdigest(),
            }
            for name, schema in schemas.items()
        ],
    }
    if mutate:
        mutate(manifest, raw)
    return ContractBundle(json.dumps(manifest).encode(), raw.__getitem__)


def test_detached_source_and_metadata_no_defaults_or_coercion():
    bundle = bundle_for(
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "default": "untouched",
                    "x-nebula-display-name": "A name",
                }
            },
            "additionalProperties": True,
        }
    )
    ref = ContractRef("test", "1")
    value = {"opaque": {"default": "data", "__proto__": {"safe": True}}, "null": None}
    before = copy.deepcopy(value)
    bundle.validate(ref, value, profile="portable-json/v1")
    assert value == before and "name" not in value
    schema = bundle.schema(ref)
    schema["properties"]["name"]["type"] = "integer"
    bundle.validate(ref, {"name": "still string"}, profile="portable-json/v1")
    metadata = bundle.metadata(ContractRef("test", "1", "/properties/name"))
    assert metadata == {"x-nebula-display-name": "A name"}
    metadata["x-nebula-display-name"] = "changed"
    assert (
        bundle.metadata(ContractRef("test", "1", "/properties/name"))["x-nebula-display-name"]
        == "A name"
    )
    with pytest.raises(ContractError, match="CONTRACT_INSTANCE_INVALID"):
        bundle.validate(ref, {"name": 7}, profile="portable-json/v1")


def test_data_property_named_like_keyword_is_valid():
    bundle = bundle_for(
        {
            "type": "object",
            "properties": {"default": {"type": "string"}, "x-nebula-any": {"type": "boolean"}},
        }
    )
    bundle.validate(
        ContractRef("test", "1"),
        {"default": "data", "x-nebula-any": True},
        profile="portable-json/v1",
    )


@pytest.mark.parametrize(
    "schema,code",
    [
        ({"unknownInstruction": True}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"$schema": "http://json-schema.org/draft-07/schema#"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"type": "string", "format": "email"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"x-nebula-security-scope": True}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"x-nebula-evidence-required": "yes"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"x-nebula-exec": "ignored?"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"$dynamicRef": "#x"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        ({"$ref": "https://outside.invalid/schema"}, "CONTRACT_REFERENCE_UNRESOLVED"),
        ({"$ref": "file:///etc/passwd"}, "CONTRACT_REFERENCE_UNRESOLVED"),
        (
            {"if": {"const": False}, "then": {"$ref": "missing.schema.json"}},
            "CONTRACT_REFERENCE_UNRESOLVED",
        ),
        ({"$ref": "#/$defs/missing"}, "CONTRACT_REFERENCE_UNRESOLVED"),
        ({"$ref": "#/description", "description": "not a schema"}, "CONTRACT_REFERENCE_UNRESOLVED"),
        ({"$ref": "#"}, "CONTRACT_SCHEMA_UNSUPPORTED"),
        (
            {"$defs": {"a": {"$ref": "#/$defs/b"}, "b": {"$ref": "#/$defs/a"}}},
            "CONTRACT_SCHEMA_UNSUPPORTED",
        ),
    ],
)
def test_schema_failures_are_closed_before_any_instance(schema, code):
    with pytest.raises(ContractError) as error:
        bundle_for(schema)
    assert error.value.code == code
    assert str(error.value) == code


def test_closed_registered_relative_refs_and_escaped_pointers(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **k: pytest.fail("network retrieval")
    )
    bundle = bundle_for(
        {"$ref": "other.schema.json#/$defs/a~1b~0c"},
        {"$defs": {"a/b~c": {"type": "string", "const": "yes"}}},
    )
    bundle.validate(ContractRef("test", "1"), "yes", profile="portable-json/v1")
    with pytest.raises(ContractError):
        bundle.validate(ContractRef("test", "1"), "no", profile="portable-json/v1")
    for ref in (
        ContractRef("test", "2"),
        ContractRef("../test", "1"),
        ContractRef("test", "1", "/bad"),
        ContractRef("test", "1", "#"),
    ):
        with pytest.raises(ContractError):
            bundle.schema(ref)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda m, r: m.update(bundle="unknown"),
        lambda m, r: m.update(profile="unknown"),
        lambda m, r: m.update(toolchain={}),
        lambda m, r: m.update(unrecognized=True),
        lambda m, r: m.update(resources=[]),
        lambda m, r: m["resources"].append(dict(m["resources"][0])),
        lambda m, r: m["resources"][0].update(version="0"),
        lambda m, r: m["resources"][0].update(path="../test.schema.json"),
        lambda m, r: m["resources"][0].update(id="file:///test.schema.json"),
        lambda m, r: m["resources"][0].update(sha256="0" * 64),
        lambda m, r: r.update({"test.schema.json": b"{}"}),
        lambda m, r: r.pop("test.schema.json"),
    ],
)
def test_bundle_corruption_never_exposes_partial_registry(mutation):
    with pytest.raises(ContractError):
        bundle_for({"type": "string"}, mutate=mutation)


@pytest.mark.parametrize(
    "raw",
    [
        '{"x":1,"x":2}',
        '{"x":{"y":1,"y":2}}',
        "NaN",
        "Infinity",
        "-Infinity",
        "1e9999",
        "9007199254740992",
        "9007199254740993e0",
        '"\\ud800"',
        '"\\udfff"',
        '{/*comment*/"x":1}',
        '{"x":1,}',
        "",
        "\ufeff{}",
        b'"\xff"',
    ],
)
def test_portable_decode_refuses_malformed_or_nonportable_json(raw):
    with pytest.raises(ContractError):
        decode_json(raw, profile="portable-json/v1")


@pytest.mark.parametrize(
    "raw,value",
    [
        ("9007199254740991", 9007199254740991),
        ("-9007199254740991", -9007199254740991),
        ("0.25", 0.25),
        ('"\\ud83d\\ude00"', "😀"),
        ('{"__proto__":null}', {"__proto__": None}),
    ],
)
def test_portable_decode_boundaries(raw, value):
    assert decode_json(raw, profile="portable-json/v1") == value


def test_profiles_are_selected_explicitly_and_do_not_fallback():
    assert decode_json("9007199254740993", profile="native-compat/v1") == 9007199254740993
    with pytest.raises(ContractError):
        decode_json("9007199254740993", profile="portable-json/v1")
    with pytest.raises(ContractError):
        decode_json("{}", profile="unknown")
    bundle = bundle_for({"type": "integer"})
    bundle.validate(ContractRef("test", "1"), 2**100, profile="native-compat/v1")
    with pytest.raises(ContractError):
        bundle.validate(ContractRef("test", "1"), 2**100, profile="portable-json/v1")


def test_portable_limits_cycles_and_opaque_keys():
    with pytest.raises(ContractError):
        decode_json('"' + "x" * MAX_BYTES + '"', profile="portable-json/v1")
    assert decode_json("[" * 127 + "0" + "]" * 127, profile="portable-json/v1")
    with pytest.raises(ContractError):
        decode_json("[" * 128 + "0" + "]" * 128, profile="portable-json/v1")
    bundle = bundle_for({})
    cyclic = []
    cyclic.append(cyclic)
    for value in (cyclic, {7: "not JSON"}, float("nan"), object(), [None] * 1_000_000):
        with pytest.raises(ContractError):
            bundle.validate(ContractRef("test", "1"), value, profile="portable-json/v1")


@pytest.mark.parametrize(
    "format,good,bad",
    [
        (
            "uuid",
            "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
            "urn:uuid:AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
        ),
        ("date", "0001-01-01", "0000-01-01"),
        ("date", "2000-02-29", "1900-02-29"),
        ("date-time", "2026-01-01t00:00:59.123z", "2026-01-01T00:00:60Z"),
        ("date-time", "2026-01-01T00:00:00+23:59", "2026-01-01T00:00:00+24:00"),
        ("uri-reference", "", "x%ZZ"),
        ("uri-reference", "../a?x=1#f", "https://example.test/a b"),
    ],
)
def test_portable_formats_are_explicit_and_consistent(format, good, bad):
    bundle = bundle_for({"type": "string", "format": format})
    ref = ContractRef("test", "1")
    bundle.validate(ref, good, profile="portable-json/v1")
    with pytest.raises(ContractError):
        bundle.validate(ref, bad, profile="portable-json/v1")


def test_errors_never_contain_instance_values():
    bundle = bundle_for({"type": "object", "additionalProperties": False})
    with pytest.raises(ContractError) as error:
        bundle.validate(
            ContractRef("test", "1"),
            {"secret source quote": "credential"},
            profile="portable-json/v1",
        )
    assert str(error.value) == "CONTRACT_INSTANCE_INVALID"
    assert "secret" not in repr(error.value.issue) and "credential" not in repr(error.value.issue)


def test_installed_bundle_resource_count_and_identity():
    bundle = ContractBundle.installed()
    # F0011 shipped 21; F0009 adds provenance-query/result, the reservation and
    # attempt carriers, and review-decision as their closed $ref dependency.
    # F0012 adds the ontology module authoring, release manifest and impact report.
    assert len(bundle._manifest["resources"]) == 29
    for name in (
        "ontology-module-authoring-v1",
        "ontology-release-manifest-v1",
        "ontology-impact-report-v1",
        "provenance-query-v1",
        "provenance-result-v1",
        "learning-candidate-reservation-v1",
        "review-submission-attempt-v1",
    ):
        assert bundle.schema(ContractRef(name, "1"))["$id"].endswith(f"/{name}.schema.json")
    assert len(bundle.digest) == 64
    assert bundle.schema(ContractRef("qualified-money-v1", "1"))["$ref"].endswith("/money_value")
    assert bundle.openapi()["openapi"] == "3.1.0"
    with pytest.raises(ContractError):
        ContractBundle.from_directory("/does-not-exist")


def test_portable_exact_end_pattern_preserves_native_reader_policy():
    bundle = bundle_for({"type": "string", "pattern": "^[A-Z]{3}$"})
    ref = ContractRef("test", "1")
    bundle.validate(ref, "USD", profile="portable-json/v1")
    with pytest.raises(ContractError, match="CONTRACT_INSTANCE_INVALID"):
        bundle.validate(ref, "USD\n", profile="portable-json/v1")
    bundle.validate(ref, "USD\n", profile="native-compat/v1")
    for pattern in ("a$b", r"\\$b"):
        with pytest.raises(ContractError, match="CONTRACT_SCHEMA_UNSUPPORTED"):
            bundle_for({"pattern": pattern})
    for pattern, value in ((r"\$", "$"), ("[$]", "$"), ("a$", "a"), ("a", "a")):
        bundle_for({"pattern": pattern}).validate(ref, value, profile="portable-json/v1")


def test_caller_cannot_select_annotation_data_as_a_schema():
    bundle = bundle_for({"default": {}, "examples": [{}], "properties": {"default": {}}})
    for pointer in ("/default", "/examples/0"):
        ref = ContractRef("test", "1", pointer)
        for operation in (
            lambda ref=ref: bundle.schema(ref),
            lambda ref=ref: bundle.metadata(ref),
            lambda ref=ref: bundle.validate(ref, 1, profile="portable-json/v1"),
        ):
            with pytest.raises(ContractError, match="CONTRACT_REFERENCE_UNRESOLVED"):
                operation()
    bundle.validate(ContractRef("test", "1", "/properties/default"), 1, profile="portable-json/v1")


@pytest.mark.parametrize(
    "value,expected",
    [
        (1.0, b"1"),
        (-0.0, b"0"),
        (1e-7, b"1e-7"),
        (1e-6, b"0.000001"),
        (5e-324, b"5e-324"),
        ({"é": "\n", "𝄞": 1e-7}, '{"é":"\\n","𝄞":1e-7}'.encode()),
    ],
)
def test_portable_bytes_use_ecmascript_binary64_and_unicode(value, expected):
    assert portable_json_bytes(value) == expected
    assert decode_json(expected, profile="portable-json/v1") == value
