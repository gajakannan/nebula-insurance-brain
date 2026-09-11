#!/usr/bin/env python3
"""Fail closed if any Docker image reference is unpinned (F0001-S0002).

Checks `docker-compose.yml` `image:`/`build:` references and every
`docker/**/Dockerfile` `FROM` line for a `:latest` tag or a bare (untagged)
image reference. Exits 1 and names the offending line on any violation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

IMAGE_LINE_RE = re.compile(r"^\s*image:\s*(?P<image>\S+)\s*$")
FROM_LINE_RE = re.compile(r"^\s*FROM\s+(?P<image>\S+)", re.IGNORECASE)


def _is_unpinned(image: str) -> bool:
    image = image.strip("\"'")
    if image.endswith(":latest"):
        return True
    # A digest pin (@sha256:...) is always acceptable regardless of tag.
    if "@sha256:" in image:
        return False
    # No ":" after the last "/" means no tag at all (bare image name).
    tail = image.rsplit("/", 1)[-1]
    return ":" not in tail


def check_compose_file(path: Path) -> list[str]:
    violations = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = IMAGE_LINE_RE.match(line)
        if match and _is_unpinned(match.group("image")):
            violations.append(f"{path}:{lineno}: unpinned image reference: {line.strip()}")
    return violations


def check_dockerfile(path: Path) -> list[str]:
    violations = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = FROM_LINE_RE.match(line)
        if match and _is_unpinned(match.group("image")):
            violations.append(f"{path}:{lineno}: unpinned FROM: {line.strip()}")
    return violations


def main(repo_root: Path = REPO_ROOT) -> int:
    violations: list[str] = []

    compose_file = repo_root / "docker-compose.yml"
    if compose_file.is_file():
        violations.extend(check_compose_file(compose_file))

    docker_dir = repo_root / "docker"
    if docker_dir.is_dir():
        for dockerfile in docker_dir.rglob("Dockerfile"):
            violations.extend(check_dockerfile(dockerfile))

    if violations:
        print("Unpinned image references found (F0001-S0002 validation rule):", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1

    print("check_pins: all image references are pinned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
