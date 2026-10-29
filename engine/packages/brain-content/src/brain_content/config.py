from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(Exception):
    """Raised when the committed local object-store configuration cannot be found or parsed."""


@dataclass(frozen=True)
class LocalObjectStoreConfig:
    provider: str
    root: Path
    immutable: bool


@dataclass(frozen=True)
class ContentWriterConfig:
    v2_writer_enabled: bool = False


def load_content_writer_config() -> ContentWriterConfig:
    override = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
    path = Path(override) if override else _find_config_file(Path.cwd())
    if not path.is_file():
        raise ConfigError("content writer configuration is missing")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    section = data.get("content", {})
    enabled = section.get("v2_writer_enabled", False)
    if type(enabled) is not bool:
        raise ConfigError("content.v2_writer_enabled must be a boolean")
    return ContentWriterConfig(v2_writer_enabled=enabled)


EXTRACTION_PIPELINES = ("direct-baseline", "graph-dense", "graph-direct")


@dataclass(frozen=True)
class ExtractionConfig:
    """Committed pipeline for new submissions; jobs pin it, so changes never mix engines."""

    pipeline: str = "direct-baseline"


def load_extraction_config() -> ExtractionConfig:
    # Only the existing isolated-config facility selects another file; there is
    # deliberately no environment variable naming a pipeline (F0005 Step 6).
    override = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
    path = Path(override) if override else _find_config_file(Path.cwd())
    if not path.is_file():
        raise ConfigError("extraction configuration is missing")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    section = data.get("extraction")
    if not isinstance(section, dict) or "pipeline" not in section:
        raise ConfigError("extraction.pipeline must be set explicitly")
    pipeline = section["pipeline"]
    if pipeline not in EXTRACTION_PIPELINES:
        raise ConfigError("extraction.pipeline is not a known pipeline")
    return ExtractionConfig(pipeline=pipeline)


DEFAULT_MAX_QUEUE_DEPTH = 100


@dataclass(frozen=True)
class JobQueueConfig:
    """Bound on unfinished document jobs; new submissions beyond it are rejected."""

    max_queue_depth: int = DEFAULT_MAX_QUEUE_DEPTH


def load_job_queue_config() -> JobQueueConfig:
    override = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
    path = Path(override) if override else _find_config_file(Path.cwd())
    if not path.is_file():
        raise ConfigError("job queue configuration is missing")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    section = data.get("jobs") or {}
    depth = section.get("max_queue_depth", DEFAULT_MAX_QUEUE_DEPTH)
    if type(depth) is not int or depth <= 0:
        raise ConfigError("jobs.max_queue_depth must be a positive integer")
    return JobQueueConfig(max_queue_depth=depth)


def _find_config_file(start: Path) -> Path:
    """Walk upward from `start` looking for `config/local.yaml` (a fresh checkout may
    run the app from the repo root or from within `engine/`)."""
    for candidate_dir in (start, *start.parents):
        candidate = candidate_dir / "config" / "local.yaml"
        if candidate.is_file():
            return candidate
    raise ConfigError(
        f"config/local.yaml not found by walking up from {start}; "
        "no storage environment variables are supported as a substitute (ADR-0059)."
    )


def load_local_object_store_config() -> LocalObjectStoreConfig:
    override = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
    config_path = Path(override) if override else _find_config_file(Path.cwd())
    if not config_path.is_file():
        raise ConfigError(f"BRAIN_LOCAL_CONFIG_PATH does not exist: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    store = data.get("object_store", {})

    provider = store.get("provider")
    if provider != "filesystem":
        raise ConfigError(
            f"{config_path}: object_store.provider must be 'filesystem' in v0.1, got {provider!r}"
        )

    root_value = store.get("root")
    if not root_value:
        raise ConfigError(f"{config_path}: object_store.root is required")

    # Relative roots resolve against the config file's own directory's parent
    # (the repo root), not the process cwd, so behavior is independent of
    # where the app happens to be launched from.
    repo_root = config_path.parent.parent
    root = (repo_root / root_value).resolve() if not os.path.isabs(root_value) else Path(root_value)

    return LocalObjectStoreConfig(
        provider=provider,
        root=root,
        immutable=bool(store.get("immutable", True)),
    )
