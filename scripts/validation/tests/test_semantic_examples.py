from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/validation/validate_semantic_examples.py"
spec = importlib.util.spec_from_file_location("semantic_examples", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.fixture
def records():
    return json.loads((ROOT / validator.BUNDLE).read_text())


def validate_gl_records(records):
    schema = json.loads((ROOT / validator.SCHEMA).read_text())
    return validator.validate_records(ROOT, records, schema)


def test_repository_example_and_markdown_links_resolve():
    assert validator.validate_examples(ROOT) == []


@pytest.mark.parametrize("field,value", [
    ("fact_ref", "EX-F-MISSING"),
    ("rule_ref", "EX-RULE-MISSING"),
    ("subject_ref", "EX-COV-MISSING"),
])
def test_dangling_assessment_lineage_is_rejected(records, field, value):
    records["assessments"][0][field] = value
    assert any("dangling" in item for item in validate_gl_records(records))


def test_duplicate_identity_is_rejected(records):
    records["facts"].append(dict(records["facts"][0]))
    assert any("Duplicate record ID" in item for item in validate_gl_records(records))


@pytest.mark.parametrize("mutation", ["numeric_money", "confidence", "timestamp", "invalid_date", "unlabeled_output", "operator"])
def test_malformed_or_misleading_records_fail_schema(records, mutation):
    if mutation == "numeric_money":
        records["facts"][0]["amount"] = 500000.0
    elif mutation == "confidence":
        records["assertions"][0]["model_confidence"] = 1.1
    elif mutation == "timestamp":
        records["assessments"][0]["known_as_of"] = "July 8"
    elif mutation == "invalid_date":
        records["assessments"][0]["known_as_of"] = "2026-02-30T00:00:00Z"
    elif mutation == "unlabeled_output":
        records["status"] = "executed"
    elif mutation == "operator":
        records["rules"][0]["operation"] = "execute_logic_string"
    assert validate_gl_records(records)


def test_source_and_provenance_links_are_not_silently_accepted(records):
    records["evidence"][0]["source_ref"] = "source-package.md#missing-region"
    assert any("missing heading" in item for item in validate_gl_records(records))
    records["evidence"][0]["source_ref"] = "../../../../../../outside.md"
    assert any("escapes product" in item for item in validate_gl_records(records))


def test_quoted_teaching_evidence_must_exist(records):
    records["evidence"][0]["quote"] = "A nonexistent source statement."
    assert any("quote missing" in item for item in validate_gl_records(records))


def test_structure_check_does_not_claim_to_execute_reasoning(records):
    # Runtime conformance is a separate future gate; this check is deliberately
    # limited to structure and references, not a second implementation of rules.
    records["assessments"][0]["outcome"] = "MEETS_GUIDELINE"
    assert validate_gl_records(records) == []


def _load(name: str):
    module_spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/validation/{name}.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


snapshot_builder = _load("build_commercial_pc_snapshot")
rdf_checker = _load("validate_semantic_rdf")
PC_FOLDER = ROOT / snapshot_builder.FOLDER


def test_commercial_snapshot_projections_are_generated_from_records():
    records = json.loads((PC_FOLDER / "records.json").read_text(encoding="utf-8"))
    outputs = snapshot_builder.build(records)
    for name, text in outputs.items():
        assert (PC_FOLDER / name).read_text(encoding="utf-8") == text, name
    # Simple literals keep sh:hasValue shapes matching (rdflib compares terms).
    assert "^^xsd:string" not in outputs["snapshot.ttl"]


def test_commercial_snapshot_drift_is_reported(tmp_path, monkeypatch, capsys):
    folder = tmp_path / snapshot_builder.FOLDER
    folder.mkdir(parents=True)
    for name in ("records.json", *snapshot_builder.OUTPUTS):
        (folder / name).write_bytes((PC_FOLDER / name).read_bytes())
    with (folder / "snapshot.ttl").open("a", encoding="utf-8") as handle:
        handle.write("d:EX-PC-ACCOUNT pc:groupsParty d:EX-PC-MGA .\n")
    monkeypatch.setattr("sys.argv", ["build", "--product-root", str(tmp_path), "--check"])
    assert snapshot_builder.main() == 1
    assert "snapshot.ttl" in capsys.readouterr().out
    assert "groupsParty d:EX-PC-MGA" in (folder / "snapshot.ttl").read_text(encoding="utf-8")  # --check writes nothing


def test_commercial_rdf_expectations_hold():
    pytest.importorskip("rdflib")
    pytest.importorskip("pyshacl")
    pytest.importorskip("owlrl")
    assert rdf_checker.check_bundle(PC_FOLDER) == []


def test_typed_string_literals_break_completeness_shapes(tmp_path, monkeypatch):
    pytest.importorskip("rdflib")
    pytest.importorskip("pyshacl")
    pytest.importorskip("owlrl")
    import shutil
    folder = tmp_path / "bundle"
    shutil.copytree(PC_FOLDER, folder)
    monkeypatch.setattr(snapshot_builder, "SIMPLE_LITERAL", "__never__")
    outputs = snapshot_builder.build(json.loads((folder / "records.json").read_text(encoding="utf-8")))
    for name, text in outputs.items():
        (folder / name).write_text(text, encoding="utf-8")
    findings = rdf_checker.check_bundle(folder)
    assert any("gl-completeness.ttl on snapshot.ttl" in item for item in findings)


def _at(day: str):
    return snapshot_builder.stamp(f"{day}T00:00:00Z")


@pytest.mark.parametrize("valid_time,day,expected", [
    ({"kind": "ETERNAL"}, "1999-01-01", "VALUE"),
    ({"kind": "EVENT", "at": "2026-06-21T00:00:00Z", "granularity": "DAY"}, "2026-06-20", None),
    ({"kind": "EVENT", "at": "2026-06-21T00:00:00Z", "granularity": "DAY"}, "2026-07-05", "VALUE"),
    # Unknown start is never widened to "since always".
    ({"kind": "STATE", "from": None, "from_granularity": None, "attested_from": "2025-12-15T00:00:00Z",
      "to": None, "to_state": "OPEN", "to_granularity": None}, "2025-06-01", "UNKNOWN"),
    ({"kind": "STATE", "from": "2026-01-01T00:00:00Z", "from_granularity": "DAY", "attested_from": "2025-12-22T00:00:00Z",
      "to": "2027-01-01T00:00:00Z", "to_state": "BOUNDED", "to_granularity": "DAY"}, "2025-12-31", None),
    ({"kind": "STATE", "from": "2026-01-01T00:00:00Z", "from_granularity": "DAY", "attested_from": "2025-12-22T00:00:00Z",
      "to": "2027-01-01T00:00:00Z", "to_state": "BOUNDED", "to_granularity": "DAY"}, "2027-01-01", None),
    # An undated end reads UNKNOWN until the reporting document, then absent.
    ({"kind": "STATE", "from": None, "from_granularity": None, "attested_from": "2025-12-15T00:00:00Z",
      "to": None, "to_state": "UNKNOWN", "to_granularity": None, "attested_to": "2026-05-15T00:00:00Z"}, "2026-03-01", "UNKNOWN"),
    ({"kind": "STATE", "from": None, "from_granularity": None, "attested_from": "2025-12-15T00:00:00Z",
      "to": None, "to_state": "UNKNOWN", "to_granularity": None, "attested_to": "2026-05-15T00:00:00Z"}, "2026-05-15", None),
])
def test_valid_time_readings_follow_adr_0064(valid_time, day, expected):
    assert snapshot_builder.read_valid(valid_time, _at(day)) == expected


@pytest.fixture
def pc_root(tmp_path):
    import shutil
    shutil.copytree(PC_FOLDER, tmp_path / snapshot_builder.FOLDER)
    schema = ROOT / "planning-mds/schemas/commercial-pc-example.schema.json"
    (tmp_path / "planning-mds/schemas").mkdir(parents=True)
    shutil.copy(schema, tmp_path / "planning-mds/schemas" / schema.name)
    return tmp_path


def _mutate_records(root, change):
    path = root / snapshot_builder.FOLDER / "records.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    return validator.validate_commercial_example(root)


def test_commercial_fixture_copy_is_clean(pc_root):
    assert validator.validate_commercial_example(pc_root) == []


def test_policy_year_cannot_be_assumed_for_eternal_properties(pc_root):
    def change(data):
        fact = next(f for f in data["facts"] if f["id"] == "EX-PC-F-018")  # policyNumber is ETERNAL
        fact["valid_time"] = {"kind": "STATE", "from": "2026-01-01T00:00:00Z", "from_granularity": "DAY",
                              "attested_from": "2025-12-22T00:00:00Z", "to": "2027-01-01T00:00:00Z",
                              "to_state": "BOUNDED", "to_granularity": "DAY"}
    assert any("temporal_kind" in item for item in _mutate_records(pc_root, change))


def test_unknown_end_requires_an_undated_ending_reading(pc_root):
    def change(data):
        next(a for a in data["assertions"] if a["id"] == "EX-PC-A-YARD-ENDED").pop("time_shape")
    assert any("ENDED_UNDATED" in item for item in _mutate_records(pc_root, change))


def test_document_date_must_be_stated_in_the_source(pc_root):
    def change(data):
        data["evidence"][0]["document_date"] = "2025-11-01T00:00:00Z"
    findings = _mutate_records(pc_root, change)
    assert any("document date not stated" in item for item in findings)
    assert any("attestation differs" in item for item in findings)
