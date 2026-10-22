"""Synchronous worker reads through current F0002 authority and trusted metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_content.object_store import ObjectNotFoundError
from brain_content.service import VerifiedContentStore
from brain_content.validation import ArtifactIntegrityError, VerifiedBundle
from brain_domain.authx import OperationOutcome, RequestedScope, ResourceKey, ResourceType
from brain_jobs.queue import JobLease
from brain_persistence.authx import SyncAuthorityStore
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.models import ContentArtifact
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationUnavailable, decide, recheck
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


class SourceContentAccess:
    def __init__(
        self,
        engine: Engine,
        store: VerifiedContentStore,
        policy: CasbinAuthorizationAdapter,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.engine, self.store, self.policy = engine, store, policy
        self.clock = clock or (lambda: datetime.now(UTC))

    def resolve(self, lease: JobLease) -> VerifiedBundle | None:
        with Session(self.engine) as session:
            source = ContentArtifactRepository(session).find_source(
                lease.tenant_id, lease.knowledge_base_id, lease.payload["source_sha256"]
            )
            if source is None or not source[1]:
                return None
            if len(source[1]) != 1:
                raise ArtifactIntegrityError("source has ambiguous accepted artifacts")
            artifact_id = source[1][0].artifact_id
        return self.read(lease, artifact_id)

    def read(self, lease: JobLease, artifact_id: UUID) -> VerifiedBundle:
        decision = None
        try:
            with Session(self.engine) as session, session.begin():
                authority = SyncAuthorityStore(session)
                (evaluated,) = decide(
                    authority,
                    self.policy,
                    self.policy.release,
                    authenticated_id=UUID(lease.payload["actor_id"]),
                    keys=[ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)],
                    action="read",
                    requested=RequestedScope(frozenset({lease.knowledge_base_id}), (), None, None),
                    trace_id=str(UUID(lease.payload["correlation_id"])),
                    delegation_id=(
                        UUID(lease.payload["delegation_id"])
                        if lease.payload.get("delegation_id")
                        else None
                    ),
                    clock=self.clock,
                    new_id=uuid4,
                )
                evaluated = recheck(evaluated, self.policy, self.clock())
                decision = evaluated.decision
                if not decision.allowed:
                    raise AuthorizationDenied(decision)
                session.execute(
                    select(ContentArtifact.id)
                    .where(ContentArtifact.id == artifact_id)
                    .with_for_update(read=True)
                ).one()
                repository = ContentArtifactRepository(session)
                metadata = repository.get_metadata(artifact_id)
                if (
                    metadata.key.tenant_id,
                    metadata.key.knowledge_base_id,
                    metadata.source_sha256,
                ) != (lease.tenant_id, lease.knowledge_base_id, lease.payload["source_sha256"]):
                    raise ArtifactIntegrityError("job and accepted source identities disagree")
                try:
                    bundle = self.store.load_verified(metadata.key)
                except ObjectNotFoundError:
                    raise ArtifactIntegrityError("accepted source marker is missing") from None
                except PermissionError:
                    raise ArtifactIntegrityError("accepted source has another owner") from None
                metadata.verify_identity(bundle)
                repository.verify_indexes(bundle)
                evaluated = recheck(evaluated, self.policy, self.clock())
                decision = evaluated.decision
                if not decision.allowed:
                    raise AuthorizationDenied(decision)
                authority.append_decision(decision.with_outcome(OperationOutcome.SUCCEEDED))
                return bundle
        except Exception:
            if decision is not None:
                try:
                    with Session(self.engine) as session, session.begin():
                        SyncAuthorityStore(session).append_decision(
                            decision.with_outcome(OperationOutcome.FAILED)
                            if decision.allowed
                            else decision
                        )
                except Exception as exc:
                    raise AuthorizationUnavailable("worker content read audit unavailable") from exc
            raise
