"""F0012-S0004 AC1/AC3-AC5, S0002 AC2/AC4/AC5, S0003 AC1-AC5, S0005 AC1: compile."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from brain_contracts.schema_runtime import ContractRef, validate_contract
from brain_domain.ontology import definition_digest, manifest_digest, release_ref_for
from brain_ontology.compiler import (
    check_identity,
    check_release,
    compile_release,
    write_release,
)
from brain_ontology.errors import CompileFailed

FOUNDATION_REQUEST = "ontology/releases/foundation/1/release.yaml"


def _fail(request: Path, root: Path) -> list[str]:
    with pytest.raises(CompileFailed) as failed:
        compile_release(request, root=root)
    return [i.code for i in failed.value.issues]


REPO = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def foundation() -> Any:
    return compile_release(REPO / FOUNDATION_REQUEST, root=REPO)


def test_ac1_committed_lock_matches_a_fresh_compile(kit: Any) -> None:
    compiled = compile_release(kit.REPO / FOUNDATION_REQUEST, root=kit.REPO)
    assert check_release(compiled, kit.FOUNDATION_RELEASE, file=FOUNDATION_REQUEST) == []
    again = compile_release(kit.REPO / FOUNDATION_REQUEST, root=kit.REPO)
    assert again.files() == compiled.files()


def test_ac1_fresh_checkout_and_shuffled_source(tmp_path: Path, kit: Any) -> None:
    """A copy elsewhere with terms, constraints and keys reordered gives the same bytes."""
    original = compile_release(kit.REPO / FOUNDATION_REQUEST, root=kit.REPO)
    data = yaml.safe_load(kit.FOUNDATION.read_text(encoding="utf-8"))
    data["terms"].reverse()
    data["constraints"].reverse()
    data["projection"].reverse()
    data = {k: data[k] for k in reversed(list(data))}
    for name in (
        "planning-mds/domain",
        "planning-mds/examples/commercial-pc-account",
        "planning-mds/architecture",
    ):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    for ref in ("planning-mds/domain/glossary.md", "planning-mds/architecture/master-blueprint.md"):
        shutil.copy(kit.REPO / ref, tmp_path / ref)
    for ref in ("records.json", "cases.md"):
        shutil.copy(
            kit.REPO / "planning-mds/examples/commercial-pc-account" / ref,
            tmp_path / "planning-mds/examples/commercial-pc-account" / ref,
        )
    module = tmp_path / "ontology/modules/foundation/module.yaml"
    module.parent.mkdir(parents=True)
    module.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    (module.parent / "changes.yaml").write_text("change_records: []\n", encoding="utf-8")
    request = tmp_path / FOUNDATION_REQUEST
    request.parent.mkdir(parents=True)
    shutil.copy(kit.REPO / FOUNDATION_REQUEST, request)
    shuffled = compile_release(request, root=tmp_path)
    assert shuffled.files() == original.files()


def test_ac3_manifest_fields(foundation: Any) -> None:
    manifest = foundation.manifest
    validate_contract(
        ContractRef("ontology-release-manifest-v1", "1"), manifest, profile="portable-json/v1"
    )
    assert manifest["manifest_digest"] == manifest_digest(manifest)
    assert manifest["release_ref"] == release_ref_for(manifest["manifest_digest"])
    assert len(manifest["release_ref"]) == 78
    assert manifest["modules"][0]["id"] == "foundation"
    assert manifest["semantics"]["ruleset"] == "nebula-tbox-subset/v1"
    assert manifest["semantics"]["inference"] == ["subClassOf", "subPropertyOf", "inverseOf"]
    assert set(manifest["artifact_slots"]) == {"profiles", "templates", "compiler", "validation"}
    assert manifest["projection_mapping"]["version"] == "nebula-age-mapping/v1"
    assert "ontology_release_ref" in manifest["projection_mapping"]["required_context"]


def test_ac3_constraint_metadata_in_normalized_release(foundation: Any) -> None:
    constraints = foundation.normalized["modules"][0]["normalized"]["constraints"]
    assert len(constraints) == 7
    for c in constraints:
        for field in (
            "stage",
            "consumer",
            "applicability",
            "severity",
            "on_nonconformance",
            "data_basis",
        ):
            assert c[field]


def test_s0005_ac1_predicate_contracts_from_manifest(foundation: Any) -> None:
    predicates = {p["predicate_key"]: p for p in foundation.manifest["predicates"]}
    assert len(predicates) == 15
    assert predicates["fnd:accountOrganization@v1"]["temporal_kind"] == "ETERNAL"
    assert (
        predicates["fnd:accountOrganization@v1"]["term_iri"]
        == "urn:nebula:ont:foundation.account.organization"
    )
    assert predicates["fnd:roleCoveragePart@v1"]["member_key_source"] == "entity"
    assert predicates["fnd:operatesAt@v1"]["cardinality"] == "RELATIONSHIP"
    assert all(p["basis_required"] is False for p in predicates.values())


def test_s0003_ac1_classes(foundation: Any) -> None:
    terms = {
        r["iri"].removeprefix("urn:nebula:ont:"): r["term"] for r in foundation.normalized["terms"]
    }
    required = [
        "thing",
        "party",
        "person",
        "organization",
        "account",
        "place",
        "document",
        "agreement",
        "event",
        "process",
        "decision",
        "role",
        "time-interval",
        "amount",
        "measurement",
        "identifier",
    ]
    for name in required:
        assert terms[f"foundation.{name}"]["kind"] == "class"
    assert terms["foundation.person"]["parents"] == ["foundation.party"]
    assert terms["foundation.organization"]["parents"] == ["foundation.party"]
    subclasses_of_org = [
        t for t in terms.values() if "foundation.organization" in t.get("parents", [])
    ]
    assert subclasses_of_org == []


def test_s0003_ac2_temporal_kinds(foundation: Any) -> None:
    kinds = {
        p["term_iri"].removeprefix("urn:nebula:ont:foundation."): p["temporal_kind"]
        for p in foundation.manifest["predicates"]
    }
    assert kinds == {
        "organization.parent-organization": "STATE",
        "organization.operates-at": "STATE",
        "person.employed-by": "STATE",
        "account.organization": "ETERNAL",
        "account.status": "STATE",
        "account.parent-account": "STATE",
        "ownership-interest.owner": "ETERNAL",
        "ownership-interest.owned-organization": "ETERNAL",
        "ownership-interest.percentage": "STATE",
        "role-assignment.party": "STATE",
        "role-assignment.acted-for": "STATE",
        "role-assignment.role-kind": "ETERNAL",
        "role-assignment.scope": "ETERNAL",
        "role-assignment.coverage-part": "STATE",
        "role-assignment.authoritative-source": "STATE",
    }


def test_s0003_ac3_role_kinds(foundation: Any) -> None:
    kinds = [
        r["term"]
        for r in foundation.normalized["terms"]
        if r["term"].get("code_of") == "foundation.role-kind"
    ]
    names = {k["id"].rsplit(".", 1)[-1] for k in kinds}
    assert len(kinds) == 14
    assert {"first-named-insured", "additional-named-insured", "additional-insured"} <= names
    for kind in kinds:
        codes = kind.get("external_codes", {})
        assert codes.get("PartyRoleTypeCode_status") in {"existing", "proposed", "unmapped"}
        assert ("PartyRoleTypeCode" in codes) == (
            codes["PartyRoleTypeCode_status"] != "unmapped"
        ) or codes.get("PartyRoleTypeCode") is None


def test_s0003_ac4_scope_class(foundation: Any) -> None:
    terms = {r["term"]["id"]: r["term"] for r in foundation.normalized["terms"]}
    assert terms["foundation.role-assignment.scope"]["range"] == "foundation.role-scope"
    assert terms["foundation.account"]["parents"] == ["foundation.role-scope"]
    assert terms["foundation.role-assignment.coverage-part"]["cardinality"] == "MULTI"


def test_s0003_ac5_constraints_and_no_majority(foundation: Any) -> None:
    constraints = {
        c["id"]: c for c in foundation.normalized["modules"][0]["normalized"]["constraints"]
    }
    stages = {cid.rsplit(".", 1)[-1]: c["stage"] for cid, c in constraints.items()}
    assert stages["percentage-total"] == "canonical-admission"
    assert stages["one-parent-account"] == "example-validation"
    assert stages["one-account-organization"] == "authoring"
    ids = {r["term"]["id"] for r in foundation.normalized["terms"]}
    assert not any("majority" in i for i in ids)


def test_s0002_ac4_label_change_keeps_iri_and_digest() -> None:
    term = {
        "id": "demo.thing",
        "iri": "urn:nebula:ont:demo.thing",
        "kind": "class",
        "labels": {"en-US": "Thing"},
        "definition": "x" * 20,
    }
    renamed = {
        **term,
        "labels": {"en-US": "Object"},
        "aliases": [{"tag": "en-US", "value": "Thing"}],
    }
    assert definition_digest(term) == definition_digest(renamed)


def _locked(ws: Any, kit: Any, data: dict[str, Any], name: str = "demo") -> Path:
    request = ws.release(name, 1, {name: data})
    write_release(compile_release(request, root=ws.root), request.parent)
    return request.parent


def test_ac4_dependencies(ws: Any, kit: Any) -> None:
    base = kit.module()
    request = ws.release("demo", 1, {"demo": base})
    digest = compile_release(request, root=ws.root).manifest["modules"][0]["digest"]
    ext_terms = [kit.cls("ext.thing", ["demo.thing"])]
    good = kit.module(
        "ext", ext_terms, namespace="ext", dependencies=[f"demo@1#sha256:{digest}"], projection=[]
    )
    ok = ws.release("bundle", 1, {"demo": base, "ext": good})
    manifest = compile_release(ok, root=ws.root).manifest
    assert manifest["dependency_lock"] == [{"module": "ext", "requires": f"demo@1#sha256:{digest}"}]

    for dep in ("demo@latest", "demo@>=1#sha256:" + "0" * 64):
        bad = kit.module("ext", ext_terms, namespace="ext", dependencies=[dep], projection=[])
        assert "DEPENDENCY_UNRESOLVED" in _fail(
            ws.release("bundle", 2, {"demo": base, "ext": bad}), ws.root
        )
    wrong = kit.module(
        "ext", ext_terms, namespace="ext", dependencies=[f"demo@1#sha256:{'0' * 64}"], projection=[]
    )
    assert "DEPENDENCY_UNRESOLVED" in _fail(
        ws.release("bundle", 3, {"demo": base, "ext": wrong}), ws.root
    )
    missing = kit.module(
        "ext", ext_terms, namespace="ext", dependencies=[f"other@1#sha256:{digest}"], projection=[]
    )
    assert "DEPENDENCY_UNRESOLVED" in _fail(
        ws.release("bundle", 4, {"demo": base, "ext": missing}), ws.root
    )
    v2 = kit.module(version=2)
    v2["terms"] = [kit.cls("demo.v2-thing")]
    v2["projection"] = []
    assert "DEPENDENCY_UNRESOLVED" in _fail(
        ws.release("bundle", 5, {"demo": base, "demo2": v2}), ws.root
    )


def test_ac5_projection_uncovered(ws: Any, kit: Any) -> None:
    data = kit.module(projection=[])
    assert _fail(ws.release("demo", 1, {"demo": data}), ws.root) == ["PROJECTION_UNCOVERED"]


def test_ac5_projection_mapping_contents(foundation: Any) -> None:
    entries = {e["term_iri"]: e for e in foundation.projection["properties"]}
    assert len(entries) == 16
    child = entries["urn:nebula:ont:foundation.organization.child-organization"]
    assert child["disposition"] == "omitted" and child["reason"]
    parent = entries["urn:nebula:ont:foundation.organization.parent-organization"]
    assert (
        parent["label"] == "PARENT_ORGANIZATION"
        and parent["predicate_key"] == "fnd:parentOrganization@v1"
    )


def test_s0002_ac2_identity_reuse_rejected(ws: Any, kit: Any) -> None:
    _locked(ws, kit, kit.module())
    changed = kit.module()
    changed["terms"][1]["definition"] = "A different meaning for the same synthetic identifier."
    request = ws.release("demo", 2, {"demo": changed})
    assert "IDENTITY_REUSE_REJECTED" in _fail(request, ws.root)
    record = {
        "class": "semantic_change",
        "source_iris": ["urn:nebula:ont:demo.party"],
        "replacement_iris": ["urn:nebula:ont:demo.party"],
        "rationale": "Clarified meaning.",
    }
    request = ws.release("demo", 2, {"demo": changed}, changes=[record])
    assert (
        compile_release(request, root=ws.root).manifest["change_records"][0]["class"]
        == "semantic_change"
    )


def test_s0002_ac2_additive_axiom_keeps_iri(ws: Any, kit: Any) -> None:
    """EX-ONT-003: adding a superclass to a published term is additive, not reuse."""
    base = kit.module(
        terms=[
            kit.cls("demo.thing"),
            kit.cls("demo.a"),
            kit.cls("demo.b"),
            kit.prop("demo.a.p", "demo.a", "demo.b", local="p"),
        ]
    )
    _locked(ws, kit, base)
    grown = kit.deep(base)
    grown["terms"][1]["parents"] = ["demo.b"]
    compile_release(ws.release("demo", 2, {"demo": grown}), root=ws.root)


def test_s0002_ac5_removal_needs_retirement(ws: Any, kit: Any) -> None:
    lock = _locked(ws, kit, kit.module())
    smaller = kit.module()
    smaller["terms"] = smaller["terms"][:2]
    smaller["projection"] = []
    request = ws.release("demo", 2, {"demo": smaller}, predecessor=f"../{lock.name}")
    assert "TERM_REMOVED_WITHOUT_RETIREMENT" in _fail(request, ws.root)
    retire = {
        "class": "retirement",
        "source_iris": ["urn:nebula:ont:demo.party.parent"],
        "replacement_iris": [],
        "rationale": "Unused.",
    }
    request = ws.release(
        "demo", 2, {"demo": smaller}, changes=[retire], predecessor=f"../{lock.name}"
    )
    assert compile_release(request, root=ws.root).manifest["change_records"] == [retire]


def test_s0002_ac5_change_record_shapes(ws: Any, kit: Any) -> None:
    _locked(ws, kit, kit.module())
    cases = [
        {
            "class": "split",
            "source_iris": ["urn:nebula:ont:demo.party"],
            "replacement_iris": ["urn:nebula:ont:demo.thing"],
            "rationale": "x",
        },
        {
            "class": "merge",
            "source_iris": ["urn:nebula:ont:demo.party"],
            "replacement_iris": ["urn:nebula:ont:demo.thing"],
            "rationale": "x",
        },
        {
            "class": "retirement",
            "source_iris": ["urn:nebula:ont:demo.party"],
            "replacement_iris": ["urn:nebula:ont:demo.thing"],
            "rationale": "x",
        },
        {
            "class": "rename",
            "source_iris": ["urn:nebula:ont:demo.party"],
            "replacement_iris": [],
            "rationale": "x",
        },
        {
            "class": "semantic_change",
            "source_iris": ["urn:nebula:ont:demo.never"],
            "replacement_iris": ["urn:nebula:ont:demo.party"],
            "rationale": "",
        },
        {"class": "semantic_change", "source_iris": [], "replacement_iris": [], "rationale": "x"},
        {
            "class": "semantic_change",
            "source_iris": ["urn:nebula:ont:demo.party"],
            "replacement_iris": ["urn:nebula:ont:demo.absent"],
            "rationale": "x",
        },
    ]
    for record in cases:
        request = ws.release("demo", 2, {"demo": kit.module()}, changes=[record])
        assert "CHANGE_RECORD_INVALID" in _fail(request, ws.root), record


def test_check_identity_direct() -> None:
    history = {"urn:nebula:ont:a.b": {"d1": {"id": "a.b", "kind": "class", "parents": []}}}
    term = {"id": "a.b", "kind": "class", "parents": [], "definition": "changed"}
    issues = check_identity(
        {"urn:nebula:ont:a.b": term}, history=history, predecessor=[], change_records=[], file="r"
    )
    assert [i.code for i in issues] == ["IDENTITY_REUSE_REJECTED"]


def test_authoring_constraints_execute(ws: Any, kit: Any) -> None:
    multi = kit.module(constraints=[kit.constraint("demo.c.one")])
    multi["terms"][2]["cardinality"] = "MULTI"
    assert "AUTHORING_CONSTRAINT_VIOLATED" in _fail(ws.release("demo", 1, {"demo": multi}), ws.root)

    terms = [
        kit.cls("demo.thing"),
        kit.cls("demo.party", ["demo.thing"]),
        kit.cls("demo.scope", ["demo.thing"]),
        kit.cls("demo.account", ["demo.scope"]),
        kit.prop("demo.party.scope", "demo.party", "demo.scope", local="scope"),
        kit.prop(
            "demo.party.narrow",
            "demo.party",
            "demo.account",
            local="narrow",
            sub_property_of=["demo.party.scope"],
        ),
    ]
    rng = kit.constraint("demo.c.range", construct="range", property="demo.party.scope", value=None)
    del rng["value"]
    ok = kit.module(terms=terms, constraints=[rng])
    compile_release(ws.release("demo", 1, {"demo": ok}), root=ws.root)
    bad = kit.deep(ok)
    bad["terms"][5]["range"] = "demo.party"  # a non-member scope (S0003 AC4)
    assert "AUTHORING_CONSTRAINT_VIOLATED" in _fail(ws.release("demo", 1, {"demo": bad}), ws.root)

    dom = kit.constraint(
        "demo.c.dom", construct="domain", subject="demo.scope", property="demo.party.scope"
    )
    del dom["value"]
    assert "AUTHORING_CONSTRAINT_VIOLATED" in _fail(
        ws.release("demo", 1, {"demo": kit.module(terms=terms, constraints=[dom])}), ws.root
    )
    dis = kit.constraint(
        "demo.c.dis", construct="disjoint", subject="demo.scope", **{"with": ["demo.thing"]}
    )
    del dis["value"], dis["property"]
    assert "AUTHORING_CONSTRAINT_VIOLATED" in _fail(
        ws.release("demo", 1, {"demo": kit.module(terms=terms, constraints=[dis])}), ws.root
    )


def test_cross_module_collision_and_duplicate_keys(ws: Any, kit: Any) -> None:
    a = kit.module("demo")
    b = kit.module(
        "other",
        [kit.cls("demo.thing"), kit.prop("other.p", "demo.thing", "demo.thing", local="parent")],
        namespace="dmo",
    )
    codes = _fail(ws.release("bundle", 1, {"demo": a, "other": b}), ws.root)
    assert "IRI_COLLISION" in codes


def test_release_request_invalid(ws: Any) -> None:
    request = ws.write("r.yaml", {"name": "x"})
    assert _fail(request, ws.root).count("RELEASE_REQUEST_INVALID") == 2
    assert _fail(ws.write("r2.yaml", None, raw="- a\n"), ws.root) == ["RELEASE_REQUEST_INVALID"]


def test_check_release_reports_stale_outputs(tmp_path: Path, foundation: Any) -> None:
    issues = check_release(foundation, tmp_path, file="r.yaml")
    assert sorted(i.code for i in issues) == ["OUTPUT_STALE"] * 5
    write_release(foundation, tmp_path)
    assert check_release(foundation, tmp_path, file="r.yaml") == []
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["release_ref"] == foundation.release_ref
