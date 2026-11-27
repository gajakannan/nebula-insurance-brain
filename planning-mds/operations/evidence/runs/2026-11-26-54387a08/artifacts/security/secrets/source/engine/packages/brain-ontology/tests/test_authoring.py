"""F0012-S0001 AC1-AC7 and S0002 AC1/AC3/AC6: offline authoring validation."""

from __future__ import annotations

from typing import Any

import pytest
import yaml
from brain_domain.ontology import TERM_ID, term_iri
from brain_ontology.authoring import resolve_reference, validate_document, validate_module


def _validate(ws: Any, data: dict[str, Any]) -> list[tuple[str, str]]:
    path = ws.write("ontology/modules/demo/module.yaml", data)
    result = validate_module(path, repo_root=ws.root)
    return [(i.code, i.path) for i in result.issues]


def _codes(ws: Any, data: dict[str, Any]) -> set[str]:
    return {code for code, _ in _validate(ws, data)}


def test_ac1_foundation_module_validates_and_names_the_schema(kit: Any) -> None:
    result = validate_module(kit.FOUNDATION, repo_root=kit.REPO)
    assert result.ok, result.issues
    summary = result.summary()
    assert summary["authoring_schema"] == "ontology-module-authoring/v1"
    assert summary["module"] == "foundation@1"
    assert summary["terms"] == 53 and summary["predicates"] == 15


def test_ac1_minimal_module_is_valid(ws: Any, kit: Any) -> None:
    assert _validate(ws, kit.module()) == []


def test_ac2_singular_parent_is_retired(ws: Any, kit: Any) -> None:
    data = kit.module()
    term = data["terms"][1]
    del term["parents"]
    term["parent"] = "demo.thing"
    issues = validate_module(ws.write("m.yaml", data), repo_root=ws.root).issues
    retired = [i for i in issues if i.code == "AUTHORING_FIELD_RETIRED"]
    assert len(retired) == 1
    assert retired[0].file == "m.yaml" and "demo.party" in retired[0].message
    assert "parents" in retired[0].message


def test_ac2_empty_parents_is_a_root(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][1]["parents"] = []
    assert _validate(ws, data) == []


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("definition", "", "DEFINITION_REQUIRED"),
        ("examples", [], "EXAMPLE_REQUIRED"),
        ("regression_cases", [], "REGRESSION_CASE_REQUIRED"),
    ],
)
def test_ac3_definition_examples_regressions_required(
    ws: Any, kit: Any, field: str, value: Any, code: str
) -> None:
    data = kit.module()
    data["terms"][0][field] = value
    assert code in _codes(ws, data)


def test_ac3_missing_fields_each_reported(ws: Any, kit: Any) -> None:
    data = kit.module()
    for name in ("definition", "examples", "regression_cases"):
        del data["terms"][0][name]
    codes = [c for c, _ in _validate(ws, data)]
    assert codes.count("DEFINITION_REQUIRED") == 1
    assert codes.count("EXAMPLE_REQUIRED") == 1
    assert codes.count("REGRESSION_CASE_REQUIRED") == 1


def test_ac3_unresolved_references(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][0]["examples"] = ["missing.md"]
    data["terms"][0]["regression_cases"] = ["ex.md#EX-404"]
    data["terms"][1]["parents"] = ["demo.unknown"]
    found = _validate(ws, data)
    assert ("REFERENCE_UNRESOLVED", "$.terms[0].examples[0]") in found
    assert ("REFERENCE_UNRESOLVED", "$.terms[0].regression_cases[0]") in found
    assert ("REFERENCE_UNRESOLVED", "$.terms[1].parents[0]") in found


def test_ac3_reference_rules(ws: Any) -> None:
    assert resolve_reference("ex.md", ws.root)
    assert resolve_reference("ex.md#EX-1", ws.root)
    assert not resolve_reference("ex.md#EX-10", ws.root)
    assert not resolve_reference("../ex.md", ws.root)
    assert not resolve_reference("/etc/passwd", ws.root)


def test_ac4_labels(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][0]["labels"] = {"fr-FR": "Chose"}
    data["terms"][1]["labels"] = {"en-US": "Party", "EN_us": "bad"}
    data["terms"][2]["aliases"] = [{"tag": "not a tag", "value": "x"}]
    codes = _codes(ws, data)
    assert {"LABEL_EN_US_REQUIRED", "LABEL_TAG_INVALID"} <= codes


def test_ac4_duplicate_preferred_label_in_one_tag(ws: Any, kit: Any) -> None:
    text = yaml.safe_dump(kit.module(), sort_keys=False).replace(
        "    en-US: Thing\n", "    en-US: Thing\n    en-US: Other\n", 1
    )
    path = ws.write("m.yaml", None, raw=text)
    issues = validate_module(path, repo_root=ws.root).issues
    assert [i.code for i in issues] == ["LABEL_PREFERRED_DUPLICATE"]


@pytest.mark.parametrize("value", [None, "INSTANT", "state"])
def test_ac5_temporal_kind_required_and_closed(ws: Any, kit: Any, value: Any) -> None:
    data = kit.module()
    if value is None:
        del data["terms"][2]["temporal_kind"]
    else:
        data["terms"][2]["temporal_kind"] = value
    assert "TEMPORAL_KIND_INVALID" in _codes(ws, data)


@pytest.mark.parametrize("construct", ["symmetric", "transitive", "equivalent_class", "functional"])
def test_ac6_unsupported_term_constructs(ws: Any, kit: Any, construct: str) -> None:
    data = kit.module()
    data["terms"][2][construct] = True
    issues = validate_module(ws.write("m.yaml", data), repo_root=ws.root).issues
    assert [i.code for i in issues] == ["UNSUPPORTED_CONSTRUCT"]
    assert construct in issues[0].message


def test_ac6_unsupported_constraint_construct(ws: Any, kit: Any) -> None:
    data = kit.module(constraints=[kit.constraint("demo.c.one", construct="equivalentClass")])
    assert "UNSUPPORTED_CONSTRUCT" in _codes(ws, data)
    data = kit.module(
        constraints=[kit.constraint("demo.c.one", construct="custom", expression="x")]
    )
    assert "UNSUPPORTED_CONSTRUCT" in _codes(ws, data)  # custom cannot run at authoring


@pytest.mark.parametrize(
    "missing", ["stage", "consumer", "applicability", "severity", "on_nonconformance", "data_basis"]
)
def test_ac7_constraint_execution_context(ws: Any, kit: Any, missing: str) -> None:
    c = kit.constraint("demo.c.one")
    del c[missing]
    found = _validate(ws, kit.module(constraints=[c]))
    assert ("CONSTRAINT_CONTEXT_INCOMPLETE", f"$.constraints[0].{missing}") in found


def test_ac7_inferred_basis_names_the_ruleset(ws: Any, kit: Any) -> None:
    ok = kit.constraint("demo.c.one", data_basis={"inferred": "nebula-tbox-subset/v1"})
    assert _validate(ws, kit.module(constraints=[ok])) == []
    bad = kit.constraint("demo.c.one", data_basis={"inferred": "owl-full"})
    assert "CONSTRAINT_CONTEXT_INCOMPLETE" in _codes(ws, kit.module(constraints=[bad]))


def test_ac7_all_errors_in_deterministic_order(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][0]["definition"] = ""
    data["terms"][1]["labels"] = {"de-DE": "Partei"}
    data["terms"][2]["temporal_kind"] = "NOW"
    data["terms"][2]["symmetric"] = True
    first = _validate(ws, data)
    second = _validate(ws, data)
    assert first == second
    assert first == sorted(first, key=lambda x: (x[1], x[0]))
    assert len(first) >= 4


def test_ac7_yaml_error_is_one_error_with_position(ws: Any) -> None:
    path = ws.write("m.yaml", None, raw="terms: [\n  - id: a\n")
    issues = validate_module(path, repo_root=ws.root).issues
    assert len(issues) == 1 and issues[0].code == "YAML_INVALID"
    assert "line" in issues[0].message


def test_s0002_ac1_iri_mapping_and_grammar(ws: Any, kit: Any) -> None:
    assert term_iri("foundation.account.status") == "urn:nebula:ont:foundation.account.status"
    for bad in (
        "Foundation.account",
        "foundation.açcount",
        "foundation",
        "foundation..x",
        "a." + "b" * 49,
    ):
        assert not TERM_ID.match(bad)
        with pytest.raises(ValueError):
            term_iri(bad)
    data = kit.module()
    data["terms"][0]["id"] = "Demo.Thing"
    assert "TERM_ID_INVALID" in _codes(ws, data)


def test_s0002_ac3_duplicate_ids_collide(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"].append(kit.deep(data["terms"][0]))
    issues = validate_module(ws.write("m.yaml", data), repo_root=ws.root).issues
    assert [i.code for i in issues] == ["IRI_COLLISION"]


def test_s0002_ac3_cross_module_collision(ws: Any, kit: Any) -> None:
    data = kit.module()
    external = {"demo.thing": {"id": "demo.thing", "kind": "class"}}
    result = validate_document(data, file="m.yaml", repo_root=ws.root, external=external)
    assert "IRI_COLLISION" in {i.code for i in result.issues}


def test_s0002_ac6_tenant_namespace_reserved(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][2]["range"] = "urn:nebula:tenant:00000000-0000-4000-8000-000000000001:ont:x"
    data["terms"].append(kit.cls("tenant.custom"))
    codes = [c for c, _ in _validate(ws, data)]
    assert codes.count("TENANT_NAMESPACE_RESERVED") == 2


def test_predicate_keys_unique_and_valid(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"].append(kit.prop("demo.party.other", "demo.party", "demo.party", local="parent"))
    assert "PREDICATE_KEY_DUPLICATE" in _codes(ws, data)
    data = kit.module()
    data["terms"][0]["predicate"] = {"local_name": "thing", "major": 1}
    data["terms"][0]["value_type"] = "text"
    data["terms"][0]["cardinality"] = "SINGLE"
    assert "PREDICATE_KEY_INVALID" in _codes(ws, data)


def test_inverse_property_declares_no_predicate(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"].append(
        kit.prop(
            "demo.party.child",
            "demo.party",
            "demo.party",
            local="child",
            inverse_of="demo.party.parent",
        )
    )
    assert "PREDICATE_KEY_INVALID" in _codes(ws, data)


def test_value_type_shape_checks(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"].append(
        kit.prop(
            "demo.party.rel",
            "demo.party",
            "demo.party",
            local="rel",
            value_type="text",
            cardinality="RELATIONSHIP",
        )
    )
    assert "SCHEMA_INVALID" in _codes(ws, data)


def test_class_only_fields_on_properties(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"][0]["domain"] = "demo.party"
    assert "UNSUPPORTED_CONSTRUCT" in _codes(ws, data)


def test_code_value_needs_class(ws: Any, kit: Any) -> None:
    data = kit.module()
    data["terms"].append(
        {
            "id": "demo.thing.code",
            "kind": "code_value",
            "labels": {"en-US": "Code"},
            "definition": "A synthetic code value for the code_of check.",
            "examples": ["ex.md"],
            "regression_cases": ["ex.md"],
            "code_of": "demo.party.parent",
        }
    )
    assert "REFERENCE_UNRESOLVED" in _codes(ws, data)


def test_unreadable_file(ws: Any) -> None:
    issues = validate_module(ws.root / "nope.yaml", repo_root=ws.root).issues
    assert [i.code for i in issues] == ["YAML_INVALID"]
