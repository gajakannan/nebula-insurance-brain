from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "dev"))

import check_pins  # noqa: E402


def test_repo_compose_and_dockerfiles_are_pinned() -> None:
    assert check_pins.main(REPO_ROOT) == 0


def test_latest_tag_in_compose_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  a:\n    image: postgres:latest\n", encoding="utf-8"
    )

    assert check_pins.main(tmp_path) == 1


def test_bare_image_in_compose_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  a:\n    image: postgres\n", encoding="utf-8"
    )

    assert check_pins.main(tmp_path) == 1


def test_pinned_image_in_compose_passes(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  a:\n    image: postgres:18.0-trixie\n", encoding="utf-8"
    )

    assert check_pins.main(tmp_path) == 0


def test_unpinned_dockerfile_from_is_rejected(tmp_path: Path) -> None:
    docker_dir = tmp_path / "docker" / "x"
    docker_dir.mkdir(parents=True)
    (docker_dir / "Dockerfile").write_text("FROM ubuntu\n", encoding="utf-8")

    assert check_pins.main(tmp_path) == 1


def test_digest_pinned_image_passes(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  a:\n    image: postgres@sha256:" + "0" * 64 + "\n", encoding="utf-8"
    )

    assert check_pins.main(tmp_path) == 0
