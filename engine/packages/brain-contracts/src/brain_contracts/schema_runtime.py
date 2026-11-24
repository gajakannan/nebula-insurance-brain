"""Closed, immutable, installed structural contracts (ADR-0013 / ADR-0079).

Structural acceptance grants no authority and performs no domain normalization.
Existing readers explicitly choose the native profile before inspecting input.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, NoReturn
from urllib.parse import urldefrag, urljoin

import rfc8785
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource
from rfc3986_validator import validate_rfc3986  # type: ignore[import-untyped]

WireProfile = Literal["portable-json/v1", "native-compat/v1"]
DIALECT = "https://json-schema.org/draft/2020-12/schema"
PROFILES = frozenset(("portable-json/v1", "native-compat/v1"))
MAX_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 128
MAX_NODES = 1_000_000
SAFE_INTEGER = 2**53 - 1
VALIDATION_KEYWORDS = frozenset(
    [
        "type",
        "const",
        "enum",
        "properties",
        "required",
        "additionalProperties",
        "propertyNames",
        "maxProperties",
        "items",
        "minItems",
        "maxItems",
        "uniqueItems",
        "contains",
        "minContains",
        "maxContains",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "allOf",
        "anyOf",
        "oneOf",
        "if",
        "then",
        "else",
        "not",
    ]
)
ANNOTATIONS = {
    "title": str,
    "description": str,
    "default": object,
    "examples": list,
    "x-nebula-concept": str,
    "x-nebula-display-name": str,
    "x-nebula-evidence-required": bool,
    "x-nebula-relationship": str,
    "x-nebula-security-scope": str,
    "x-nebula-extraction-hint": str,
    "x-nebula-line-of-business": str,
    "x-nebula-document-profile": str,
}
CORE_KEYWORDS = frozenset(("$schema", "$id", "$ref", "$defs"))
FORMATS = frozenset(("uuid", "date", "date-time", "uri-reference"))
MAP_SCHEMAS = frozenset(("properties", "$defs"))
SINGLE_SCHEMAS = frozenset(
    ("items", "contains", "propertyNames", "additionalProperties", "if", "then", "else", "not")
)
ARRAY_SCHEMAS = frozenset(("allOf", "anyOf", "oneOf"))
LEGACY_NATIVE_RESOURCES = frozenset(
    (
        "content-artifact-manifest.schema.json",
        "content-artifact-manifest-v2.schema.json",
        "content-records-v2.schema.json",
        "document-date-record.schema.json",
        "interpretation-output-manifest.schema.json",
        "assertion-record-v2.schema.json",
        "interpretation-result.schema.json",
        "interpretation-result-v2.schema.json",
        "assertion-admission-result-v1.schema.json",
    )
)


@dataclass(frozen=True, slots=True)
class ContractRef:
    name: str
    version: str
    pointer: str = ""


@dataclass(frozen=True, slots=True)
class ContractIssue:
    code: str
    contract_id: str
    schema_pointer: str


class ContractError(ValueError):
    """Only fixed codes and trusted schema coordinates can escape validation."""

    def __init__(self, code: str, contract_id: str = "", schema_pointer: str = "") -> None:
        self.code = code
        self.issue = ContractIssue(code, contract_id, schema_pointer)
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise ContractError(code)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("CONTRACT_JSON_INVALID")
        result[key] = value
    return result


def _number(token: str) -> float:
    number = float(token)
    if not math.isfinite(number):
        _fail("CONTRACT_JSON_UNSUPPORTED")
    # WHY: check the original token, before binary64 rounding can hide a large
    # integral number such as 9007199254740991.1 or 9007199254740993e0.
    decimal = Decimal(token)
    if decimal == decimal.to_integral_value() and abs(decimal) > SAFE_INTEGER:
        _fail("CONTRACT_JSON_UNSUPPORTED")
    return number


def _admit(value: Any, *, portable: bool) -> None:
    stack = [(value, 1, False)]
    count = 0
    ancestors: set[int] = set()
    while stack:
        item, depth, leaving = stack.pop()
        if leaving:
            ancestors.remove(id(item))
            continue
        count += 1
        if portable and (count > MAX_NODES or depth > MAX_DEPTH):
            _fail("CONTRACT_JSON_UNSUPPORTED")
        if item is None or type(item) is bool:
            continue
        if isinstance(item, str):
            item.encode("utf-8", errors="strict")
        elif type(item) in (int, float):
            if (type(item) is float and not math.isfinite(item)) or (
                portable and item == math.trunc(item) and abs(item) > SAFE_INTEGER
            ):
                _fail("CONTRACT_JSON_UNSUPPORTED")
        elif type(item) in (dict, list):
            if id(item) in ancestors:
                _fail("CONTRACT_JSON_UNSUPPORTED")
            ancestors.add(id(item))
            stack.append((item, depth, True))
            if type(item) is dict:
                for key in item:
                    if not isinstance(key, str):
                        _fail("CONTRACT_JSON_UNSUPPORTED")
                    key.encode("utf-8", errors="strict")
                children = item.values()
            else:
                children = item
            stack.extend((child, depth + 1, False) for child in children)
        else:
            _fail("CONTRACT_JSON_UNSUPPORTED")


def _profile(profile: str) -> bool:
    if profile not in PROFILES:
        _fail("CONTRACT_VERSION_UNSUPPORTED")
    return profile == "portable-json/v1"


def decode_json(raw: bytes | str, *, profile: WireProfile) -> Any:
    portable = _profile(profile)
    try:
        if not isinstance(raw, (bytes, str)):
            _fail("CONTRACT_JSON_INVALID")
        size = len(raw) if isinstance(raw, bytes) else len(raw.encode("utf-8", errors="strict"))
        if portable and size > MAX_BYTES:
            _fail("CONTRACT_JSON_UNSUPPORTED")
        text = raw.decode("utf-8", errors="strict") if isinstance(raw, bytes) else raw
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=_number if portable else float,
            parse_constant=lambda _: _fail("CONTRACT_JSON_INVALID"),
        )
        _admit(value, portable=portable)
        return value
    except ContractError:
        raise
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        raise ContractError("CONTRACT_JSON_INVALID") from None


def portable_json_bytes(value: Any) -> bytes:
    """Encode admitted JSON with ECMAScript binary64 spelling, without mutation.

    The caller owns admission and size limits. This also lets build/test callers
    send the same compact bytes through the actual raw model boundary.
    """
    try:
        return rfc8785.dumps(value)
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        raise ContractError("CONTRACT_JSON_UNSUPPORTED") from None


@lru_cache(maxsize=256)
def _portable_pattern_source(pattern: str) -> str:
    # The selected source patterns use one terminal anchor. Python '$' also
    # matches before a final newline; the ECMAScript portable policy does not.
    escaped = False
    character_class = False
    for index, character in enumerate(pattern):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "[":
            character_class = True
        elif character == "]":
            character_class = False
        elif character == "$" and not character_class:
            if index != len(pattern) - 1:
                _fail("CONTRACT_SCHEMA_UNSUPPORTED")
            return pattern[:-1] + r"\Z"
    return pattern


def _date(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _date_time(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    match = re.fullmatch(
        r"([0-9]{4}-[0-9]{2}-[0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]+)?(?:[Zz]|([+-])([0-9]{2}):([0-9]{2}))",
        value,
    )
    return bool(
        match
        and _date(match[1])
        and int(match[2]) < 24
        and int(match[3]) < 60
        and int(match[4]) < 60
        and (match[5] is None or (int(match[6]) < 24 and int(match[7]) < 60))
    )


def portable_formats() -> FormatChecker:
    checker = FormatChecker(formats=[])
    checker.checks("uuid")(
        lambda v: (
            not isinstance(v, str)
            or bool(
                re.fullmatch(
                    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                    v,
                )
            )
        )
    )
    checker.checks("date")(_date)
    checker.checks("date-time")(_date_time)
    checker.checks("uri-reference")(
        lambda v: not isinstance(v, str) or bool(validate_rfc3986(v, rule="URI_reference"))
    )
    return checker


def escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def resolve_pointer(value: Any, pointer: str) -> Any:
    if not pointer:
        return value
    if (
        not isinstance(pointer, str)
        or not pointer.startswith("/")
        or re.search(r"~(?:[^01]|$)", pointer)
    ):
        _fail("CONTRACT_REFERENCE_UNRESOLVED")
    try:
        for part in pointer[1:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    _fail("CONTRACT_REFERENCE_UNRESOLVED")
                value = value[int(key)]
            else:
                value = value[key]
        return value
    except (KeyError, IndexError, TypeError, ValueError):
        raise ContractError("CONTRACT_REFERENCE_UNRESOLVED") from None


def schema_nodes(schema: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
    """Traverse schema positions only; property names and annotations are data."""
    yield pointer, schema
    if not isinstance(schema, dict):
        return
    for keyword, value in schema.items():
        location = f"{pointer}/{escape_pointer(keyword)}"
        if keyword in MAP_SCHEMAS and isinstance(value, dict):
            for name, child in value.items():
                yield from schema_nodes(child, f"{location}/{escape_pointer(name)}")
        elif keyword in SINGLE_SCHEMAS and isinstance(value, (dict, bool)):
            yield from schema_nodes(value, location)
        elif keyword in ARRAY_SCHEMAS and isinstance(value, list):
            for index, child in enumerate(value):
                yield from schema_nodes(child, f"{location}/{index}")


def metadata_for(schemas: Mapping[str, Any]) -> dict[str, Any]:
    return {
        identity: {
            pointer: {
                key: value
                for key, value in node.items()
                if key in ANNOTATIONS and key not in ("default", "examples")
            }
            for pointer, node in schema_nodes(schema)
            if isinstance(node, dict)
            and any(k in node for k in ANNOTATIONS if k not in ("default", "examples"))
        }
        for identity, schema in sorted(schemas.items())
    }


def _no_retrieve(uri: str) -> Resource:
    raise NoSuchResource(uri)


class ContractBundle:
    """A bundle becomes usable only after every resource and dormant ref passes."""

    def __init__(self, manifest_raw: bytes, read: Callable[[str], bytes]) -> None:
        try:
            manifest = decode_json(manifest_raw, profile="portable-json/v1")
            if set(manifest) != {"bundle", "profile", "resources", "toolchain"}:
                _fail("CONTRACT_BUNDLE_INVALID")
            if (
                manifest["bundle"] != "brain-contracts/v1"
                or manifest["profile"] != "nebula-json-schema/1"
            ):
                _fail("CONTRACT_BUNDLE_INVALID")
            toolchain = manifest["toolchain"]
            expected_tools = {
                "builder",
                "python",
                "jsonschema",
                "referencing",
                "pydantic",
                "datamodel_code_generator",
                "ajv",
                "ajv_formats",
                "jsonc_parser",
            }
            if (
                not isinstance(toolchain, dict)
                or set(toolchain) != expected_tools
                or any(not isinstance(v, str) or not v for v in toolchain.values())
            ):
                _fail("CONTRACT_BUNDLE_INVALID")
            resources = manifest["resources"]
            if not isinstance(resources, list) or not 1 <= len(resources) <= 256:
                _fail("CONTRACT_BUNDLE_INVALID")
            names: dict[str, dict[str, Any]] = {}
            schemas: dict[str, dict[str, Any]] = {}
            graph: dict[tuple[str, str], list[tuple[str, str]]] = {}
            for resource in resources:
                if set(resource) != {"id", "version", "path", "sha256"}:
                    _fail("CONTRACT_BUNDLE_INVALID")
                name = resource["path"]
                if not isinstance(name, str) or not re.fullmatch(
                    r"[a-z][a-z0-9-]*\.schema\.json", name
                ):
                    _fail("CONTRACT_BUNDLE_INVALID")
                identity = resource["id"]
                if (
                    not isinstance(identity, str)
                    or not identity.startswith("https://")
                    or "#" in identity
                ):
                    _fail("CONTRACT_BUNDLE_INVALID")
                if (
                    name in names
                    or identity in schemas
                    or not re.fullmatch(r"[1-9][0-9]*", resource["version"])
                ):
                    _fail("CONTRACT_BUNDLE_INVALID")
                raw = read(name)
                if hashlib.sha256(raw).hexdigest() != resource["sha256"]:
                    _fail("CONTRACT_BUNDLE_INVALID")
                schema = decode_json(raw, profile="portable-json/v1")
                if (
                    not isinstance(schema, dict)
                    or schema.get("$id") != identity
                    or schema.get("$schema") != DIALECT
                ):
                    _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                Draft202012Validator.check_schema(schema)
                names[name] = dict(resource)
                schemas[identity] = schema
            for identity, schema in schemas.items():
                nodes = dict(schema_nodes(schema))
                for pointer, node in nodes.items():
                    key = identity, pointer
                    edges = graph.setdefault(key, [])
                    if isinstance(node, bool):
                        continue
                    if not isinstance(node, dict):
                        _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                    unknown = set(node) - VALIDATION_KEYWORDS - CORE_KEYWORDS - set(ANNOTATIONS)
                    if unknown or (pointer and ("$id" in node or "$schema" in node)):
                        _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                    for annotation, kind in ANNOTATIONS.items():
                        if (
                            annotation in node
                            and kind is not object
                            and type(node[annotation]) is not kind
                        ):
                            _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                    if "format" in node and node["format"] not in FORMATS:
                        _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                    if "pattern" in node:
                        _portable_pattern_source(node["pattern"])
                    # Structural child edges make cycles through fragments visible.
                    for child_pointer in nodes:
                        if child_pointer.startswith(pointer + "/"):
                            remainder = child_pointer[len(pointer) + 1 :]
                            if remainder.count("/") <= 1:
                                edges.append((identity, child_pointer))
                    if "$ref" in node:
                        target_id, target_pointer = urldefrag(urljoin(identity, node["$ref"]))
                        if target_id not in schemas:
                            _fail("CONTRACT_REFERENCE_UNRESOLVED")
                        target = resolve_pointer(schemas[target_id], target_pointer)
                        if target_pointer not in dict(
                            schema_nodes(schemas[target_id])
                        ) or not isinstance(target, (dict, bool)):
                            _fail("CONTRACT_REFERENCE_UNRESOLVED")
                        edges.append((target_id, target_pointer))
            visiting: set[tuple[str, str]] = set()
            visited: set[tuple[str, str]] = set()

            def acyclic(key: tuple[str, str]) -> None:
                if key in visiting:
                    _fail("CONTRACT_SCHEMA_UNSUPPORTED")
                if key in visited:
                    return
                visiting.add(key)
                for child in graph[key]:
                    acyclic(child)
                visiting.remove(key)
                visited.add(key)

            for key in graph:
                acyclic(key)
            # attrs exposes the public alias `retrieve` for `_retrieve`; mypy
            # does not infer that alias from referencing's generated initializer.
            registry = Registry(retrieve=_no_retrieve).with_resources(  # type: ignore[call-arg]
                (identity, Resource.from_contents(schema)) for identity, schema in schemas.items()
            )
            self._names = names
            self._schemas = schemas
            self._registry = registry
            # A profile-local engine projection preserves exact-end matching
            # through every $ref, including roots which declare their dialect.
            # The public source schemas and native registry remain unchanged.
            portable_schemas = copy.deepcopy(schemas)
            for schema in portable_schemas.values():
                for _, node in schema_nodes(schema):
                    if isinstance(node, dict) and "pattern" in node:
                        node["pattern"] = _portable_pattern_source(node["pattern"])
            self._portable_registry = Registry(retrieve=_no_retrieve).with_resources(  # type: ignore[call-arg]
                (identity, Resource.from_contents(schema))
                for identity, schema in portable_schemas.items()
            )
            self._read = read
            self._validators: dict[tuple[str, str, str], Draft202012Validator] = {}
            self.digest = hashlib.sha256(manifest_raw).hexdigest()
            self._manifest = manifest
        except ContractError:
            raise
        except Exception:
            raise ContractError("CONTRACT_BUNDLE_INVALID") from None

    @classmethod
    @lru_cache(maxsize=1)
    def installed(cls) -> ContractBundle:
        root = files("brain_contracts").joinpath("resources", "v1")
        try:
            return cls(
                root.joinpath("manifest.json").read_bytes(),
                lambda name: root.joinpath(name).read_bytes(),
            )
        except ContractError:
            raise
        except Exception:
            raise ContractError("CONTRACT_BUNDLE_INVALID") from None

    @classmethod
    def from_directory(cls, directory: str | Path) -> ContractBundle:
        root = Path(directory)
        try:
            return cls(
                (root / "manifest.json").read_bytes(), lambda name: (root / name).read_bytes()
            )
        except ContractError:
            raise
        except Exception:
            raise ContractError("CONTRACT_BUNDLE_INVALID") from None

    def _resolve(self, ref: ContractRef) -> tuple[str, str]:
        name = ref.name if ref.name.endswith(".schema.json") else ref.name + ".schema.json"
        resource = self._names.get(name)
        if resource is None or resource["version"] != ref.version:
            _fail("CONTRACT_VERSION_UNSUPPORTED")
        identity = resource["id"]
        if ref.pointer not in dict(schema_nodes(self._schemas[identity])):
            _fail("CONTRACT_REFERENCE_UNRESOLVED")
        return identity, ref.pointer

    def schema(self, ref: ContractRef) -> Mapping[str, Any]:
        identity, pointer = self._resolve(ref)
        return copy.deepcopy(resolve_pointer(self._schemas[identity], pointer))

    def metadata(self, ref: ContractRef) -> Mapping[str, Any]:
        identity, pointer = self._resolve(ref)
        return copy.deepcopy(
            metadata_for({identity: self._schemas[identity]})[identity].get(pointer, {})
        )

    def openapi(self) -> dict[str, Any]:
        try:
            return decode_json(self._read("brain-api.openapi.json"), profile="portable-json/v1")
        except Exception:
            raise ContractError("CONTRACT_BUNDLE_INVALID") from None

    def decode(self, raw: bytes | str, *, profile: WireProfile) -> Any:
        return decode_json(raw, profile=profile)

    def validate(self, ref: ContractRef, value: Any, *, profile: WireProfile) -> None:
        portable = _profile(profile)
        identity, pointer = self._resolve(ref)
        try:
            if portable:
                _admit(value, portable=True)
                raw = portable_json_bytes(value)
                if len(raw) > MAX_BYTES:
                    _fail("CONTRACT_JSON_UNSUPPORTED")
            key = identity, pointer, profile
            if key not in self._validators:
                name = ref.name if ref.name.endswith(".schema.json") else ref.name + ".schema.json"
                # WHY: the shipped delegates had UUID/date checks but no optional
                # date-time checker. Freeze that boundary so installing build
                # tools cannot silently tighten old readers. Newly adopted
                # canonical/response guards explicitly check all declared formats.
                checker = (
                    FormatChecker(formats=["uuid", "date"])
                    if not portable and name in LEGACY_NATIVE_RESOURCES
                    else portable_formats()
                )
                self._validators[key] = Draft202012Validator(
                    {"$ref": identity + "#" + pointer},
                    registry=self._portable_registry if portable else self._registry,
                    format_checker=checker,
                )
            error = next(self._validators[key].iter_errors(value), None)
            if error is not None:
                # The pointer is derived from a trusted schema path, never instance paths.
                location = "/" + "/".join(escape_pointer(str(p)) for p in error.schema_path)
                raise ContractError("CONTRACT_INSTANCE_INVALID", identity, location)
        except ContractError:
            raise
        except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
            raise ContractError("CONTRACT_JSON_UNSUPPORTED") from None


def validate_contract(ref: ContractRef, value: Any, *, profile: WireProfile) -> None:
    ContractBundle.installed().validate(ref, value, profile=profile)
