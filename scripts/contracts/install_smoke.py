"""Build an offline wheelhouse and source archives for isolated install proof.

Run this in the pinned engine validation runtime. The resulting directory is the
only product material mounted into the network-disabled installation container.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import pathlib
import shutil
import subprocess
import sys
import tomllib
import urllib.request

from packaging.markers import Marker
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGES = ("brain-domain", "brain-contracts", "brain-content")


def prepare(output: pathlib.Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    wheels = output / "wheels"
    sdists = output / "sdists"
    wheels.mkdir(exist_ok=True)
    sdists.mkdir(exist_ok=True)
    for name in PACKAGES:
        package = ROOT / "engine/packages" / name
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--wheel",
                "--outdir",
                str(wheels),
                str(package),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--sdist",
                "--outdir",
                str(sdists),
                str(package),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    locked = tomllib.loads((ROOT / "engine/uv.lock").read_text())
    indexed = {}
    selected: set[str] = set()

    def visit(name: str) -> None:
        if name in selected:
            return
        installed = importlib.metadata.version(name)
        candidates = [
            package
            for package in locked["package"]
            if package["name"] == name
            and package["version"] == installed
            and (
                not package.get("resolution-markers")
                or any(
                    Marker(marker).evaluate()
                    for marker in package["resolution-markers"]
                )
            )
        ]
        if len(candidates) != 1:
            raise ValueError("Installed package is not one exact active lock entry")
        indexed[name] = candidates[0]
        selected.add(name)
        for dependency in indexed[name].get("dependencies", []):
            if dependency.get("marker") and not Marker(dependency["marker"]).evaluate():
                continue
            if (
                dependency.get("version")
                and importlib.metadata.version(dependency["name"])
                != dependency["version"]
            ):
                raise ValueError("Locked dependency version mismatch")
            visit(dependency["name"])

    for name in (*PACKAGES, "setuptools", "wheel"):
        visit(name)
    supported = set(sys_tags())
    fetched = []
    for name in sorted(selected):
        package = indexed[name]
        if name in PACKAGES:
            continue
        for wheel in package.get("wheels", []):
            filename = wheel["url"].rsplit("/", 1)[1]
            if not (parse_wheel_filename(filename)[3] & supported):
                continue
            expected = wheel["hash"].removeprefix("sha256:")
            target = wheels / filename
            raw = (
                target.read_bytes()
                if target.exists()
                else urllib.request.urlopen(wheel["url"], timeout=120).read()
            )
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("Locked wheel digest mismatch")
            target.write_bytes(raw)
            fetched.append(
                {
                    "name": name,
                    "version": package["version"],
                    "file": filename,
                    "sha256": expected,
                }
            )
            break
        else:
            raise ValueError(f"No locked wheel for the validated interpreter: {name}")

    cases = json.loads((ROOT / "scripts/contracts/cases.json").read_bytes())["cases"]
    required = (
        "content-artifact-manifest.schema.json",
        "content-artifact-manifest-v2.schema.json",
        "interpretation-result.schema.json",
        "interpretation-result-v2.schema.json",
        "fact-answer-v1.schema.json",
    )
    fixtures = []
    for contract in required:
        case = next(
            c
            for c in cases
            if c["contract"] == contract
            and c["valid"]
            and c.get("kind", "instance") == "instance"
            and not c.get("pointer")
        )
        fixture = {
            "id": case["id"],
            "contract": contract,
            "version": case["version"],
            "input": case["input"],
        }
        if contract == "interpretation-result.schema.json":
            # Existing native producers emit explicit nullable fields. The
            # portable source fixture remains untouched and is checked separately.
            native = copy.deepcopy(case["input"])
            native["provenance_ledger_ref"] = None
            for assertion in native["assertions"]:
                assertion.setdefault("model_confidence", None)
            fixture["native_input"] = native
        fixtures.append(fixture)
    (output / "fixtures.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    shutil.copyfile(
        ROOT / "scripts/contracts/installed_probe.py", output / "installed_probe.py"
    )
    shutil.copyfile(
        ROOT / "scripts/contracts/run_installed_probe.py",
        output / "run_installed_probe.py",
    )
    manifest = ROOT / "schemas/contracts/v1/manifest.json"
    report = {
        "status": "pass",
        "builder_python": sys.version.split()[0],
        "bundle_digest": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "packages": list(PACKAGES),
        "locked_wheels": fetched,
        "artifacts": {
            str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob("*"))
            if p.is_file() and p.name != "preparation.json"
        },
    }
    (output / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = prepare(args.output.resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "bundle_digest": report["bundle_digest"],
                "packages": report["packages"],
                "locked_wheel_count": len(report["locked_wheels"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
