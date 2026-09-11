from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Protocol

from brain_content.config import LocalObjectStoreConfig


class ObjectAlreadyExistsError(Exception):
    """Raised by `create_exclusive` when the key is already occupied."""


class ObjectNotFoundError(Exception):
    """Raised by `read`/`delete` when the key does not exist."""


class ObjectStore(Protocol):
    """Provider-neutral byte-object port beneath `ContentArtifactStore` (ADR-0059).

    Object keys are opaque strings chosen by the caller; callers never see
    filesystem paths, bucket names, or provider-specific URLs.
    """

    def create_exclusive(self, key: str, data: bytes) -> str:
        """Write `data` at `key` iff `key` does not already exist. Returns the
        sha256 hex digest of `data`. Raises ObjectAlreadyExistsError otherwise."""
        ...

    def read(self, key: str) -> bytes:
        """Raises ObjectNotFoundError if `key` does not exist."""
        ...

    def exists(self, key: str) -> bool: ...

    def delete(self, key: str) -> None:
        """Controlled deletion. Raises ObjectNotFoundError if `key` does not exist."""
        ...


class LocalFilesystemObjectStore:
    """v0.1 `ObjectStore` adapter: objects below the configured local root.

    Immutability (ADR-0059) applies to the committed artifact namespace. Keys
    under the reserved `_scratch/` prefix are for operational self-checks (for
    example the `/health` storage round trip) and may be overwritten freely —
    they are never treated as accepted content artifacts.
    """

    _SCRATCH_PREFIX = "_scratch/"

    def __init__(self, config: LocalObjectStoreConfig) -> None:
        self._root = config.root
        self._immutable = config.immutable
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        if not key or key.startswith("/") or ".." in Path(key).parts:
            raise ValueError(f"invalid object key: {key!r}")
        path = (self._root / key).resolve()
        if self._root not in path.parents and path != self._root:
            raise ValueError(f"object key escapes the configured root: {key!r}")
        return path

    def create_exclusive(self, key: str, data: bytes) -> str:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        is_scratch = key.startswith(self._SCRATCH_PREFIX)
        flags = os.O_WRONLY | os.O_CREAT
        flags |= os.O_TRUNC if (is_scratch or not self._immutable) else os.O_EXCL
        try:
            fd = os.open(path, flags, 0o644)
        except FileExistsError as exc:
            raise ObjectAlreadyExistsError(key) from exc
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return hashlib.sha256(data).hexdigest()

    def read(self, key: str) -> bytes:
        path = self._path_for(key)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise ObjectNotFoundError(key) from exc

    def exists(self, key: str) -> bool:
        return self._path_for(key).is_file()

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        try:
            path.unlink()
        except FileNotFoundError as exc:
            raise ObjectNotFoundError(key) from exc
