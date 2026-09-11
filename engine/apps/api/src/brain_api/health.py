from __future__ import annotations

import os
import uuid

from brain_content.config import ConfigError, load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore
from fastapi import APIRouter
from pydantic import BaseModel, Field

from brain_api.versions import collect_versions

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    git_sha: str
    versions: dict[str, str]
    storage: str


def _check_storage_round_trip() -> str:
    """Write and read back a 1 KB object through LocalFilesystemObjectStore,
    proving `config/local.yaml` resolves with no storage environment variables
    (F0001-S0002 acceptance criterion)."""
    try:
        config = load_local_object_store_config()
        store = LocalFilesystemObjectStore(config)
        key = f"_scratch/health-{uuid.uuid4()}.bin"
        payload = b"h" * 1024
        store.create_exclusive(key, payload)
        return "ok" if store.read(key) == payload else "mismatch"
    except ConfigError as exc:
        return f"error: {exc}"
    except OSError as exc:
        return f"error: {exc}"


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        git_sha=os.environ.get("BRAIN_GIT_SHA", "unknown"),
        versions=collect_versions(),
        storage=_check_storage_round_trip(),
    )
