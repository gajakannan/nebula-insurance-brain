from __future__ import annotations

import mimetypes
from collections.abc import Sequence
from uuid import UUID, uuid4

from brain_content.store import ArtifactNotFound, ContentArtifactStore
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import SqlAlchemyContentArtifactLookup
from brain_security.authorization import AuthorizationService, ResourceRef
from fastapi import APIRouter, Depends, Response

from brain_api.deps import (
    current_principal,
    current_principal_memberships,
    get_authorization_service,
    get_content_artifact_lookup,
    get_content_store,
)
from brain_api.errors import NotFoundError

router = APIRouter(prefix="/content", tags=["Content"])


async def _authorize_artifact_read(
    artifact_id: UUID,
    principal: Principal,
    memberships: Sequence[Membership],
    authz: AuthorizationService,
    lookup: SqlAlchemyContentArtifactLookup,
) -> None:
    """Streamed authorized artifact reads (F0001-S0004: settles the story's open
    question over a signed short-lived URL vs. an authorized endpoint — no public
    or signed URL is ever issued; every byte read goes through the same
    principal/authz path as any other protected read, per the story's own
    Non-Functional Expectations)."""
    owner = await lookup.get_tenant_and_kb(artifact_id)
    if owner is None:
        raise NotFoundError()
    tenant_id, knowledge_base_id = owner
    resource = ResourceRef(
        type="content_artifact",
        id=artifact_id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
    )
    decision = await authz.authorize(
        principal, memberships, resource, "read", trace_id=str(uuid4())
    )
    if not decision.allowed:
        raise NotFoundError()


@router.get("/{artifact_id}")
async def get_content_artifact_manifest(
    artifact_id: UUID,
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    lookup: SqlAlchemyContentArtifactLookup = Depends(get_content_artifact_lookup),
    store: ContentArtifactStore = Depends(get_content_store),
) -> Response:
    await _authorize_artifact_read(artifact_id, principal, memberships, authz, lookup)
    try:
        manifest = await store.get_manifest(artifact_id)
    except ArtifactNotFound as exc:
        raise NotFoundError() from exc
    return Response(content=manifest.model_dump_json(), media_type="application/json")


@router.get("/{artifact_id}/files/{path:path}")
async def get_content_artifact_file(
    artifact_id: UUID,
    path: str,
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    lookup: SqlAlchemyContentArtifactLookup = Depends(get_content_artifact_lookup),
    store: ContentArtifactStore = Depends(get_content_store),
) -> Response:
    """Streams one bundled file's bytes (the original source, `docling-document.json`,
    ...) — never a public or signed URL. Only files declared in the artifact's own
    manifest are reachable; `path` is validated against it before any read."""
    await _authorize_artifact_read(artifact_id, principal, memberships, authz, lookup)
    try:
        manifest = await store.get_manifest(artifact_id)
    except ArtifactNotFound as exc:
        raise NotFoundError() from exc
    if path not in {f.path for f in manifest.files}:
        raise NotFoundError()
    try:
        data = await store.open_file(artifact_id, path)
    except ArtifactNotFound as exc:
        raise NotFoundError() from exc
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return Response(content=data, media_type=content_type)
