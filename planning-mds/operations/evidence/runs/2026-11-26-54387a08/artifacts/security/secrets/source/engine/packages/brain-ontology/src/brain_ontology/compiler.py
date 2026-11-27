"""Deterministic release compile (F0012-S0004 AC1-AC5, S0002, S0005 AC1; ADR-0081 D3).

A release request (`release.yaml`) names the release, its sequence, the module
files and, optionally, the predecessor lock directory. The compiler validates
every module, resolves exact dependencies, checks identity against every
committed lock, executes the `authoring`-stage constraints, builds the projection
mapping and writes five files. The same sources give byte-identical output in
any order on any machine.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_contracts.schema_runtime import ContractError, ContractRef, validate_contract
from brain_domain.ontology import (
    AUTHORING_SCHEMA,
    IRI_PREFIX,
    MANIFEST_CONTRACT,
    RULESET,
    definition_digest,
    manifest_digest,
    only_added_axioms,
    release_ref_for,
    sha256_jcs,
    term_iri,
)

from brain_ontology import COMPILER_VERSION
from brain_ontology.authoring import PROPERTY_KINDS, _Collector, load_yaml, validate_document
from brain_ontology.errors import Code, CompileFailed, Issue
from brain_ontology.rdf_export import to_jsonld, to_turtle, triples
from brain_ontology.semantics import closure

MANIFEST_REF = ContractRef("ontology-release-manifest-v1", "1")
MAPPING_VERSION = "nebula-age-mapping/v1"
NORMALIZED_CONTRACT = "ontology-release-normalized/v1"
REQUIRED_CONTEXT = (
    "tenant_id",
    "knowledge_base_id",
    "valid_as_of",
    "known_as_of",
    "source_fact_version_ids",
    "source_relationship_version_ids",
    "assertion_refs",
    "evidence_refs",
    "ontology_release_ref",
    "mapping_version",
    "asserted_or_derived_basis",
)
OUTPUT_FILES = (
    "manifest.json",
    "normalized.json",
    "projection-mapping.json",
    "release.ttl",
    "release.jsonld",
)
CHANGE_CLASSES = ("rename_alias", "semantic_change", "split", "merge", "retirement")
_SET_FIELDS = ("parents", "sub_property_of", "examples", "regression_cases")


@dataclass(frozen=True, slots=True)
class CompiledRelease:
    name: str
    sequence: int
    manifest: dict[str, Any]
    normalized: dict[str, Any]
    projection: dict[str, Any]
    turtle: str
    jsonld: str

    @property
    def release_ref(self) -> str:
        return str(self.manifest["release_ref"])

    def files(self) -> dict[str, bytes]:
        return {
            "manifest.json": dump_json(self.manifest),
            "normalized.json": dump_json(self.normalized),
            "projection-mapping.json": dump_json(self.projection),
            "release.ttl": self.turtle.encode("utf-8"),
            "release.jsonld": self.jsonld.encode("utf-8"),
        }


def dump_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


# --- normalization --------------------------------------------------------------


def normalize_term(term: Mapping[str, Any], namespace: str) -> dict[str, Any]:
    out: dict[str, Any] = {k: v for k, v in term.items() if k != "predicate"}
    out["iri"] = term_iri(term["id"])
    for name in _SET_FIELDS:
        if name in out:
            out[name] = sorted(out[name])
    if "aliases" in out:
        out["aliases"] = sorted(out["aliases"], key=lambda a: (a["tag"], a["value"]))
    predicate = term.get("predicate")
    if predicate is not None:
        out["predicate_key"] = f"{namespace}:{predicate['local_name']}@v{predicate['major']}"
    return out


def normalize_module(module: Mapping[str, Any]) -> dict[str, Any]:
    meta = dict(module["module"])
    meta["dependencies"] = sorted(meta.get("dependencies", []))
    namespace = meta["predicate_namespace"]
    terms = sorted((normalize_term(t, namespace) for t in module["terms"]), key=lambda t: t["iri"])
    constraints = []
    for constraint in module.get("constraints", []):
        item = dict(constraint)
        if "with" in item:
            item["with"] = sorted(item["with"])
        constraints.append(item)
    return {
        "authoring_schema": AUTHORING_SCHEMA,
        "module": meta,
        "terms": terms,
        "constraints": sorted(constraints, key=lambda c: c["id"]),
        "projection": sorted(module.get("projection", []), key=lambda r: r["property"]),
    }


def predicate_entry(term: Mapping[str, Any]) -> dict[str, Any]:
    cardinality = term["cardinality"]
    value_type = term["value_type"]
    member = None
    if cardinality == "MULTI":
        member = "entity" if value_type == "entity_ref" else "value"
    return {
        "term_iri": term["iri"],
        "predicate_key": term["predicate_key"],
        "cardinality": cardinality,
        "value_type": value_type,
        "temporal_kind": term["temporal_kind"],
        "qualifiers": [],
        "member_key_source": member,
        "basis_required": value_type == "money",
    }


# --- history ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LockedTerm:
    iri: str
    digest: str
    release: str


def read_lock(directory: Path) -> dict[str, LockedTerm]:
    normalized = json.loads((directory / "normalized.json").read_text(encoding="utf-8"))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    ref = manifest["release_ref"]
    return {
        t["iri"]: LockedTerm(t["iri"], t["definition_digest"], ref) for t in normalized["terms"]
    }


def identity_history(
    root: Path, *, exclude: Path | None = None
) -> dict[str, dict[str, Mapping[str, Any]]]:
    """IRI -> {definition digest: normalized term} for every committed release lock."""
    history: dict[str, dict[str, Mapping[str, Any]]] = {}
    base = root / "ontology" / "releases"
    if not base.is_dir():
        return history
    for manifest in sorted(base.glob("*/*/manifest.json")):
        directory = manifest.parent
        if exclude is not None and directory.resolve() == exclude.resolve():
            continue
        normalized = json.loads((directory / "normalized.json").read_text(encoding="utf-8"))
        for row in normalized["terms"]:
            history.setdefault(row["iri"], {})[row["definition_digest"]] = row["term"]
    return history


def check_identity(
    candidate: Mapping[str, Mapping[str, Any]],
    *,
    history: Mapping[str, Mapping[str, Mapping[str, Any]]],
    predecessor: Iterable[str],
    change_records: Sequence[Mapping[str, Any]],
    file: str,
) -> list[Issue]:
    """S0002 AC2/AC5. `candidate` maps IRI -> normalized term. A new definition for
    a published IRI needs a change record, unless it only adds `parents` /
    `sub_property_of` axioms (a monotonic additive edit, EX-ONT-003); the impact
    report then shows its entailment change."""
    covered = {iri for record in change_records for iri in record["source_iris"]}
    issues: list[Issue] = []
    for iri, term in sorted(candidate.items()):
        known = history.get(iri)
        digest = definition_digest(term)
        if not known or digest in known or iri in covered:
            continue
        if any(only_added_axioms(previous, term) for previous in known.values()):
            continue
        issues.append(
            Issue(
                file,
                f"$.terms[{iri}]",
                Code.IDENTITY_REUSE_REJECTED.value,
                f"{iri} was published with another definition; declare a change record",
            )
        )
    for iri in sorted(set(predecessor) - set(candidate)):
        if iri not in covered:
            issues.append(
                Issue(
                    file,
                    f"$.terms[{iri}]",
                    Code.TERM_REMOVED_WITHOUT_RETIREMENT.value,
                    f"{iri} is in the predecessor but missing without a change record",
                )
            )
    return issues


def check_change_records(
    records: Sequence[Mapping[str, Any]], *, candidate: set[str], known: set[str], file: str
) -> list[Issue]:
    issues: list[Issue] = []

    def bad(index: int, message: str) -> None:
        issues.append(
            Issue(file, f"$.change_records[{index}]", Code.CHANGE_RECORD_INVALID.value, message)
        )

    for index, record in enumerate(records):
        cls = record.get("class")
        sources = record.get("source_iris")
        targets = record.get("replacement_iris")
        if cls not in CHANGE_CLASSES:
            bad(index, f"unknown change class {cls!r}")
            continue
        if not isinstance(sources, list) or not sources or not isinstance(targets, list):
            bad(index, "source_iris (non-empty) and replacement_iris are required")
            continue
        if not str(record.get("rationale", "")).strip():
            bad(index, "a rationale is required")
        shape = {
            "retirement": len(targets) == 0,
            "split": len(sources) == 1 and len(targets) >= 2,
            "merge": len(sources) >= 2 and len(targets) == 1,
        }.get(cls, len(targets) >= 1)
        if not shape:
            bad(index, f"{cls} has the wrong number of source or replacement IRIs")
        for iri in sources:
            if iri not in known:
                bad(index, f"source {iri} was never published")
        for iri in targets:
            if iri not in candidate:
                bad(index, f"replacement {iri} is not in the candidate release")
    return issues


# --- authoring-stage constraints ---------------------------------------------------


def run_authoring_constraints(
    terms: Mapping[str, Mapping[str, Any]], constraints: list[tuple[str, Mapping[str, Any]]]
) -> list[Issue]:
    entailed = closure(terms.values())
    sub = {(e.subject, e.object) for e in entailed if e.relation == "subClassOf"}
    subprop = {(e.subject, e.object) for e in entailed if e.relation == "subPropertyOf"}
    issues: list[Issue] = []

    def is_sub(a: str, b: str) -> bool:
        return (IRI_PREFIX + a, IRI_PREFIX + b) in sub

    for file, constraint in constraints:
        if constraint.get("stage") != "authoring":
            continue
        cid = constraint["id"]
        construct = constraint["construct"]
        prop = terms.get(constraint.get("property", ""))

        def fail(message: str, file: str = file, cid: str = cid) -> None:
            issues.append(
                Issue(
                    file,
                    f"$.constraints[{cid}]",
                    Code.AUTHORING_CONSTRAINT_VIOLATED.value,
                    f"{cid}: {message}",
                )
            )

        if construct in {"domain", "range", "minCardinality", "maxCardinality"} and prop is None:
            fail("property does not resolve")
            continue
        if construct == "maxCardinality":
            assert prop is not None
            if int(constraint["value"]) <= 1 and prop.get("cardinality") != "SINGLE":
                fail(f"{prop['id']} must be a SINGLE slot")
            if not is_sub(constraint["subject"], prop["domain"]) and not is_sub(
                prop["domain"], constraint["subject"]
            ):
                fail(f"{prop['id']} does not apply to {constraint['subject']}")
        elif construct == "domain":
            assert prop is not None
            if not is_sub(prop["domain"], constraint["subject"]):
                fail(f"{prop['id']} domain is outside {constraint['subject']}")
        elif construct == "range":
            assert prop is not None
            target = (constraint.get("with") or [prop["range"]])[0]
            for other in terms.values():
                if other.get("kind") not in PROPERTY_KINDS:
                    continue
                governed = other["id"] == prop["id"] or (other["iri"], prop["iri"]) in subprop
                if governed and not is_sub(other["range"], target):
                    fail(f"{other['id']} range {other['range']} is not a member of {target}")
        elif construct == "disjoint":
            for other in constraint.get("with", []):
                shared = [
                    t
                    for t in terms.values()
                    if t.get("kind") == "class"
                    and is_sub(t["id"], constraint["subject"])
                    and is_sub(t["id"], other)
                ]
                if shared:
                    fail(f"{shared[0]['id']} is under both {constraint['subject']} and {other}")
    return issues


# --- projection -----------------------------------------------------------------------


def build_projection(
    modules: list[tuple[str, dict[str, Any]]], terms: Mapping[str, Mapping[str, Any]]
) -> tuple[dict[str, Any], list[Issue]]:
    issues: list[Issue] = []
    entries = []
    for file, module in modules:
        rules = {r["property"]: r for r in module.get("projection", [])}
        for term in module["terms"]:
            if term["kind"] not in PROPERTY_KINDS:
                continue
            rule = rules.get(term["id"])
            if rule is None:
                issues.append(
                    Issue(
                        file,
                        f"$.projection[{term['id']}]",
                        Code.PROJECTION_UNCOVERED.value,
                        f"{term['id']} is neither mapped nor omitted",
                    )
                )
                continue
            entry: dict[str, Any] = {
                "term_iri": term_iri(term["id"]),
                "disposition": rule["disposition"],
            }
            if rule["disposition"] == "omitted":
                entry["reason"] = rule["reason"]
            else:
                entry["label"] = rule["label"]
                if "direction" in rule:
                    entry["direction"] = rule["direction"]
                entry["subject_types"] = [term_iri(term["domain"])]
                rng = term["range"]
                entry["object_types"] = [rng if rng.startswith("xsd:") else term_iri(rng)]
                if term.get("predicate_key"):
                    entry["predicate_key"] = term["predicate_key"]
            entries.append(entry)
    mapping = {
        "version": MAPPING_VERSION,
        "required_context": list(REQUIRED_CONTEXT),
        "properties": sorted(entries, key=lambda e: e["term_iri"]),
    }
    return mapping, issues


# --- release ------------------------------------------------------------------------------


def _request(path: Path, root: Path) -> tuple[dict[str, Any], list[Issue]]:
    out = _Collector(_rel(path, root))
    data = load_yaml(path, out)
    issues = list(out.issues)
    if not isinstance(data, Mapping):
        if not issues:
            issues.append(
                Issue(
                    out.file,
                    "$",
                    Code.RELEASE_REQUEST_INVALID.value,
                    "a release request is a mapping",
                )
            )
        return {}, issues
    for key, kind in (("name", str), ("sequence", int), ("modules", list)):
        if not isinstance(data.get(key), kind):
            issues.append(
                Issue(
                    out.file, f"$.{key}", Code.RELEASE_REQUEST_INVALID.value, f"{key} is required"
                )
            )
    return dict(data), issues


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def compile_release(request_path: Path, *, root: Path) -> CompiledRelease:
    """Compile or raise `CompileFailed` with every error, sorted."""
    request, issues = _request(request_path, root)
    if issues:
        raise CompileFailed(issues)
    request_file = _rel(request_path, root)
    base = request_path.parent

    # 1. Load every module, then validate each with the others as external terms.
    loaded: list[tuple[str, Any, _Collector]] = []
    for entry in request["modules"]:
        path = (base / entry).resolve() if not Path(entry).is_absolute() else Path(entry)
        file = _rel(path, root)
        out = _Collector(file)
        loaded.append((file, load_yaml(path, out), out))
    by_file_terms: dict[str, dict[str, Mapping[str, Any]]] = {}
    for file, data, _ in loaded:
        raw_terms = data.get("terms") if isinstance(data, Mapping) else None
        by_file_terms[file] = {
            t["id"]: t
            for t in (raw_terms or [])
            if isinstance(t, Mapping) and isinstance(t.get("id"), str)
        }
    modules: list[tuple[str, dict[str, Any]]] = []
    for file, data, out in loaded:
        if any(i.code == Code.YAML_INVALID for i in out.issues):
            issues.extend(out.issues)
            continue
        external = {k: v for f, ts in by_file_terms.items() if f != file for k, v in ts.items()}
        result = validate_document(
            data, file=file, repo_root=root, external=external, collector=out
        )
        issues.extend(result.issues)
        if result.ok:
            modules.append((file, dict(data)))
    if issues:
        raise CompileFailed(issues)

    # 2. Normalize and resolve exact dependencies (S0004 AC4).
    normalized = [(file, normalize_module(m)) for file, m in modules]
    digests = {file: sha256_jcs(n) for file, n in normalized}
    by_id: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for file, n in normalized:
        by_id.setdefault(n["module"]["id"], []).append((file, n))
    for module_id, members in sorted(by_id.items()):
        if len(members) > 1:
            for file, _ in members:
                issues.append(
                    Issue(
                        file,
                        "$.module.id",
                        Code.DEPENDENCY_UNRESOLVED.value,
                        f"two versions of module {module_id} in one release",
                    )
                )
    lock: list[dict[str, str]] = []
    for file, n in normalized:
        for dep in n["module"]["dependencies"]:
            name, _, rest = dep.partition("@")
            version, _, digest = rest.partition("#sha256:")
            match = [
                f
                for f, m in by_id.get(name, [])
                if str(m["module"]["version"]) == version and digests[f] == digest
            ]
            if len(match) != 1:
                issues.append(
                    Issue(
                        file,
                        "$.module.dependencies",
                        Code.DEPENDENCY_UNRESOLVED.value,
                        f"{dep} does not match exactly one release member",
                    )
                )
            else:
                lock.append({"module": n["module"]["id"], "requires": dep})

    # 3. Terms, predicates and change records.
    terms: dict[str, dict[str, Any]] = {}
    term_file: dict[str, str] = {}
    for file, n in normalized:
        for term in n["terms"]:
            terms[term["id"]] = term
            term_file[term["id"]] = file
    keys: dict[str, str] = {}
    for tid, term in sorted(terms.items()):
        key = term.get("predicate_key")
        if key is None:
            continue
        if key in keys:
            issues.append(
                Issue(
                    term_file[tid],
                    f"$.terms[{tid}]",
                    Code.PREDICATE_KEY_DUPLICATE.value,
                    f"{key} is declared by {keys[key]} and {tid}",
                )
            )
        keys[key] = tid
    records: list[dict[str, Any]] = []
    for entry in request.get("changes", []) or []:
        path = base / entry
        out = _Collector(_rel(path, root))
        data = load_yaml(path, out)
        issues.extend(out.issues)
        for record in (data or {}).get("change_records", []) if isinstance(data, Mapping) else []:
            records.append(
                {
                    "class": record.get("class"),
                    "source_iris": sorted(record.get("source_iris") or []),
                    "replacement_iris": sorted(record.get("replacement_iris") or []),
                    "rationale": record.get("rationale", ""),
                }
            )
    records.sort(key=lambda r: (str(r["class"]), r["source_iris"], r["replacement_iris"]))

    output_dir = base
    history = identity_history(root, exclude=output_dir)
    predecessor_terms: dict[str, LockedTerm] = {}
    if request.get("predecessor"):
        predecessor_terms = read_lock((base / request["predecessor"]).resolve())
    candidate_digests = {t["iri"]: definition_digest(t) for t in terms.values()}
    issues += check_change_records(
        records,
        candidate=set(candidate_digests),
        known=set(history) | set(predecessor_terms),
        file=request_file,
    )
    issues += check_identity(
        {t["iri"]: t for t in terms.values()},
        history=history,
        predecessor=predecessor_terms,
        change_records=records,
        file=request_file,
    )

    # 4. Authoring constraints and projection coverage (S0004 AC5).
    constraints = [(file, c) for file, n in normalized for c in n["constraints"]]
    issues += run_authoring_constraints(terms, constraints)
    projection, uncovered = build_projection(normalized, terms)
    issues += uncovered
    if issues:
        raise CompileFailed(issues)

    # 5. Manifest (S0004 AC3) and outputs.
    term_rows = [
        {
            "iri": t["iri"],
            "module": term_file[tid]
            and next(n["module"]["id"] for f, n in normalized if f == term_file[tid]),
            "kind": t["kind"],
            "definition_digest": candidate_digests[t["iri"]],
            "term": t,
        }
        for tid, t in sorted(terms.items(), key=lambda kv: kv[1]["iri"])
    ]
    module_rows = sorted(
        (
            {"id": n["module"]["id"], "version": n["module"]["version"], "digest": digests[f]}
            for f, n in normalized
        ),
        key=lambda m: m["id"],
    )
    manifest: dict[str, Any] = {
        "contract": MANIFEST_CONTRACT,
        "name": request["name"],
        "sequence": request["sequence"],
        "authoring_schema": AUTHORING_SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "semantics": {
            "inference": ["subClassOf", "subPropertyOf", "inverseOf"],
            "validation": [
                "domain",
                "range",
                "disjoint",
                "minCardinality",
                "maxCardinality",
                "custom",
            ],
            "ruleset": RULESET,
        },
        "modules": module_rows,
        "dependency_lock": sorted(lock, key=lambda d: (d["module"], d["requires"])),
        "terms_digest": sha256_jcs([[r["iri"], r["definition_digest"]] for r in term_rows]),
        "predicates": [
            predicate_entry(t)
            for t in sorted(terms.values(), key=lambda t: t["iri"])
            if "predicate_key" in t
        ],
        "change_records": records,
        "projection_mapping": {
            "version": MAPPING_VERSION,
            "digest": sha256_jcs(projection),
            "required_context": list(REQUIRED_CONTEXT),
        },
        "artifact_slots": {"profiles": [], "templates": [], "compiler": [], "validation": []},
    }
    digest = manifest_digest(manifest)
    manifest["manifest_digest"] = digest
    manifest["release_ref"] = release_ref_for(digest)
    try:
        validate_contract(MANIFEST_REF, manifest, profile="portable-json/v1")
    except ContractError as exc:  # pragma: no cover - compiler output guard
        raise CompileFailed(
            [
                Issue(
                    request_file,
                    "$",
                    Code.SCHEMA_INVALID.value,
                    f"manifest output guard: {exc.issue.schema_pointer}",
                )
            ]
        ) from exc
    normalized_release = {
        "contract": NORMALIZED_CONTRACT,
        "name": request["name"],
        "sequence": request["sequence"],
        "modules": [
            {
                "id": n["module"]["id"],
                "version": n["module"]["version"],
                "digest": digests[f],
                "normalized": n,
            }
            for f, n in sorted(normalized, key=lambda x: x[1]["module"]["id"])
        ],
        "terms": term_rows,
        "change_records": records,
    }
    rows = triples(
        manifest["release_ref"],
        f"{request['name']}@{request['sequence']}",
        [r["term"] for r in term_rows],
    )
    return CompiledRelease(
        name=request["name"],
        sequence=request["sequence"],
        manifest=manifest,
        normalized=normalized_release,
        projection=projection,
        turtle=to_turtle(rows),
        jsonld=to_jsonld(rows),
    )


def write_release(compiled: CompiledRelease, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in compiled.files().items():
        (directory / name).write_bytes(data)


def check_release(compiled: CompiledRelease, directory: Path, *, file: str) -> list[Issue]:
    """`compile --check`: committed outputs must equal a fresh compile byte for byte."""
    issues = []
    for name, data in compiled.files().items():
        target = directory / name
        if not target.is_file() or target.read_bytes() != data:
            issues.append(
                Issue(
                    file,
                    f"$.outputs[{name}]",
                    Code.OUTPUT_STALE.value,
                    f"{name} differs from a fresh compile",
                )
            )
    return issues
