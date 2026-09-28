"""Synthetic development fixtures over the trusted provisioning services (F0002).

Test and local-harness helpers only: every builder calls the same operational
services a real deployment uses (`tenancy`, `identity`, `grants`), so a fixture
can never create state that production code paths could not. Synthetic labels
here are development data, kept outside any frozen evaluation holdout.

All builders are synchronous `Session` functions; async callers use
`await session.run_sync(lambda s: seed_...(s, ...))`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from brain_domain.authx import (
    LabelSet,
    PilotRole,
    ResourceKey,
    ResourceType,
    ScopedId,
    Selector,
    unrestricted_selectors,
)
from brain_domain.principal import Principal, PrincipalKind
from brain_persistence.grants import activate_policy_release, grant_membership
from brain_persistence.identity import provision_principal
from brain_persistence.models import (
    Assertion,
    ContentArtifact,
    DocumentVersion,
    FactSlotRow,
    ReviewBatchRow,
    ReviewItemRow,
    SourceDocument,
)
from brain_persistence.tenancy import (
    provision_resource_access,
    provision_scope,
    resolve_entity,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from sqlalchemy.orm import Session

SYNTHETIC_OPERATOR = UUID("00000000-0000-4000-8000-0000000f0002")
FIXTURE_APPROVAL = "synthetic-fixture"
DEFAULT_CLASSIFICATION = ("internal",)


def utc_now() -> datetime:
    return datetime.now(UTC)


def workspace_for(tenant_id: UUID) -> UUID:
    """Deterministic synthetic workspace for tests that only name tenant and KB."""
    return uuid5(NAMESPACE_URL, f"nebula:test-workspace:{tenant_id}")


def activate_policy(session: Session, model_path: Path, policy_path: Path) -> None:
    release = CasbinAuthorizationAdapter(model_path, policy_path).release
    activate_policy_release(
        session,
        release,
        operator_id=SYNTHETIC_OPERATOR,
        approval_ref=FIXTURE_APPROVAL,
        at=utc_now(),
    )


def seed_scope(
    session: Session,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    workspace_id: UUID | None = None,
) -> UUID:
    workspace_id = workspace_id or workspace_for(tenant_id)
    provision_scope(
        session,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        knowledge_base_id=knowledge_base_id,
        actor_id=SYNTHETIC_OPERATOR,
        at=utc_now(),
    )
    return workspace_id


def seed_principal(
    session: Session, *, issuer: str, subject: str, kind: PrincipalKind = PrincipalKind.USER
) -> Principal:
    return provision_principal(
        session,
        issuer=issuer,
        subject=subject,
        kind=kind,
        operator_id=SYNTHETIC_OPERATOR,
        approval_ref=FIXTURE_APPROVAL,
        at=utc_now(),
    )


def seed_grant(
    session: Session,
    principal_id: UUID,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    role: PilotRole | str,
    *,
    selectors: Sequence[Selector] | None = None,
    classifications: LabelSet | Iterable[str] = "*",
    source_acl_ids: LabelSet | Iterable[str] = "*",
    valid_from: datetime | None = None,
    expires_at: datetime | None = None,
) -> UUID:
    """A complete grant slice. The fixture default is explicit trusted data
    (`all` selectors, `*` labels) — the production API has no such default."""
    seed_scope(session, tenant_id, knowledge_base_id)
    return grant_membership(
        session,
        principal_id=principal_id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        role=role,
        selectors=selectors if selectors is not None else unrestricted_selectors(),
        classifications=classifications,
        source_acl_ids=source_acl_ids,
        valid_from=valid_from or utc_now() - timedelta(minutes=1),
        expires_at=expires_at,
        operator_id=SYNTHETIC_OPERATOR,
        approval_ref=FIXTURE_APPROVAL,
        at=utc_now(),
    )


def protect(
    session: Session,
    key: ResourceKey,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    *,
    classifications: Iterable[str] = DEFAULT_CLASSIFICATION,
    source_acl_ids: Iterable[str] = (),
    parent_chain: Iterable[ScopedId] = (),
    dependency_keys: Iterable[ResourceKey] = (),
    before_record: bool = False,
) -> None:
    seed_scope(session, tenant_id, knowledge_base_id)
    provision_resource_access(
        session,
        key,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        classifications=classifications,
        source_acl_ids=source_acl_ids,
        parent_chain=parent_chain,
        dependency_keys=dependency_keys,
        actor_id=SYNTHETIC_OPERATOR,
        at=utc_now(),
        allow_before_record=before_record,
    )


def seed_content_artifact(
    session: Session, tenant_id: UUID, knowledge_base_id: UUID, **restrictions: object
) -> UUID:
    seed_scope(session, tenant_id, knowledge_base_id)
    owner = {"tenant_id": tenant_id, "knowledge_base_id": knowledge_base_id}
    source = SourceDocument(source_sha256=uuid4().hex, **owner)
    session.add(source)
    session.flush()
    version = DocumentVersion(source_document_id=source.id, **owner)
    session.add(version)
    session.flush()
    artifact = ContentArtifact(
        id=uuid4(),
        document_version_id=version.id,
        artifact_sha256=uuid4().hex,
        page_count=1,
        extraction_status="complete",
        **owner,
    )
    session.add(artifact)
    session.flush()
    protect(
        session,
        ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact.id),
        tenant_id,
        knowledge_base_id,
        **restrictions,  # type: ignore[arg-type]
    )
    return artifact.id


def seed_review_item(
    session: Session,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    *,
    assembling_principal_id: UUID,
    batch_id: UUID | None = None,
    **restrictions: object,
) -> tuple[UUID, UUID]:
    """Returns (review_item_id, review_batch_id)."""
    seed_scope(session, tenant_id, knowledge_base_id)
    owner = {"tenant_id": tenant_id, "knowledge_base_id": knowledge_base_id}
    assertion = Assertion(
        id=uuid4(),
        run_id=None,
        origin="MACHINE_EXTRACTION",
        subject_type="Policy",
        slot_type="each_occurrence_limit",
        value={"value": "$20,000,000"},
        model_confidence=0.41,
        interpretation_basis="EXPLICIT",
        **owner,
    )
    session.add(assertion)
    session.flush()
    if batch_id is None:
        batch = ReviewBatchRow(id=uuid4(), assembling_principal_id=assembling_principal_id, **owner)
        session.add(batch)
        session.flush()
        batch_id = batch.id
    item = ReviewItemRow(
        id=uuid4(),
        type="LOW_CONFIDENCE_ASSERTION",
        status="open",
        assertion_id=assertion.id,
        assertion_version=1,
        review_batch_id=batch_id,
        **owner,
    )
    session.add(item)
    session.flush()
    protect(
        session,
        ResourceKey(ResourceType.REVIEW_TASK, item.id),
        tenant_id,
        knowledge_base_id,
        **restrictions,  # type: ignore[arg-type]
    )
    return item.id, batch_id


def seed_fact_slot(
    session: Session,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    *,
    external_key: str | None = None,
    **restrictions: object,
) -> UUID:
    seed_scope(session, tenant_id, knowledge_base_id)
    entity_id = resolve_entity(
        session,
        tenant_id,
        namespace="synthetic-account",
        external_key=external_key or uuid4().hex,
        actor_id=SYNTHETIC_OPERATOR,
        at=utc_now(),
    )
    slot = FactSlotRow(
        id=uuid4(),
        entity_id=entity_id,
        slot_type="each_occurrence_limit",
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
    )
    session.add(slot)
    session.flush()
    protect(
        session,
        ResourceKey(ResourceType.FACT_SLOT, slot.id),
        tenant_id,
        knowledge_base_id,
        **restrictions,  # type: ignore[arg-type]
    )
    return slot.id
