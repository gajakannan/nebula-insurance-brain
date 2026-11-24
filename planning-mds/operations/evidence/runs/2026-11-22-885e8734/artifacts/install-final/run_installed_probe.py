"""Install wheel and source archives offline with no source checkout mounted."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile


def main() -> None:
    package_root = pathlib.Path("/packages")
    wheelhouse = package_root / "wheels"
    result = {}
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    environment["UV_OFFLINE"] = "1"
    for kind in ("wheel", "sdist"):
        with tempfile.TemporaryDirectory(
            prefix=f"brain-installed-{kind}-"
        ) as directory:
            venv = pathlib.Path(directory) / "venv"
            subprocess.run(
                ["uv", "venv", "--python", "/usr/local/bin/python3", str(venv)],
                env=environment,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            python = venv / "bin/python"
            base = [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--offline",
                "--no-index",
                "--find-links",
                str(wheelhouse),
            ]
            if kind == "sdist":
                subprocess.run(
                    [*base, "setuptools==84.1.0", "wheel"],
                    env=environment,
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
                selections = [
                    str(p) for p in sorted((package_root / "sdists").glob("*.tar.gz"))
                ]
                if len(selections) != 3:
                    raise AssertionError("Source distribution inventory incomplete")
                install = [*base, "--no-build-isolation", *selections]
            else:
                install = [
                    *base,
                    "brain-domain==0.1.0",
                    "brain-contracts==0.1.0",
                    "brain-content==0.1.0",
                ]
            subprocess.run(
                install, env=environment, check=True, stdout=subprocess.DEVNULL
            )
            execution = subprocess.run(
                [str(python), str(package_root / "installed_probe.py")],
                env=environment,
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            if execution.returncode:
                print(execution.stderr, file=sys.stderr)
                execution.check_returncode()
            result[kind] = json.loads(execution.stdout)
    report = {"status": "pass", "installations": result}
    pathlib.Path("/output/installed-distribution-results.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
