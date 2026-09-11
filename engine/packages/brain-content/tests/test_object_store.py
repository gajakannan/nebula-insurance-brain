from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import (
    LocalFilesystemObjectStore,
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
)


def _store(tmp_path: Path, *, immutable: bool = True) -> LocalFilesystemObjectStore:
    config = LocalObjectStoreConfig(
        provider="filesystem", root=tmp_path / "content", immutable=immutable
    )
    return LocalFilesystemObjectStore(config)


def test_create_exclusive_writes_and_returns_checksum(tmp_path: Path) -> None:
    store = _store(tmp_path)
    data = b"x" * 1024

    digest = store.create_exclusive("artifacts/a.bin", data)

    assert digest == hashlib.sha256(data).hexdigest()
    assert store.read("artifacts/a.bin") == data


def test_create_exclusive_rejects_duplicate_key_when_immutable(tmp_path: Path) -> None:
    store = _store(tmp_path, immutable=True)
    store.create_exclusive("artifacts/a.bin", b"first")

    with pytest.raises(ObjectAlreadyExistsError):
        store.create_exclusive("artifacts/a.bin", b"second")


def test_scratch_prefix_allows_overwrite_even_when_immutable(tmp_path: Path) -> None:
    store = _store(tmp_path, immutable=True)
    store.create_exclusive("_scratch/probe.bin", b"first")

    store.create_exclusive("_scratch/probe.bin", b"second")

    assert store.read("_scratch/probe.bin") == b"second"


def test_read_missing_key_raises_not_found(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ObjectNotFoundError):
        store.read("missing")


def test_exists_reports_true_only_after_write(tmp_path: Path) -> None:
    store = _store(tmp_path)

    assert store.exists("a.bin") is False
    store.create_exclusive("a.bin", b"data")
    assert store.exists("a.bin") is True


def test_delete_removes_object(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.create_exclusive("a.bin", b"data")

    store.delete("a.bin")

    assert store.exists("a.bin") is False


def test_delete_missing_key_raises_not_found(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ObjectNotFoundError):
        store.delete("missing")


def test_key_cannot_escape_root(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError):
        store.create_exclusive("../escape.bin", b"data")
