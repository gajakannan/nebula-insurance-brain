"""New-source identities only. Existing registry IDs always take precedence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from uuid import UUID, uuid5

from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.validation import ArtifactConflict, ArtifactKey


class ParserMigrationRequired(ArtifactConflict):
    code = "PARSER_MIGRATION_REQUIRED"


@dataclass(frozen=True)
class ContentIdentity:
    document_id: UUID
    version_id: UUID
    key: ArtifactKey


def new_source_identity(
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    document_id: UUID,
    source_sha256: str,
    recipe_sha256: str,
    contract_version: Literal[1, 2],
) -> ContentIdentity:
    if any(
        re.fullmatch(r"[a-f0-9]{64}", value) is None for value in (source_sha256, recipe_sha256)
    ):
        raise ValueError("invalid source or recipe fingerprint")
    if contract_version == 1:
        version_id = uuid5(document_id, recipe_sha256)
        artifact_id = uuid5(version_id, "content")
    elif contract_version == 2:
        version_id = uuid5(document_id, "source-v1:" + source_sha256)
        artifact_id = uuid5(version_id, "artifact-v2:" + recipe_sha256)
    else:
        raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")
    return ContentIdentity(
        document_id,
        version_id,
        ArtifactKey(artifact_id, tenant_id, knowledge_base_id, contract_version),
    )


def fallback_key(version_id: UUID, tenant_id: UUID, knowledge_base_id: UUID) -> ArtifactKey:
    return ArtifactKey(uuid5(version_id, "content"), tenant_id, knowledge_base_id, 1)


def is_fallback_pair(
    original: ArtifactKey,
    candidate: ArtifactKey,
    *,
    document_id: UUID,
    version_id: UUID,
    source_sha256: str,
    recipe_sha256: str,
) -> bool:
    if original.contract_version != 2:
        return False
    expected = new_source_identity(
        tenant_id=original.tenant_id,
        knowledge_base_id=original.knowledge_base_id,
        document_id=document_id,
        source_sha256=source_sha256,
        recipe_sha256=recipe_sha256,
        contract_version=2,
    )
    return (
        expected.key == original
        and expected.version_id == version_id
        and candidate == fallback_key(version_id, original.tenant_id, original.knowledge_base_id)
    )
