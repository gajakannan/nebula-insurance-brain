from __future__ import annotations

import mimetypes
from uuid import UUID

from brain_content.object_store import ObjectNotFoundError
from brain_content.store import ArtifactNotFound, ContentArtifactStore
from brain_content.validation import ArtifactIntegrityError, VerifiedBundle
from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.principal import Principal
from brain_persistence.content_repository import ContentArtifactRepository
from brain_security.execution import AuthorizationExecution
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.deps import (
    current_principal,
    get_authorization_execution,
    get_content_store,
    get_db_session,
    new_trace_id,
)
from brain_api.errors import ContentUnavailableError, NotFoundError

router = APIRouter(prefix="/content", tags=["Content"])


def _artifact(artifact_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)


async def _load_verified(
    session: AsyncSession, store: ContentArtifactStore, artifact_id: UUID
) -> VerifiedBundle:
    metadata = await session.run_sync(
        lambda s: ContentArtifactRepository(s).get_metadata(artifact_id)
    )
    try:
        bundle = await store.load_verified(metadata.key)
    except (ObjectNotFoundError, ArtifactNotFound):
        # An authorized database row promises a retained completed bundle.
        raise ArtifactIntegrityError("accepted content is missing") from None
    except (ValueError, PermissionError) as exc:
        # Unsafe filesystem keys/symlinks and malformed retained contracts are
        # definitive integrity failures, never another namespace lookup.
        from brain_content.manifest import ArtifactVersionUnsupported

        if isinstance(exc, (ArtifactIntegrityError, ArtifactVersionUnsupported)):
            raise
        raise ArtifactIntegrityError("invalid retained content") from None
    except OSError:
        raise ContentUnavailableError() from None
    metadata.verify_identity(bundle)
    await session.run_sync(lambda s: ContentArtifactRepository(s).verify_indexes(bundle))
    return bundle


@router.get("/{artifact_id}")
async def get_content_artifact_manifest(
    artifact_id: UUID,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    store: ContentArtifactStore = Depends(get_content_store),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """Streamed authorized artifact reads — no public or signed URL is ever issued
    (F0001-S0004). F0002: the manifest is loaded only after current authority, the
    artifact's own restrictions and its audit are resolved (S0004 AC7)."""

    async def load(_decision: AuthorizationDecision) -> bytes:
        return (await _load_verified(session, store, artifact_id)).manifest_bytes

    body = await execution.read(
        principal, _artifact(artifact_id), Action.READ, trace_id=new_trace_id(), load=load
    )
    return Response(
        content=body,
        media_type="application/json",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/{artifact_id}/files/{path:path}")
async def get_content_artifact_file(
    artifact_id: UUID,
    path: str,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    store: ContentArtifactStore = Depends(get_content_store),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """Streams one bundled file's bytes (the original source, `docling-document.json`,
    ...). Only files declared in the artifact's own manifest are reachable, and the
    bytes are never opened before the allow decision (assembly plan endpoint table)."""

    async def load(_decision: AuthorizationDecision) -> bytes:
        bundle = await _load_verified(session, store, artifact_id)
        if path not in bundle.files:
            raise NotFoundError()
        return bundle.files[path]

    data = await execution.read(
        principal, _artifact(artifact_id), Action.READ, trace_id=new_trace_id(), load=load
    )
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    safe_types = {
        "application/pdf",
        "application/json",
        "text/plain",
        "text/markdown",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
    return Response(
        content=data,
        media_type=(content_type if content_type in safe_types else "application/octet-stream"),
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )
