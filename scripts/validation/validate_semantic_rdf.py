#!/usr/bin/env python3
"""Execute the Cedar Bridge RDF, OWL-RL, SHACL and SPARQL expectations.

The checks need the optional `semantic-rdf` tools (`pip install -e '.[semantic-rdf]'`).
Without them the result is `skipped` and the exit code is 0, unless `--require`
is passed, which CI does. A pass covers only the selected expectations in
expected-results.yaml; it is not Nebula runtime, assessment or AGE behaviour.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from importlib import metadata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path("planning-mds/examples/commercial-pc-account")
TOOLS = ("rdflib", "pyshacl", "owlrl")


def check_bundle(folder: Path) -> list[str]:
    from owlrl import DeductiveClosure, OWLRL_Semantics
    from pyshacl import validate as shacl_validate
    from rdflib import Graph
    from rdflib.compare import isomorphic

    def parse(name: str, fmt: str = "turtle") -> Graph:
        return Graph().parse(folder / name, format=fmt)

    findings: list[str] = []
    manifest = yaml.safe_load((folder / "release.yaml").read_text(encoding="utf-8"))
    expected = yaml.safe_load((folder / "expected-results.yaml").read_text(encoding="utf-8"))
    asserted = parse("snapshot.ttl")
    if not isomorphic(asserted, parse("snapshot.jsonld", "json-ld")):
        findings.append("snapshot.ttl and snapshot.jsonld are not isomorphic")

    consequences = parse("expected-inferences.ttl")
    findings += [f"expected inference already asserted: {t}" for t in consequences if t in asserted]
    closure = Graph() + asserted
    for module in manifest["modules"]:
        closure.parse(folder / module["file"], format="turtle")
    DeductiveClosure(OWLRL_Semantics).expand(closure)
    findings += [f"expected inference missing after OWL-RL: {t}" for t in consequences if t not in closure]

    for case in expected["shacl"]:
        conforms, _, report = shacl_validate(
            parse(case["data"]), shacl_graph=parse(case["shape"]),
            inference="none", meta_shacl=True, do_owl_imports=False)
        if conforms != case["conforms"]:
            findings.append(f"SHACL {case['shape']} on {case['data']}: expected conforms={case['conforms']}, "
                            f"got {conforms}\n{report}")

    for query in expected["queries"]:
        rows = len(list(asserted.query((folder / query["file"]).read_text(encoding="utf-8"))))
        if rows != query["rows"]:
            findings.append(f"{query['file']}: expected {query['rows']} rows, got {rows}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=ROOT)
    parser.add_argument("--require", action="store_true", help="fail instead of skipping when the RDF tools are absent")
    args = parser.parse_args()
    try:
        versions = {tool: metadata.version(tool) for tool in TOOLS}
    except metadata.PackageNotFoundError as error:
        print(json.dumps({"check_id": "semantic-rdf", "status": "fail" if args.require else "skipped",
                          "reason": f"optional RDF tool not installed: {error.name}; "
                                    "pip install -e '.[semantic-rdf]'"}, indent=2))
        return 1 if args.require else 0
    findings = check_bundle(args.product_root.resolve() / FOLDER)
    print(json.dumps({
        "check_id": "semantic-rdf",
        "status": "fail" if findings else "pass",
        "scope": "selected Cedar Bridge RDF equivalence, OWL-RL, SHACL and query expectations only",
        "python": platform.python_version(),
        "tools": versions,
        "findings": findings,
    }, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
