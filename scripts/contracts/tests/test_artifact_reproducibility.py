"""Real builder determinism, failed publication rollback and drift injection."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "generate.py"
SPEC = importlib.util.spec_from_file_location("contract_generate", SCRIPT)
generate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate)


@pytest.fixture(scope="module")
def outputs(tmp_path_factory):
    directory = tmp_path_factory.mktemp("first-build")
    first = generate.build(directory)
    second = generate.build(tmp_path_factory.mktemp("second-build"))
    assert first == second
    return first


def test_every_declared_snapshot_and_model_is_reproducible(outputs):
    assert len(outputs) > 70
    for name, raw in outputs.items():
        assert (generate.ROOT / name).read_bytes() == raw, name
        assert b"/tmp/" not in raw and str(generate.ROOT).encode() not in raw


def test_bundle_copies_are_identical(outputs):
    root = "schemas/contracts/v1/"
    for name, raw in outputs.items():
        if name.startswith(root):
            suffix = name.removeprefix(root)
            for target in generate.RESOURCE_ROOTS:
                assert outputs[target + "/" + suffix] == raw


def test_failed_publication_restores_previous_coherent_files(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    for name in ("a", "b", "manifest.json"):
        (tmp_path / name).write_bytes(b"previous")
        (tmp_path / name).chmod(0o600)
    replace = generate.os.replace
    calls = 0

    def fail_on_second(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected publication failure")
        replace(source, target)

    monkeypatch.setattr(generate.os, "replace", fail_on_second)
    with pytest.raises(OSError):
        generate.publish({"a": b"new", "b": b"new", "manifest.json": b"new"})
    assert all(
        (tmp_path / name).read_bytes() == b"previous"
        for name in ("a", "b", "manifest.json")
    )
    assert {path.name for path in tmp_path.iterdir()} == {"a", "b", "manifest.json"}
    assert all(
        (tmp_path / name).stat().st_mode & 0o777 == 0o600
        for name in ("a", "b", "manifest.json")
    )


def test_published_contracts_are_readable_by_the_runtime_user(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    generate.publish({"bundle/schema.json": b"{}", "bundle/manifest.json": b"{}"})
    assert all(
        path.stat().st_mode & 0o777 == 0o644 for path in (tmp_path / "bundle").iterdir()
    )


@pytest.mark.parametrize(
    "suffix",
    [
        "engine/packages/brain-contracts/src/brain_contracts/generated/contracts_v1.py",
        "schemas/contracts/v1/ui-metadata.json",
        "experience/src/generated/contracts/v1/fact-answer-v1.schema.json",
        "engine/packages/brain-contracts/src/brain_contracts/resources/v1/brain-api.openapi.json",
    ],
)
def test_check_refuses_tampered_generated_artifact_without_writing(
    outputs, tmp_path, monkeypatch, capsys, suffix
):
    # Use actual fully built outputs, then inject one model/schema/metadata/API drift.
    for name, raw in outputs.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    target = tmp_path / suffix
    target.write_bytes(target.read_bytes() + b" ")
    before = target.read_bytes()
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    monkeypatch.setattr(generate, "build", lambda scratch: outputs)
    monkeypatch.setattr(sys, "argv", ["generate.py", "--check"])
    assert generate.main() == 1
    assert target.read_bytes() == before
    report = json.loads(capsys.readouterr().out)
    assert suffix in report["stale"]


def test_case_join_refuses_missing_duplicate_or_changed_results(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "contract_check", SCRIPT.parent / "check.py"
    )
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    case = {
        "id": "F0011-C0001",
        "contract": "fact-answer-v1.schema.json",
        "version": "1",
        "valid": True,
    }

    def result(consumer):
        return {
            **{key: case[key] for key in ("id", "contract", "version")},
            "consumer": consumer,
            "accepted": True,
        }

    python = {
        "bundle_digest": "a",
        "cases": [result("jsonschema"), result("pydantic")],
        "versions": {},
    }
    ajv = {"bundle_digest": "a", "cases": [result("ajv")], "versions": {}}
    assert check.join([case], python, ajv)["status"] == "pass"
    with pytest.raises(ValueError):
        check.join([case], python, {**ajv, "cases": []})
    with pytest.raises(ValueError):
        check.join([case], python, {**ajv, "cases": ajv["cases"] * 2})
    with pytest.raises(ValueError):
        check.join([case], python, {**ajv, "bundle_digest": "wrong"})
    changed = {**ajv, "cases": [{**result("ajv"), "accepted": False}]}
    assert check.join([case], python, changed)["status"] == "fail"
    assert check.join([{**case, "valid": False}], python, ajv)["status"] == "fail"
    complete = json.loads((SCRIPT.parent / "cases.json").read_bytes())["cases"]
    canonical = complete[0]
    seed = tmp_path / "case-expectation.json"
    seed.write_text(json.dumps({"cases": [canonical]}))
    assert len(check.cases_from(seed)) == len(complete)
    seed.write_text(
        json.dumps({"cases": [{**canonical, "valid": not canonical["valid"]}]})
    )
    with pytest.raises(ValueError, match="expectation differs"):
        check.cases_from(seed)
