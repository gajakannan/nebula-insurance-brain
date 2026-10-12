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
        handle.write("d:EX-PC-ACCOUNT-RIDGE pc:parentAccount d:EX-PC-ACCOUNT .\n")
    monkeypatch.setattr("sys.argv", ["build", "--product-root", str(tmp_path), "--check"])
    assert snapshot_builder.main() == 1
    assert "snapshot.ttl" in capsys.readouterr().out
    assert "EX-PC-ACCOUNT-RIDGE pc:parentAccount" in (folder / "snapshot.ttl").read_text(encoding="utf-8")  # --check writes nothing


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



def _swap_contacts(records):
    objects = {a["id"]: a["object"] for a in records["assertions"]}
    for assertion in records["assertions"]:
        if assertion["id"] == "EX-PC-A-AUTO-BROKER-CONTACT-PARTY":
            assertion["object"] = objects["EX-PC-A-UMBRELLA-BROKER-CONTACT-PARTY"]
        elif assertion["id"] == "EX-PC-A-UMBRELLA-BROKER-CONTACT-PARTY":
            assertion["object"] = objects["EX-PC-A-AUTO-BROKER-CONTACT-PARTY"]


def _set_object(assertion_id, value):
    def mutate(records):
        next(a for a in records["assertions"] if a["id"] == assertion_id)["object"] = value
    return mutate


def _drop_bop_placement_broker(records):
    gone = {a["id"] for a in records["assertions"] if a["subject_ref"] == "EX-PC-ASSIGN-BOP-BROKER"}
    records["assertions"] = [a for a in records["assertions"] if a["id"] not in gone]
    records["facts"] = [f for f in records["facts"] if f["assertion_ref"] not in gone]


# Counterexamples from the PR #19 review: each keeps every query's row count but must still fail.
@pytest.mark.parametrize("mutate, expected", [
    (_swap_contacts, "broker-contact-reach.rq: forbidden row"),
    (_set_object("EX-PC-A-PARENT-CONTRACTOR", {"ref": "EX-PC-ACCOUNT-CONTRACTOR"}),
     "shapes.ttl on snapshot.ttl"),
    (_set_object("EX-PC-A-OWN-RIDGE-PERCENT", {"value": "80.00", "datatype": "xsd:decimal"}),
     "shapes.ttl on snapshot.ttl"),
    (_drop_bop_placement_broker, "EX-PC-POLICY-BOP, EX-BOP-100, EX-PC-PRODUCT-BOP, EX-PC-MAPLE, EX-PC-BROKER, broker of record"),
])
def test_commercial_account_counterexamples_are_caught(tmp_path, mutate, expected):
    pytest.importorskip("rdflib")
    pytest.importorskip("pyshacl")
    pytest.importorskip("owlrl")
    import shutil
    folder = tmp_path / "bundle"
    shutil.copytree(PC_FOLDER, folder)
    records = json.loads((folder / "records.json").read_text(encoding="utf-8"))
    mutate(records)
    for name, text in snapshot_builder.build(records).items():
        (folder / name).write_text(text, encoding="utf-8")
    findings = "\n".join(rdf_checker.check_bundle(folder))
    assert expected in findings.replace("'", "")

def _at(day: str):
    return snapshot_builder.stamp(f"{day}T00:00:00Z")


@pytest.mark.parametrize("policy,relation", [("GL", "owner"), ("AUTO", "named insured")])
@pytest.mark.parametrize("role_state", ["missing", "expired"])
def test_account_360_keeps_ownership_independent_of_current_insured_roles(policy, relation, role_state):
    rdflib = pytest.importorskip("rdflib")
    records = json.loads((PC_FOLDER / "records.json").read_text(encoding="utf-8"))
    assignment = f"EX-PC-ASSIGN-{policy}-CONTRACTOR"
    assertions = {a["id"]: a for a in records["assertions"]}
    if role_state == "missing":
        records["entities"] = [e for e in records["entities"] if e["id"] != assignment]
        records["facts"] = [f for f in records["facts"]
                            if assertions[f["assertion_ref"]]["subject_ref"] != assignment]
    else:
        fact = next(f for f in records["facts"]
                    if assertions[f["assertion_ref"]]["subject_ref"] == assignment
                    and assertions[f["assertion_ref"]]["predicate"] == "pc:roleParty")
        fact["valid_time"].update(to=records["snapshot"]["valid_as_of"], to_state="BOUNDED", to_granularity="DAY")
    graph = rdflib.Graph().parse(data=snapshot_builder.build(records)["snapshot.ttl"], format="turtle")
    query = (PC_FOLDER / "queries/account-360-contracting.rq").read_text(encoding="utf-8")
    rows = sorted([rdf_checker.render(v) for v in row] for row in graph.query(query))
    expected = [
        ["EX-PC-POLICY-AUTO", "EX-2042", "named insured", "EX-PC-ROLE-AdditionalNamedInsured"],
        ["EX-PC-POLICY-GL", "EX-2042", "owner", "EX-PC-ROLE-FirstNamedInsured"],
        ["EX-PC-POLICY-PROGRAM-CONTRACTOR", "EX-PROP-100-C", "owner", "EX-PC-ROLE-FirstNamedInsured"],
        ["EX-PC-POLICY-UMBRELLA", "EX-UMB-100", "named insured", "EX-PC-ROLE-AdditionalNamedInsured"],
    ]
    if relation == "owner":
        expected[1][3] = ""  # Ownership supplies no evidence of the insured role.
    else:
        expected.pop(0)  # A non-owned policy still needs a current named-insured role.
    assert rows == expected


def test_closed_account_allows_replacement_without_erasing_history():
    rdflib = pytest.importorskip("rdflib")
    shacl = pytest.importorskip("pyshacl")
    graph = rdflib.Graph().parse(PC_FOLDER / "boundaries/account-close-reopen.ttl")
    shapes = rdflib.Graph().parse(PC_FOLDER / "shapes.ttl")
    conforms, _, report = shacl.validate(graph, shacl_graph=shapes, inference="none")
    assert conforms, report
    pc = rdflib.Namespace(snapshot_builder.PREFIXES["pc"])
    d = rdflib.Namespace(snapshot_builder.PREFIXES["d"])
    assert set(graph.subjects(pc.accountOrganization, d["EX-PC-GAP-ORG"])) == {
        d["EX-PC-GAP-ACCOUNT-OLD"], d["EX-PC-GAP-ACCOUNT-NEW"]}
    assert (d["EX-PC-GAP-POLICY"], pc.forAccount, d["EX-PC-GAP-ACCOUNT-OLD"]) in graph
    graph.set((d["EX-PC-GAP-ACCOUNT-OLD"], pc.accountStatus, rdflib.Literal("CURRENT")))
    conforms, results, _ = shacl.validate(graph, shacl_graph=shapes, inference="none")
    assert not conforms
    assert pc.OneAccountPerOrganizationShape in results.objects(predicate=rdflib.SH.sourceShape)


@pytest.mark.parametrize("statuses", [[], ["UNKNOWN"], ["CURRENT", "CLOSED"]])
def test_account_lifecycle_must_be_known_and_single_valued(statuses):
    rdflib = pytest.importorskip("rdflib")
    shacl = pytest.importorskip("pyshacl")
    pc = rdflib.Namespace(snapshot_builder.PREFIXES["pc"])
    d = rdflib.Namespace(snapshot_builder.PREFIXES["d"])
    graph = rdflib.Graph().parse(PC_FOLDER / "boundaries/account-close-reopen.ttl")
    account = d["EX-PC-GAP-ACCOUNT-OLD"]
    graph.remove((account, pc.accountStatus, None))
    for status in statuses:
        graph.add((account, pc.accountStatus, rdflib.Literal(status)))
    conforms, results, _ = shacl.validate(graph, shacl_graph=rdflib.Graph().parse(PC_FOLDER / "shapes.ttl"))
    assert not conforms
    assert pc.accountStatus in results.objects(predicate=rdflib.SH.resultPath)


@pytest.mark.parametrize("valid,known,old_status,new_status", [
    ("2026-06-30", "2026-07-11", "CURRENT", None),
    ("2026-07-01", "2026-07-09", "CURRENT", None),
    ("2026-07-01", "2026-07-11", "CLOSED", "CURRENT"),
    ("2026-07-05", "2026-07-11", "CLOSED", "CURRENT"),
])
def test_account_replacement_status_uses_valid_and_known_time(valid, known, old_status, new_status):
    import copy
    rdflib = pytest.importorskip("rdflib")
    shacl = pytest.importorskip("pyshacl")
    records = json.loads((PC_FOLDER / "records.json").read_text(encoding="utf-8"))
    old = "EX-PC-ACCOUNT-RIDGE"
    replacement = "EX-PC-ACCOUNT-RIDGE-REPLACEMENT"
    effective, recorded = "2026-07-01T00:00:00Z", "2026-07-10T00:00:00Z"
    original = next(f for f in records["facts"] if f["id"] == "EX-PC-F-STATUS-ACCOUNT-RIDGE")
    original["recorded_to"] = recorded
    retained = copy.deepcopy(original)
    retained.update(id="EX-PC-F-STATUS-RIDGE-RETAINED", recorded_from=recorded, recorded_to=None)
    retained["valid_time"].update(to=effective, to_state="BOUNDED", to_granularity="DAY")
    closed_assertion = copy.deepcopy(next(a for a in records["assertions"] if a["id"] == original["assertion_ref"]))
    closed_assertion.update(id="EX-PC-A-STATUS-RIDGE-CLOSED", object={"value": "CLOSED", "datatype": "xsd:string"})
    closed = copy.deepcopy(retained)
    closed.update(id="EX-PC-F-STATUS-RIDGE-CLOSED", assertion_ref=closed_assertion["id"])
    closed["valid_time"].update({"from": effective, "from_granularity": "DAY", "to": None,
                               "to_state": "OPEN", "to_granularity": None, "attested_from": recorded})
    records["assertions"].append(closed_assertion)
    records["facts"].extend([retained, closed])

    entity = copy.deepcopy(next(e for e in records["entities"] if e["id"] == old))
    entity.update(id=replacement, label="Ridge replacement account")
    records["entities"].append(entity)
    # Synthetic mutation of the teaching records, solely to exercise projection selection.
    for predicate, value in [("pc:accountOrganization", {"ref": "EX-PC-RIDGE"}),
                             ("pc:accountStatus", {"value": "CURRENT", "datatype": "xsd:string"})]:
        field = predicate.removeprefix("pc:")
        slot_id = f"EX-PC-SLOT-REPLACEMENT-{field}"
        records["slots"].append({"id": slot_id, "subject_ref": replacement, "predicate": predicate,
                                 "qualifiers": {"target_ref": value["ref"]} if "ref" in value else {}})
        assertion = dict(closed_assertion, id=f"EX-PC-A-REPLACEMENT-{field}", subject_ref=replacement,
                         predicate=predicate, object=value)
        fact = copy.deepcopy(closed)
        fact.update(id=f"EX-PC-F-REPLACEMENT-{field}", slot_id=slot_id, assertion_ref=assertion["id"])
        if predicate == "pc:accountOrganization":
            fact["valid_time"] = {"kind": "ETERNAL"}
        records["assertions"].append(assertion)
        records["facts"].append(fact)
    records["snapshot"] = {"valid_as_of": f"{valid}T00:00:00Z", "known_as_of": f"{known}T00:00:00Z"}
    graph = rdflib.Graph().parse(data=snapshot_builder.build(records)["snapshot.ttl"], format="turtle")
    pc = rdflib.Namespace(snapshot_builder.PREFIXES["pc"])
    d = rdflib.Namespace(snapshot_builder.PREFIXES["d"])
    assert set(graph.objects(d[old], pc.accountStatus)) == {rdflib.Literal(old_status)}
    assert set(graph.objects(d[replacement], pc.accountStatus)) == (
        {rdflib.Literal(new_status)} if new_status else set())
    assert (d[old], pc.accountOrganization, d["EX-PC-RIDGE"]) in graph
    if new_status:
        assert set(graph.subjects(pc.accountOrganization, d["EX-PC-RIDGE"])) == {d[old], d[replacement]}
        conforms, _, report = shacl.validate(graph, shacl_graph=rdflib.Graph().parse(PC_FOLDER / "shapes.ttl"))
        assert conforms, report


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
