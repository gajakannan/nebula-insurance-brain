"""Execute only from the fresh, offline installation environment."""

from __future__ import annotations

import copy
import importlib
import importlib.metadata
import json
import pathlib
import socket
import sys


def blocked(*args, **kwargs):
    raise AssertionError("Network use forbidden during installed contract proof")


socket.create_connection = blocked
socket.socket.connect = blocked

from brain_content.manifest import parse_manifest
from brain_contracts.dispatch import parse_result
from brain_contracts.model_adapter import model_for, parse_model, to_wire
from brain_contracts.schema_runtime import (
    ContractBundle,
    ContractError,
    ContractRef,
)


def main() -> None:
    if (
        pathlib.Path("/app/brain/planning-mds").exists()
        or pathlib.Path("/app/brain/engine").exists()
    ):
        raise AssertionError("Source checkout must be unavailable")
    prefixes = {}
    for name in ("brain_domain", "brain_content", "brain_contracts"):
        location = pathlib.Path(importlib.import_module(name).__file__).resolve()
        if not location.is_relative_to(pathlib.Path(sys.prefix).resolve()):
            raise AssertionError(
                "Editable/source import leaked into the installation proof"
            )
        prefixes[name] = str(location.relative_to(sys.prefix))
    bundle = ContractBundle.installed()
    fixtures = json.loads(pathlib.Path("/packages/fixtures.json").read_bytes())
    preparation = json.loads(pathlib.Path("/packages/preparation.json").read_bytes())
    if bundle.digest != preparation["bundle_digest"]:
        raise AssertionError("Installed bundle differs from candidate")
    for case in fixtures:
        original = copy.deepcopy(case["input"])
        ref = ContractRef(case["contract"], case["version"])
        raw = json.dumps(original).encode()
        bundle.validate(
            ref,
            bundle.decode(raw, profile="portable-json/v1"),
            profile="portable-json/v1",
        )
        model = parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
        if to_wire(ref, model, profile="portable-json/v1") != original:
            raise AssertionError("Installed generated-model round trip lost data")
        if case["contract"].startswith("content-artifact-manifest"):
            parse_manifest(raw)
        elif case["contract"].startswith("interpretation-result"):
            parse_result(raw)
        if case["input"] != original:
            raise AssertionError("Consumer mutated the fixture")
    try:
        bundle.validate(
            ContractRef("fact-answer-v1", "999"), {}, profile="portable-json/v1"
        )
    except ContractError as error:
        if error.code != "CONTRACT_VERSION_UNSUPPORTED":
            raise
    else:
        raise AssertionError("Unknown version accepted")
    print(
        json.dumps(
            {
                "status": "pass",
                "bundle_digest": bundle.digest,
                "fixture_ids": [case["id"] for case in fixtures],
                "native_readers": [
                    "content-v1",
                    "content-v2",
                    "assertion-v1",
                    "assertion-v2",
                ],
                "installed_paths": prefixes,
                "versions": {
                    name: importlib.metadata.version(name)
                    for name in (
                        "brain-domain",
                        "brain-contracts",
                        "brain-content",
                        "pydantic",
                        "jsonschema",
                        "referencing",
                    )
                },
                "checkout_unavailable": True,
                "network_blocked": True,
            }
        )
    )


if __name__ == "__main__":
    main()
