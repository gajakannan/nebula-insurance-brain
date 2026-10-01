from __future__ import annotations

import mimetypes
from uuid import UUID

from brain_content.store import ArtifactNotFound, ContentArtifactStore
from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.principal import Principal
from brain_security.execution import AuthorizationExecution
from fastapi import APIRouter, Depends, Response

from brain_api.deps import (
    current_principal,
    get_authorization_execution,
    get_content_store,
    new_trace_id,
)
from brain_api.errors import NotFoundError

router = APIRouter(prefix="/content", tags=["Content"])


def _artifact(artifact_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)


@router.get("/{artifact_id}")
async def get_content_artifact_manifest(
    artifact_id: UUID,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    store: ContentArtifactStore = Depends(get_content_store),
) -> Response:
    """Streamed authorized artifact reads — no public or signed URL is ever issued
    (F0001-S0004). F0002: the manifest is loaded only after current authority, the
    artifact's own restrictions and its audit are resolved (S0004 AC7)."""

    async def load(_decision: AuthorizationDecision) -> str:
        try:
            manifest = await store.get_manifest(artifact_id)
        except ArtifactNotFound as exc:
            raise NotFoundError() from exc
        return manifest.model_dump_json()

    body = await execution.read(
        principal, _artifact(artifact_id), Action.READ, trace_id=new_trace_id(), load=load
    )
    return Response(content=body, media_type="application/json")


@router.get("/{artifact_id}/files/{path:path}")
async def get_content_artifact_file(
    artifact_id: UUID,
    path: str,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    store: ContentArtifactStore = Depends(get_content_store),
) -> Response:
    """Streams one bundled file's bytes (the original source, `docling-document.json`,
    ...). Only files declared in the artifact's own manifest are reachable, and the
    bytes are never opened before the allow decision (assembly plan endpoint table)."""

    async def load(_decision: AuthorizationDecision) -> bytes:
        try:
            manifest = await store.get_manifest(artifact_id)
            if path not in {f.path for f in manifest.files}:
                raise NotFoundError()
            return await store.open_file(artifact_id, path)
        except ArtifactNotFound as exc:
            raise NotFoundError() from exc

    data = await execution.read(
        principal, _artifact(artifact_id), Action.READ, trace_id=new_trace_id(), load=load
    )
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return Response(content=data, media_type=content_type)
