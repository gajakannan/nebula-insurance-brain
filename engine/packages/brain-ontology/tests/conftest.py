"""Fixture builders for F0012 offline tests. Every fixture is synthetic and lives
in a temporary root, except tests that read the committed foundation module."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO = Path(__file__).resolve().parents[4]
FOUNDATION = REPO / "ontology" / "modules" / "foundation" / "module.yaml"
FOUNDATION_RELEASE = REPO / "ontology" / "releases" / "foundation" / "1"


def cls(term_id: str, parents: list[str] | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "id": term_id,
        "kind": "class",
        "labels": {"en-US": term_id.rsplit(".", 1)[-1].title()},
        "definition": f"Synthetic test class {term_id} for F0012 fixtures.",
        "parents": parents or [],
        "examples": ["ex.md#EX-1"],
        "regression_cases": ["ex.md"],
        **extra,
    }


def prop(
    term_id: str,
    domain: str,
    range_: str,
    *,
    kind: str = "object_property",
    temporal_kind: str = "STATE",
    local: str | None = None,
    value_type: str = "entity_ref",
    cardinality: str = "SINGLE",
    **extra: Any,
) -> dict[str, Any]:
    term: dict[str, Any] = {
        "id": term_id,
        "kind": kind,
        "labels": {"en-US": term_id.rsplit(".", 1)[-1]},
        "definition": f"Synthetic test property {term_id} for F0012 fixtures.",
        "domain": domain,
        "range": range_,
        "temporal_kind": temporal_kind,
        "examples": ["ex.md#EX-1"],
        "regression_cases": ["ex.md"],
        **extra,
    }
    if local is not None:
        term["predicate"] = {"local_name": local, "major": 1}
        term["value_type"] = value_type
        term["cardinality"] = cardinality
    return term


def module(
    module_id: str = "demo",
    terms: list[dict[str, Any]] | None = None,
    *,
    version: int = 1,
    namespace: str = "dmo",
    dependencies: list[str] | None = None,
    constraints: list[dict[str, Any]] | None = None,
    projection: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    terms = (
        terms
        if terms is not None
        else [
            cls("demo.thing"),
            cls("demo.party", ["demo.thing"]),
            prop("demo.party.parent", "demo.party", "demo.party", local="parent"),
        ]
    )
    if projection is None:
        projection = [
            {
                "property": t["id"],
                "disposition": "edge",
                "label": "REL",
                "direction": "subject-to-object",
            }
            for t in terms
            if t["kind"] in {"object_property", "datatype_property"}
        ]
    data: dict[str, Any] = {
        "authoring_schema": "ontology-module-authoring/v1",
        "module": {
            "id": module_id,
            "version": version,
            "predicate_namespace": namespace,
            "dependencies": dependencies or [],
        },
        "terms": terms,
        "projection": projection,
    }
    if constraints is not None:
        data["constraints"] = constraints
    return data


def constraint(cid: str, **overrides: Any) -> dict[str, Any]:
    base = {
        "id": cid,
        "construct": "maxCardinality",
        "subject": "demo.party",
        "property": "demo.party.parent",
        "value": 1,
        "stage": "authoring",
        "consumer": "test compiler",
        "applicability": "every party",
        "severity": "violation",
        "on_nonconformance": "refuse the release",
        "data_basis": "asserted",
    }
    base.update(overrides)
    return base


class Workspace:
    """A temporary repository root with a reference file and release folders."""

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "ex.md").write_text("# Examples\n\nEX-1 a synthetic case.\n", encoding="utf-8")

    def write(self, relative: str, data: Any, *, raw: str | None = None) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            raw if raw is not None else yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )
        return path

    def release(
        self,
        name: str,
        sequence: int,
        modules: dict[str, dict[str, Any]],
        *,
        changes: list[dict[str, Any]] | None = None,
        predecessor: str | None = None,
    ) -> Path:
        directory = f"ontology/releases/{name}/{sequence}"
        entries = []
        for module_name, data in modules.items():
            self.write(f"ontology/modules/{module_name}/module.yaml", data)
            entries.append(f"../../../modules/{module_name}/module.yaml")
        request: dict[str, Any] = {"name": name, "sequence": sequence, "modules": entries}
        if changes is not None:
            self.write(f"{directory}/changes.yaml", {"change_records": changes})
            request["changes"] = ["changes.yaml"]
        if predecessor is not None:
            request["predecessor"] = predecessor
        return self.write(f"{directory}/release.yaml", request)


@pytest.fixture
def ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path)


def deep(data: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(data)


@pytest.fixture
def kit() -> Any:
    """Builders for test modules (importlib mode cannot import conftest directly)."""
    from types import SimpleNamespace

    return SimpleNamespace(
        cls=cls,
        prop=prop,
        module=module,
        constraint=constraint,
        deep=deep,
        REPO=REPO,
        FOUNDATION=FOUNDATION,
        FOUNDATION_RELEASE=FOUNDATION_RELEASE,
    )
