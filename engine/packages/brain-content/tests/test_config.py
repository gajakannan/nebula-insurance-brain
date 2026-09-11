from __future__ import annotations

from pathlib import Path

import pytest
from brain_content.config import ConfigError, load_local_object_store_config


def test_loads_committed_repo_config_from_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "local.yaml"
    config_path.write_text(
        "object_store:\n  provider: filesystem\n  root: ./content\n  immutable: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config_path))

    config = load_local_object_store_config()

    assert config.provider == "filesystem"
    assert config.root == (tmp_path / "content").resolve()
    assert config.immutable is True


def test_missing_config_raises_config_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(tmp_path / "does-not-exist.yaml"))

    with pytest.raises(ConfigError):
        load_local_object_store_config()


def test_rejects_non_filesystem_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "local.yaml"
    config_path.write_text("object_store:\n  provider: s3\n  root: bucket\n", encoding="utf-8")
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config_path))

    with pytest.raises(ConfigError):
        load_local_object_store_config()


def test_discovers_config_by_walking_up_from_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BRAIN_LOCAL_CONFIG_PATH", raising=False)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "local.yaml").write_text(
        "object_store:\n  provider: filesystem\n  root: ./content\n", encoding="utf-8"
    )
    nested_cwd = tmp_path / "engine" / "apps" / "api"
    nested_cwd.mkdir(parents=True)
    monkeypatch.chdir(nested_cwd)

    config = load_local_object_store_config()

    assert config.root == (tmp_path / "content").resolve()


def test_no_config_found_by_walking_up_raises_config_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BRAIN_LOCAL_CONFIG_PATH", raising=False)
    isolated_cwd = tmp_path / "no-config-here"
    isolated_cwd.mkdir()
    monkeypatch.chdir(isolated_cwd)

    with pytest.raises(ConfigError):
        load_local_object_store_config()
