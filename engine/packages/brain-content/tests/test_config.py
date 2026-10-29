from __future__ import annotations

from pathlib import Path

import pytest
from brain_content.config import (
    DEFAULT_MAX_QUEUE_DEPTH,
    ConfigError,
    load_content_writer_config,
    load_extraction_config,
    load_job_queue_config,
    load_local_object_store_config,
)


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


@pytest.mark.parametrize(
    "entry,expected", [("", False), ("content:\n  v2_writer_enabled: true\n", True)]
)
def test_v2_writer_is_disabled_unless_explicitly_enabled(tmp_path, monkeypatch, entry, expected):
    path = tmp_path / "local.yaml"
    path.write_text(entry)
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(path))
    assert load_content_writer_config().v2_writer_enabled is expected


@pytest.mark.parametrize("value", ['"true"', '"false"', "1"])
def test_non_boolean_writer_activation_fails_closed(tmp_path, monkeypatch, value):
    path = tmp_path / "local.yaml"
    path.write_text(f"content:\n  v2_writer_enabled: {value}\n")
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(path))
    with pytest.raises(ConfigError):
        load_content_writer_config()


def _write_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> None:
    path = tmp_path / "local.yaml"
    path.write_text(body, encoding="utf-8")
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(path))


@pytest.mark.parametrize("pipeline", ["direct-baseline", "graph-dense", "graph-direct"])
def test_extraction_pipeline_loads_each_known_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pipeline: str
) -> None:
    _write_local(tmp_path, monkeypatch, f"extraction:\n  pipeline: {pipeline}\n")

    assert load_extraction_config().pipeline == pipeline


@pytest.mark.parametrize(
    "body",
    ["{}\n", "extraction: direct-baseline\n", "extraction:\n  other: 1\n"],
)
def test_extraction_pipeline_must_be_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    _write_local(tmp_path, monkeypatch, body)

    with pytest.raises(ConfigError, match="set explicitly"):
        load_extraction_config()


def test_extraction_pipeline_rejects_unknown_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_local(tmp_path, monkeypatch, "extraction:\n  pipeline: graph-sparse\n")

    with pytest.raises(ConfigError, match="not a known pipeline"):
        load_extraction_config()


def test_extraction_and_queue_config_require_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(tmp_path / "missing.yaml"))

    with pytest.raises(ConfigError):
        load_extraction_config()
    with pytest.raises(ConfigError):
        load_job_queue_config()


def test_queue_depth_defaults_when_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_local(tmp_path, monkeypatch, "extraction:\n  pipeline: direct-baseline\n")

    assert load_job_queue_config().max_queue_depth == DEFAULT_MAX_QUEUE_DEPTH


def test_queue_depth_loads_a_positive_integer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_local(tmp_path, monkeypatch, "jobs:\n  max_queue_depth: 7\n")

    assert load_job_queue_config().max_queue_depth == 7


@pytest.mark.parametrize("value", ["0", "-1", "true", "'5'", "2.5"])
def test_queue_depth_rejects_non_positive_or_non_integer_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    _write_local(tmp_path, monkeypatch, f"jobs:\n  max_queue_depth: {value}\n")

    with pytest.raises(ConfigError, match="positive integer"):
        load_job_queue_config()


def test_committed_config_selects_the_baseline_and_default_depth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Path(__file__).resolve().parents[4] / "config" / "local.yaml"
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))

    assert load_extraction_config().pipeline == "direct-baseline"
    assert load_job_queue_config().max_queue_depth == 100
