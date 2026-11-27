"""F0012 ontology release identity (ADR-0081). Pure domain: no I/O.

Shared by the offline toolchain (`brain_ontology`) and the release store
(`brain_persistence.ontology_releases`) so both compute the same digests.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from brain_domain.fact_values import jcs

AUTHORING_SCHEMA = "ontology-module-authoring/v1"
MANIFEST_CONTRACT = "ontology-release-manifest/v1"
IMPACT_CONTRACT = "ontology-impact-report/v1"
RULESET = "nebula-tbox-subset/v1"
IRI_PREFIX = "urn:nebula:ont:"
TENANT_PREFIX = "urn:nebula:tenant:"
RELEASE_PREFIX = "ontrel:sha256-"

TERM_ID = re.compile(r"^[a-z][a-z0-9-]{0,47}(\.[a-z][a-z0-9-]{0,47}){1,7}$")
RELEASE_REF = re.compile(r"^ontrel:sha256-[0-9a-f]{64}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")

# Predicate namespaces owned by the static registry (ADR-0077 D2): `sys` in production,
# `test` in test composition. No ontology release may declare them.
RESERVED_PREDICATE_NAMESPACES = frozenset({"sys", "test"})

# Fields that never change a term's meaning (ADR-0081 D1): a rename is never a
# semantic change.
LABEL_FIELDS = frozenset({"labels", "aliases"})
# Manifest fields excluded from its own digest: they are derived from it.
DERIVED_MANIFEST_FIELDS = frozenset({"release_ref", "manifest_digest"})


class OntologyReason(StrEnum):
    """Typed runtime refusals of install, report, review and activation."""

    MANIFEST_INVALID = "MANIFEST_INVALID"
    MANIFEST_DIGEST_MISMATCH = "MANIFEST_DIGEST_MISMATCH"
    MODULE_VERSION_IMMUTABLE = "MODULE_VERSION_IMMUTABLE"
    IDENTITY_REUSE_REJECTED = "IDENTITY_REUSE_REJECTED"
    TERM_REMOVED_WITHOUT_RETIREMENT = "TERM_REMOVED_WITHOUT_RETIREMENT"
    TENANT_EXTENSION_UNSUPPORTED = "TENANT_EXTENSION_UNSUPPORTED"
    RELEASE_NOT_INSTALLED = "RELEASE_NOT_INSTALLED"
    REPORT_NOT_FOUND = "REPORT_NOT_FOUND"
    ACTIVATION_REPORT_REQUIRED = "ACTIVATION_REPORT_REQUIRED"
    REPORT_DIGEST_MISMATCH = "REPORT_DIGEST_MISMATCH"
    REPORT_INCOMPLETE = "REPORT_INCOMPLETE"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    PREDECESSOR_MISMATCH = "PREDECESSOR_MISMATCH"
    ROLLBACK_TARGET_NEVER_ACTIVE = "ROLLBACK_TARGET_NEVER_ACTIVE"
    SELECTION_CONFLICT = "SELECTION_CONFLICT"


class OntologyRefused(Exception):
    def __init__(self, reason: OntologyReason, detail: str = "") -> None:
        super().__init__(reason.value if not detail else f"{reason.value}: {detail}")
        self.reason = reason
        self.detail = detail


def sha256_jcs(value: Any) -> str:
    """SHA-256 (lowercase hex) of the RFC 8785 serialization."""
    return hashlib.sha256(jcs(value)).hexdigest()


def term_iri(term_id: str) -> str:
    """ADR-0081 D1: the IRI is the fixed prefix plus the validated ID."""
    if not TERM_ID.match(term_id):
        raise ValueError(f"invalid term id: {term_id!r}")
    return IRI_PREFIX + term_id


def definition_digest(term: Mapping[str, Any]) -> str:
    """Digest of a normalized term without its labels and aliases."""
    return sha256_jcs({k: v for k, v in term.items() if k not in LABEL_FIELDS})


ADDITIVE_AXIOMS = ("parents", "sub_property_of")


def only_added_axioms(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    """True when `after` equals `before` plus extra `parents`/`sub_property_of`
    entries: a monotonic additive edit that keeps the IRI (EX-ONT-003). Labels and
    aliases are ignored; keys starting with `_` are storage annotations."""

    def core(term: Mapping[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in term.items() if k not in LABEL_FIELDS and not k.startswith("_")}

    a, b = core(before), core(after)
    grew = False
    for name in ADDITIVE_AXIOMS:
        old, new = set(a.pop(name, [])), set(b.pop(name, []))
        if not old <= new:
            return False
        grew = grew or new != old
    return grew and a == b


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    return sha256_jcs({k: v for k, v in manifest.items() if k not in DERIVED_MANIFEST_FIELDS})


def release_ref_for(digest: str) -> str:
    if not DIGEST.match(digest):
        raise ValueError("a manifest digest is 64 lowercase hex characters")
    return RELEASE_PREFIX + digest


def report_digest(report: Mapping[str, Any]) -> str:
    return sha256_jcs({k: v for k, v in report.items() if k != "report_digest"})
