"""Private immutable producer diagnostics needed to recover a v1 fallback marker."""

from __future__ import annotations

import json
from contextlib import suppress
from typing import Any, Literal
from uuid import UUID

from brain_content.contracts import decode_json, wire_value
from brain_content.object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore
from brain_content.validation import (
    ArtifactConflict,
    ArtifactIntegrityError,
    VerifiedBundle,
    sha256,
)
from pydantic import BaseModel, ConfigDict, Field, StrictInt


class FallbackIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal[1]
    tenant_id: UUID
    knowledge_base_id: UUID
    document_id: UUID
    version_id: UUID
    artifact_id: UUID
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    recipe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"]
    unattributed_item_count: StrictInt = Field(ge=1)
    intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _digest(value: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            wire_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    )


def _intent(identity: dict[str, Any], count: int) -> FallbackIntent:
    value = {**identity, "unattributed_item_count": count}
    return FallbackIntent(**value, intent_sha256=_digest(value))


def retain_fallback_intent(
    objects: ObjectStore, bundle: VerifiedBundle, *, recipe_sha256: str, observed_count: int
) -> int:
    """Call only inside the publisher's fenced, current-authority transaction.

    Zero means recover the retained count without conversion. Positive counts
    come from this attempt's actual provenance projection, never from inference.
    """
    key, manifest = bundle.key, bundle.manifest
    path = (
        f"publication-intents/{key.tenant_id}/{key.knowledge_base_id}/"
        f"{key.artifact_id}/fallback.json"
    )
    identity = dict(
        contract_version=1,
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        document_id=manifest.document_id,
        version_id=manifest.version_id,
        artifact_id=key.artifact_id,
        source_sha256=manifest.source_sha256,
        artifact_sha256=manifest.artifact_sha256,
        recipe_sha256=recipe_sha256,
        writer_fallback_reason="ORIGIN_UNAVAILABLE",
    )
    incoming = _intent(identity, observed_count) if observed_count else None
    if incoming is not None:
        with suppress(ObjectAlreadyExistsError):
            objects.create_exclusive(path, incoming.model_dump_json().encode())
    try:
        value = decode_json(objects.read(path))
        if not isinstance(value, dict) or type(value.get("contract_version")) is not int:
            raise ValueError("invalid intent version")
        retained = FallbackIntent.model_validate(value)
        if retained.intent_sha256 != _digest(
            retained.model_dump(mode="json", exclude={"intent_sha256"})
        ):
            raise ValueError("intent checksum mismatch")
    except ObjectNotFoundError:
        raise ArtifactIntegrityError("fallback publication intent is missing") from None
    except ValueError:
        raise ArtifactIntegrityError("fallback publication intent is invalid") from None
    expected = _intent(identity, observed_count or retained.unattributed_item_count)
    if retained != expected:
        raise ArtifactConflict("fallback publication intent conflicts with retained source")
    return retained.unattributed_item_count
