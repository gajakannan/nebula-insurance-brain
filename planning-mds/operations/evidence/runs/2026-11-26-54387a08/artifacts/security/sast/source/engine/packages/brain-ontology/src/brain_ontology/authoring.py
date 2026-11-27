"""Offline module authoring validation (F0012-S0001, S0002 AC1/AC3/AC6; ADR-0081 D1/D2).

`validate_module` reads one file, never the network or a database, and collects
every error in a deterministic (file, JSON path, code) order:

1. YAML load (one `YAML_INVALID` error with its position) and duplicate keys.
2. Pre-checks: singular `parent` -> `AUTHORING_FIELD_RETIRED`; any other term key
   the authoring schema does not define -> `UNSUPPORTED_CONSTRUCT` naming it.
3. JSON Schema `ontology-module-authoring/v1` from the installed F0011 bundle,
   with schema failures mapped to the story's stable codes.
4. Semantic checks the schema cannot express: references, identity grammar,
   tenant namespace, predicates, constraint execution context.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from brain_contracts.schema_runtime import ContractBundle, ContractRef
from brain_domain.ontology import AUTHORING_SCHEMA, TENANT_PREFIX, TERM_ID
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from brain_ontology.errors import Code, Issue, json_path

AUTHORING_REF = ContractRef("ontology-module-authoring-v1", "1")
BCP47 = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
PREDICATE_KEY = re.compile(r"^[a-z][a-z0-9-]{0,31}:[A-Za-z][A-Za-z0-9]{0,63}@v[1-9][0-9]{0,3}$")
TERM_FIELDS = frozenset(
    {
        "id",
        "kind",
        "labels",
        "aliases",
        "definition",
        "examples",
        "regression_cases",
        "parents",
        "domain",
        "range",
        "inverse_of",
        "sub_property_of",
        "temporal_kind",
        "value_type",
        "cardinality",
        "predicate",
        "code_of",
        "external_codes",
    }
)
PROPERTY_KINDS = frozenset({"object_property", "datatype_property"})
CONSTRAINT_CONTEXT = (
    "stage",
    "consumer",
    "applicability",
    "severity",
    "on_nonconformance",
    "data_basis",
)
_REQUIRED_CODES = {
    "definition": Code.DEFINITION_REQUIRED,
    "examples": Code.EXAMPLE_REQUIRED,
    "regression_cases": Code.REGRESSION_CASE_REQUIRED,
    "temporal_kind": Code.TEMPORAL_KIND_INVALID,
    "labels": Code.LABEL_EN_US_REQUIRED,
    "id": Code.TERM_ID_INVALID,
}
_FIELD_CODES = {
    "definition": Code.DEFINITION_REQUIRED,
    "examples": Code.EXAMPLE_REQUIRED,
    "regression_cases": Code.REGRESSION_CASE_REQUIRED,
    "temporal_kind": Code.TEMPORAL_KIND_INVALID,
    "id": Code.TERM_ID_INVALID,
    "parents": Code.TERM_ID_INVALID,
    "domain": Code.TERM_ID_INVALID,
    "inverse_of": Code.TERM_ID_INVALID,
    "sub_property_of": Code.TERM_ID_INVALID,
    "code_of": Code.TERM_ID_INVALID,
    "predicate": Code.PREDICATE_KEY_INVALID,
}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    file: str
    issues: tuple[Issue, ...]
    module: Mapping[str, Any] | None = None
    authoring_schema: str = AUTHORING_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.issues

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "file": self.file,
            "authoring_schema": self.authoring_schema,
            "valid": self.ok,
            "errors": [i.to_json() for i in self.issues],
        }
        if self.ok and self.module is not None:
            terms = self.module.get("terms", [])
            result["module"] = f"{self.module['module']['id']}@{self.module['module']['version']}"
            result["terms"] = len(terms)
            result["predicates"] = sum(1 for t in terms if "predicate" in t)
        return result


@dataclass(slots=True)
class _Collector:
    file: str
    issues: list[Issue] = field(default_factory=list)

    def add(self, path: Iterable[object], code: Code, message: str) -> None:
        self.issues.append(Issue(self.file, json_path(list(path)), code.value, message))


# --- YAML -------------------------------------------------------------------


def _duplicate_keys(node: yaml.Node, path: list[object], out: _Collector) -> None:
    if isinstance(node, yaml.MappingNode):
        seen: set[object] = set()
        for key_node, value_node in node.value:
            key = key_node.value
            if key in seen:
                parent = path[-1] if path else None
                code = Code.LABEL_PREFERRED_DUPLICATE if parent == "labels" else Code.DUPLICATE_KEY
                out.add(
                    [*path, key],
                    code,
                    f"key {key!r} appears more than once"
                    + (" (one preferred label per language tag)" if parent == "labels" else ""),
                )
            seen.add(key)
            _duplicate_keys(value_node, [*path, key], out)
    elif isinstance(node, yaml.SequenceNode):
        for index, item in enumerate(node.value):
            _duplicate_keys(item, [*path, index], out)


def load_yaml(path: Path, out: _Collector) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        node = yaml.compose(text, Loader=yaml.SafeLoader)
        if node is not None:
            _duplicate_keys(node, [], out)
        return yaml.safe_load(text)
    except (OSError, UnicodeError) as exc:
        out.add([], Code.YAML_INVALID, f"cannot read file: {exc.__class__.__name__}")
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"line {mark.line + 1}, column {mark.column + 1}" if mark else "unknown position"
        out.add([], Code.YAML_INVALID, f"YAML parse error at {where}")
    return None


# --- schema -------------------------------------------------------------------


_VALIDATOR: Draft202012Validator | None = None


def authoring_validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is None:
        schema = ContractBundle.installed().schema(AUTHORING_REF)
        _VALIDATOR = Draft202012Validator(dict(schema))
    return _VALIDATOR


def _schema_issue(error: ValidationError, out: _Collector) -> None:
    path = list(error.absolute_path)
    names = [p for p in path if isinstance(p, str)]
    last = names[-1] if names else None
    in_term = len(path) >= 2 and path[0] == "terms"
    in_constraint = len(path) >= 2 and path[0] == "constraints"
    if error.validator == "required":
        instance = error.instance if isinstance(error.instance, Mapping) else {}
        for missing in sorted(set(error.validator_value) - set(instance)):
            if in_constraint and len(path) == 2:
                code = Code.CONSTRAINT_CONTEXT_INCOMPLETE
            elif last == "labels":
                code = Code.LABEL_EN_US_REQUIRED
            elif in_term and len(path) == 2:
                code = _REQUIRED_CODES.get(missing, Code.SCHEMA_INVALID)
            else:
                code = Code.SCHEMA_INVALID
            out.add([*path, missing], code, f"required field {missing!r} is missing")
        return
    if in_term and "labels" in names and error.validator == "propertyNames":
        out.add(path, Code.LABEL_TAG_INVALID, f"invalid BCP 47 language tag {error.instance!r}")
        return
    if in_constraint and last == "construct":
        out.add(
            path, Code.UNSUPPORTED_CONSTRUCT, f"unsupported constraint construct {error.instance!r}"
        )
        return
    if in_constraint and "data_basis" in names:
        out.add(
            path,
            Code.CONSTRAINT_CONTEXT_INCOMPLETE,
            "data_basis is 'asserted' or {inferred: nebula-tbox-subset/v1}",
        )
        return
    if path[:2] == ["module", "dependencies"]:
        out.add(
            path,
            Code.DEPENDENCY_UNRESOLVED,
            f"dependency {error.instance!r} is not an exact module@version#sha256:<digest>",
        )
        return
    if in_term and len(path) >= 3:
        field_code = _FIELD_CODES.get(str(path[2]))
        if field_code is not None:
            out.add(path, field_code, f"{path[2]}: {error.validator} check failed")
            return
    out.add(path, Code.SCHEMA_INVALID, f"{error.validator} check failed")


# --- references ---------------------------------------------------------------


def resolve_reference(reference: str, repo_root: Path) -> bool:
    """A reference is a repository-relative file, optionally `file#ID`, where the
    ID must occur in that file as a whole token."""
    target, _, anchor = reference.partition("#")
    if not target or target.startswith("/") or ".." in Path(target).parts:
        return False
    file = repo_root / target
    if not file.is_file():
        return False
    if not anchor:
        return True
    text = file.read_text(encoding="utf-8", errors="replace")
    return re.search(rf"(?<![\w-]){re.escape(anchor)}(?![\w-])", text) is not None


# --- semantic checks ------------------------------------------------------------


def _terms(module: Mapping[str, Any]) -> Iterator[tuple[int, Mapping[str, Any]]]:
    terms = module.get("terms")
    if isinstance(terms, list):
        for index, term in enumerate(terms):
            if isinstance(term, Mapping):
                yield index, term


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def _tenant_values(value: object, path: list[object], out: _Collector) -> None:
    if isinstance(value, str) and value.startswith(TENANT_PREFIX):
        out.add(path, Code.TENANT_NAMESPACE_RESERVED, f"{TENANT_PREFIX} is reserved for tenants")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _tenant_values(item, [*path, key], out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _tenant_values(item, [*path, index], out)


def _semantic(
    module: Mapping[str, Any],
    out: _Collector,
    *,
    repo_root: Path,
    external: Mapping[str, Mapping[str, Any]],
) -> None:
    _tenant_values(module, [], out)
    local: dict[str, Mapping[str, Any]] = {}
    for index, term in _terms(module):
        term_id = term.get("id")
        if not isinstance(term_id, str):
            continue
        if not TERM_ID.match(term_id):
            continue  # reported by the schema pattern
        if term_id.split(".")[0] == "tenant":
            out.add(
                ["terms", index, "id"],
                Code.TENANT_NAMESPACE_RESERVED,
                f"term {term_id} uses the reserved tenant namespace",
            )
        if term_id in local or term_id in external:
            out.add(
                ["terms", index, "id"],
                Code.IRI_COLLISION,
                f"term {term_id} is declared more than once",
            )
            continue
        local[term_id] = term
    known = {**external, **local}

    def need(path: list[object], ref: str, *, kinds: frozenset[str] | None = None) -> None:
        target = known.get(ref)
        if target is None:
            out.add(path, Code.REFERENCE_UNRESOLVED, f"{ref} does not resolve to a term")
        elif kinds is not None and target.get("kind") not in kinds:
            out.add(path, Code.REFERENCE_UNRESOLVED, f"{ref} is not a {'/'.join(sorted(kinds))}")

    classes = frozenset({"class"})
    keys: dict[str, str] = {}
    namespace = (
        module.get("module", {}).get("predicate_namespace")
        if isinstance(module.get("module"), Mapping)
        else None
    )
    for index, term in _terms(module):
        tid = term.get("id")
        kind = term.get("kind")
        base: list[object] = ["terms", index]
        for name in ("examples", "regression_cases"):
            for j, ref in enumerate(_strings(term.get(name))):
                if not resolve_reference(ref, repo_root):
                    out.add(
                        [*base, name, j],
                        Code.REFERENCE_UNRESOLVED,
                        f"term {tid}: {name} reference {ref!r} does not resolve",
                    )
        for j, tag in enumerate(
            a.get("tag") for a in term.get("aliases", []) if isinstance(a, Mapping)
        ):
            if not isinstance(tag, str) or not BCP47.match(tag):
                out.add(
                    [*base, "aliases", j, "tag"], Code.LABEL_TAG_INVALID, f"invalid tag {tag!r}"
                )
        for j, parent in enumerate(_strings(term.get("parents"))):
            need([*base, "parents", j], parent, kinds=classes)
        if kind in PROPERTY_KINDS:
            if isinstance(term.get("domain"), str):
                need([*base, "domain"], term["domain"], kinds=classes)
            rng = term.get("range")
            if isinstance(rng, str) and not rng.startswith(TENANT_PREFIX):
                if kind == "datatype_property":
                    if not rng.startswith("xsd:"):
                        out.add(
                            [*base, "range"], Code.REFERENCE_UNRESOLVED, "a datatype range is xsd:*"
                        )
                elif not rng.startswith("xsd:"):
                    need([*base, "range"], rng, kinds=classes)
                else:
                    out.add(
                        [*base, "range"], Code.REFERENCE_UNRESOLVED, "an object range is a class"
                    )
            if isinstance(term.get("inverse_of"), str):
                need([*base, "inverse_of"], term["inverse_of"], kinds=PROPERTY_KINDS)
            for j, sup in enumerate(_strings(term.get("sub_property_of"))):
                need([*base, "sub_property_of", j], sup, kinds=PROPERTY_KINDS)
        else:
            for name in ("domain", "range", "inverse_of", "sub_property_of", "temporal_kind"):
                if name in term:
                    out.add(
                        [*base, name],
                        Code.UNSUPPORTED_CONSTRUCT,
                        f"{name} applies to properties only",
                    )
        if kind == "code_value":
            if isinstance(term.get("code_of"), str):
                need([*base, "code_of"], term["code_of"], kinds=classes)
            else:
                out.add(
                    [*base, "code_of"], Code.SCHEMA_INVALID, "a code value names its code_of class"
                )
        predicate = term.get("predicate")
        if isinstance(predicate, Mapping):
            key = f"{namespace}:{predicate.get('local_name')}@v{predicate.get('major')}"
            if kind not in PROPERTY_KINDS or "inverse_of" in term:
                out.add(
                    [*base, "predicate"],
                    Code.PREDICATE_KEY_INVALID,
                    "only a stored (non-inverse) property declares a predicate",
                )
            elif not PREDICATE_KEY.match(key):
                out.add([*base, "predicate"], Code.PREDICATE_KEY_INVALID, f"invalid key {key}")
            elif key in keys:
                out.add(
                    [*base, "predicate"],
                    Code.PREDICATE_KEY_DUPLICATE,
                    f"{key} is declared by {keys[key]} and {tid}",
                )
            else:
                keys[key] = str(tid)
            value_type = term.get("value_type")
            if term.get("cardinality") == "RELATIONSHIP" and value_type != "entity_ref":
                out.add(
                    [*base, "value_type"], Code.SCHEMA_INVALID, "a RELATIONSHIP slot is entity_ref"
                )
            if (value_type == "entity_ref") != (kind == "object_property") and value_type != "code":
                out.add(
                    [*base, "value_type"],
                    Code.SCHEMA_INVALID,
                    "entity_ref values belong to object properties only",
                )

    constraints = module.get("constraints")
    for index, constraint in enumerate(constraints if isinstance(constraints, list) else []):
        if not isinstance(constraint, Mapping):
            continue
        base = ["constraints", index]
        construct = constraint.get("construct")
        if isinstance(constraint.get("subject"), str):
            need([*base, "subject"], constraint["subject"])
        if isinstance(constraint.get("property"), str):
            need([*base, "property"], constraint["property"], kinds=PROPERTY_KINDS)
        for j, other in enumerate(_strings(constraint.get("with"))):
            need([*base, "with", j], other)
        if (
            construct in {"domain", "range", "minCardinality", "maxCardinality"}
            and "property" not in constraint
        ):
            out.add(
                [*base, "property"],
                Code.CONSTRAINT_CONTEXT_INCOMPLETE,
                f"{construct} names a property",
            )
        if construct in {"minCardinality", "maxCardinality"} and "value" not in constraint:
            out.add(
                [*base, "value"], Code.CONSTRAINT_CONTEXT_INCOMPLETE, f"{construct} names a value"
            )
        if construct == "disjoint" and not constraint.get("with"):
            out.add(
                [*base, "with"],
                Code.CONSTRAINT_CONTEXT_INCOMPLETE,
                "disjoint names the other class",
            )
        if construct == "custom":
            if constraint.get("stage") == "authoring":
                out.add(
                    [*base, "construct"],
                    Code.UNSUPPORTED_CONSTRUCT,
                    "a custom constraint cannot execute at the authoring stage",
                )
            if not constraint.get("expression"):
                out.add(
                    [*base, "expression"],
                    Code.CONSTRAINT_CONTEXT_INCOMPLETE,
                    "custom needs an expression",
                )

    projection = module.get("projection")
    for index, rule in enumerate(projection if isinstance(projection, list) else []):
        if isinstance(rule, Mapping) and isinstance(rule.get("property"), str):
            need(["projection", index, "property"], rule["property"], kinds=PROPERTY_KINDS)


def _strip_prechecked(module: Any, out: _Collector) -> Any:
    """Report retired and unsupported term fields and remove them, so the schema
    reports each problem once."""
    if not isinstance(module, Mapping):
        return module
    clean = copy.deepcopy(dict(module))
    for index, term in _terms(clean):
        assert isinstance(term, dict)
        tid = term.get("id", f"#{index}")
        for key in sorted(set(term) - TERM_FIELDS, key=str):
            if key == "parent":
                out.add(
                    ["terms", index, "parent"],
                    Code.AUTHORING_FIELD_RETIRED,
                    f"term {tid}: 'parent' is retired; use 'parents'",
                )
            else:
                out.add(
                    ["terms", index, str(key)],
                    Code.UNSUPPORTED_CONSTRUCT,
                    f"term {tid}: construct {key!r} is not supported (ADR-0081 D2)",
                )
            del term[key]
    return clean


def validate_document(
    module: Any,
    *,
    file: str,
    repo_root: Path,
    external: Mapping[str, Mapping[str, Any]] | None = None,
    collector: _Collector | None = None,
) -> ValidationResult:
    out = collector or _Collector(file)
    clean = _strip_prechecked(module, out)
    for error in authoring_validator().iter_errors(clean):
        _schema_issue(error, out)
    if isinstance(clean, Mapping):
        _semantic(clean, out, repo_root=repo_root, external=external or {})
    issues = tuple(sorted(set(out.issues)))
    return ValidationResult(file, issues, module if not issues else None)


def validate_module(
    path: Path,
    *,
    repo_root: Path,
    external: Mapping[str, Mapping[str, Any]] | None = None,
) -> ValidationResult:
    file = _display(path, repo_root)
    out = _Collector(file)
    module = load_yaml(path, out)
    if out.issues and any(i.code == Code.YAML_INVALID for i in out.issues):
        return ValidationResult(file, tuple(sorted(set(out.issues))))
    return validate_document(
        module, file=file, repo_root=repo_root, external=external, collector=out
    )


def _display(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
