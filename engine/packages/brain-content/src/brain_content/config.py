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
