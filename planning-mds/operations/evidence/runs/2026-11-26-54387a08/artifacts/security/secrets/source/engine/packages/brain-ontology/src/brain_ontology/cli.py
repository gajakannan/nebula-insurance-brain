"""`python -m brain_ontology.cli` (PRD assumption A1: command-line entry points).

Offline commands read files only: `validate`, `compile` (with `--check`).
Runtime commands act as an authenticated principal through the existing
authorization service: `install`, `install-extension`, `report`, `review`,
`activate`, `rollback`, `history`.

Exit codes: 0 success, 1 refused or invalid content, 2 invalid invocation.
Every result is one JSON document on stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

from brain_ontology.authoring import validate_module
from brain_ontology.compiler import check_release, compile_release, write_release
from brain_ontology.errors import CompileFailed


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    results = [validate_module(Path(p), repo_root=root) for p in args.modules]
    _emit({"command": "validate", "results": [r.summary() for r in results]})
    return 0 if all(r.ok for r in results) else 1


def cmd_compile(args: argparse.Namespace) -> int:
    root = Path(args.root)
    request = Path(args.request)
    try:
        compiled = compile_release(request, root=root)
    except CompileFailed as failed:
        _emit(
            {
                "command": "compile",
                "status": "failed",
                "errors": [i.to_json() for i in failed.issues],
            }
        )
        return 1
    directory = request.parent
    if args.check:
        stale = check_release(compiled, directory, file=request.as_posix())
        _emit(
            {
                "command": "compile --check",
                "status": "failed" if stale else "pass",
                "release_ref": compiled.release_ref,
                "errors": [i.to_json() for i in stale],
            }
        )
        return 1 if stale else 0
    write_release(compiled, directory)
    _emit(
        {
            "command": "compile",
            "status": "pass",
            "release_ref": compiled.release_ref,
            "manifest_digest": compiled.manifest["manifest_digest"],
            "modules": compiled.manifest["modules"],
            "outputs": sorted(compiled.files()),
        }
    )
    return 0


def _runtime(args: argparse.Namespace) -> int:
    from brain_ontology.runtime import run_command

    return asyncio.run(run_command(args, _emit))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brain_ontology.cli", description=__doc__)
    parser.add_argument("--root", default=".", help="repository root for reference resolution")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate module files (offline)")
    v.add_argument("modules", nargs="+")
    v.set_defaults(func=cmd_validate)

    c = sub.add_parser("compile", help="compile a release request (offline)")
    c.add_argument("request")
    c.add_argument("--check", action="store_true", help="compare committed outputs byte for byte")
    c.set_defaults(func=cmd_compile)

    def runtime(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--tenant", type=UUID, required=True)
        p.add_argument("--kb", type=UUID, required=True)
        p.add_argument("--token-file", type=Path, required=True)
        p.add_argument("--config", type=Path, default=None)
        p.set_defaults(func=_runtime)
        return p

    i = runtime("install", "install a compiled release into a tenant/KB")
    i.add_argument("release_dir", type=Path)
    e = runtime("install-extension", "tenant extensions are unsupported (ADR-0081 D1)")
    e.add_argument("module", type=Path)
    r = runtime("report", "build and persist an impact report for an installed candidate")
    r.add_argument("--candidate", required=True)
    rv = runtime("review", "record a review decision on a report")
    rv.add_argument("--report", type=UUID, required=True)
    rv.add_argument("--decision", choices=("approve", "reject"), required=True)
    rv.add_argument("--rationale", required=True)
    a = runtime("activate", "select a reviewed release for future work")
    a.add_argument("--release", required=True)
    a.add_argument("--review", type=UUID, required=True)
    rb = runtime("rollback", "select a previously activated release again")
    rb.add_argument("--release", required=True)
    runtime("history", "list release selections in sequence order")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code not in (0, None) else 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
