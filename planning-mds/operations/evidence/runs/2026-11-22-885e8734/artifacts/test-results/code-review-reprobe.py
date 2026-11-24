"""Independent replay of the four original F0011 review findings."""
import hashlib
import json
from pathlib import Path

from brain_contracts.model_adapter import model_for, parse_model
from brain_contracts.schema_runtime import ContractBundle, ContractError, ContractRef, MAX_BYTES


def outcome(operation):
    try:
        operation()
        return "accepted"
    except ContractError as error:
        return error.code


bundle = ContractBundle.installed()
portable = "portable-json/v1"
open_ref = ContractRef("assertion-record-v2", "2", "/$defs/qualifiers/additionalProperties")
results = {}
deep = "[" * 128 + "0" + "]" * 128
results["depth128_decode"] = outcome(lambda: bundle.decode(deep, profile=portable))
results["depth128_direct"] = outcome(lambda: bundle.validate(open_ref, json.loads(deep), profile=portable))
ref = ContractRef("qualified-money-v1", "1")
money = {"type": "money", "amount": "1\n", "currency": "USD"}
results["money_newline_jsonschema"] = outcome(lambda: bundle.validate(ref, money, profile=portable))
results["money_newline_pydantic"] = outcome(lambda: parse_model(ref, json.dumps(money), model_for(ref), profile=portable))
results["money_newline_native_unchanged"] = outcome(lambda: bundle.validate(ref, money, profile="native-compat/v1"))
head, tail = '{"n":1e-7,"p":"', '"}'
raw = head + "x" * (MAX_BYTES - len(head) - len(tail)) + tail
value = bundle.decode(raw, profile=portable)
results["max_bytes_decode"] = len(raw) == MAX_BYTES
results["max_bytes_jsonschema"] = outcome(lambda: bundle.validate(open_ref, value, profile=portable))
results["max_bytes_pydantic"] = outcome(lambda: parse_model(open_ref, raw, model_for(open_ref), profile=portable))

# This separately constructs a trusted synthetic annotation-bearing resource;
# the current 21 resources need not contain an object-valued annotation.
identity = "https://nebula.local/schemas/reviewer-test.schema.json"
schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": identity,
          "default": {}, "examples": [{}], "properties": {"default": {}}}
schema_raw = json.dumps(schema).encode()
tools = dict(bundle._manifest["toolchain"])
manifest = {"bundle": "brain-contracts/v1", "profile": "nebula-json-schema/1", "toolchain": tools,
            "resources": [{"id": identity, "version": "1", "path": "reviewer-test.schema.json",
                           "sha256": hashlib.sha256(schema_raw).hexdigest()}]}
synthetic = ContractBundle(json.dumps(manifest).encode(), lambda name: schema_raw)
for pointer in ("/default", "/examples/0"):
    selected = ContractRef("reviewer-test", "1", pointer)
    results["annotation_schema:" + pointer] = outcome(lambda: synthetic.schema(selected))
    results["annotation_metadata:" + pointer] = outcome(lambda: synthetic.metadata(selected))
    results["annotation_validate:" + pointer] = outcome(lambda: synthetic.validate(selected, 1, profile=portable))
results["real_default_property"] = outcome(lambda: synthetic.validate(ContractRef("reviewer-test", "1", "/properties/default"), 1, profile=portable))

expected = {"depth128_decode": "CONTRACT_JSON_UNSUPPORTED", "depth128_direct": "CONTRACT_JSON_UNSUPPORTED",
            "money_newline_jsonschema": "CONTRACT_INSTANCE_INVALID", "money_newline_pydantic": "CONTRACT_INSTANCE_INVALID",
            "money_newline_native_unchanged": "accepted", "max_bytes_decode": True,
            "max_bytes_jsonschema": "accepted", "max_bytes_pydantic": "accepted", "real_default_property": "accepted"}
for pointer in ("/default", "/examples/0"):
    for action in ("schema", "metadata", "validate"):
        expected["annotation_" + action + ":" + pointer] = "CONTRACT_REFERENCE_UNRESOLVED"
report = {"status": "pass" if results == expected else "fail", "reviewer": "Codex / independent Code Reviewer",
          "bundle_digest": bundle.digest, "results": results}
Path(__file__).with_name("code-review-reprobe-python.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
raise SystemExit(0 if report["status"] == "pass" else 1)
