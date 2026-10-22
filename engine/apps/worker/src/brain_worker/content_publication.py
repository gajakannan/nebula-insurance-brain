"""Fenced, authorized content readiness in the queue's existing transaction.

Filesystem completion precedes database readiness. A rolled-back publication
leaves immutable bytes for an authorized retry; it never advertises an orphan.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from brain_content.identities import is_fallback_pair
from brain_content.manifest import Manifest
from brain_content.object_store import ObjectStore
from brain_content.service import VerifiedContentStore
from brain_content.validation import ArtifactConflict, ArtifactKey, VerifiedBundle, verify_bundle
from brain_domain.authx import (
    AuthorizationDecision,
    OperationOutcome,
    RequestedScope,
    ResourceKey,
    ResourceType,
)
from brain_jobs.queue import DocumentJobQueue, JobLease
from brain_persistence.authx import SyncAuthorityStore
from brain_persistence.content_repository import ContentArtifactRepository, lock_content_identity
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationUnavailable, decide, recheck
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from brain_worker.publication_intent import retain_fallback_intent


class AuthorizedContentPublisher:
    def __init__(
        self,
        queue: DocumentJobQueue,
        store: VerifiedContentStore,
        policy: CasbinAuthorizationAdapter,
        *,
        clock: Callable[[], datetime] | None = None,
        objects: ObjectStore | None = None,
    ) -> None:
        self.queue, self.store, self.policy = queue, store, policy
        self.clock = clock or (lambda: datetime.now(UTC))
        self.objects = objects

    def publish_manifest(
        self,
        lease: JobLease,
        manifest: Manifest,
        files: Mapping[str, bytes],
        *,
        writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"] | None = None,
        unattributed_item_count: int = 0,
    ) -> Manifest:
        key = ArtifactKey(
            manifest.artifact_id,
            manifest.tenant_id,
            manifest.knowledge_base_id,
            manifest.artifact_contract_version,
        )
        return self.publish(
            lease,
            key,
            manifest.model_dump_json().encode(),
            files,
            writer_fallback_reason=writer_fallback_reason,
            unattributed_item_count=unattributed_item_count,
        ).manifest

    def publish(
        self,
        lease: JobLease,
        key: ArtifactKey,
        manifest_bytes: bytes,
        files: Mapping[str, bytes],
        *,
        writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"] | None = None,
        unattributed_item_count: int = 0,
    ) -> VerifiedBundle:
        """Commit through the existing fence; persist only failure/denial on rollback."""
        decisions: list[AuthorizationDecision] = []

        def observe(decision: AuthorizationDecision) -> None:
            for index, prior in enumerate(decisions):
                if prior.resource == decision.resource:
                    decisions[index] = decision
                    break
            else:
                decisions.append(decision)

        def operation(connection: Connection) -> VerifiedBundle:
            return self.publish_ready(
                connection,
                lease=lease,
                key=key,
                manifest_bytes=manifest_bytes,
                files=files,
                observe_decision=observe,
                writer_fallback_reason=writer_fallback_reason,
                unattributed_item_count=unattributed_item_count,
            )

        try:
            return self.queue.publish_transaction(lease, operation)
        except Exception:
            # The queue context has exited and rolled back before a fresh audit
            # transaction is opened, including failures at its commit boundary.
            if decisions:
                try:
                    with Session(self.queue.engine) as session, session.begin():
                        for decision in decisions:
                            SyncAuthorityStore(session).append_decision(
                                decision.with_outcome(OperationOutcome.FAILED)
                                if decision.allowed
                                else decision
                            )
                except Exception as exc:
                    raise AuthorizationUnavailable("publication failure audit unavailable") from exc
            raise

    def publish_ready(
        self,
        connection: Connection,
        *,
        lease: JobLease,
        key: ArtifactKey,
        manifest_bytes: bytes,
        files: Mapping[str, bytes],
        observe_decision: Callable[[AuthorizationDecision], None],
        writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"] | None = None,
        unattributed_item_count: int = 0,
    ) -> VerifiedBundle:
        """Callback only: never commit, retry, reparse, or acquire a job lock here."""
        if (key.tenant_id, key.knowledge_base_id) != (
            lease.tenant_id,
            lease.knowledge_base_id,
        ):
            raise PermissionError("publication differs from its fenced resource")
        fallback = key.artifact_id != lease.artifact_id
        if fallback:
            if lease.payload.get("content_contract_version") != 2 or not is_fallback_pair(
                ArtifactKey(lease.artifact_id, lease.tenant_id, lease.knowledge_base_id, 2),
                key,
                document_id=UUID(lease.payload["document_id"]),
                version_id=UUID(lease.payload["version_id"]),
                source_sha256=lease.payload["source_sha256"],
                recipe_sha256=lease.payload["recipe_sha256"],
            ):
                raise PermissionError("publication is not the deterministic v1 fallback")
            if writer_fallback_reason is None and unattributed_item_count:
                raise ValueError("observed fallback count requires an explicit producer reason")
            writer_fallback_reason = "ORIGIN_UNAVAILABLE"
        elif writer_fallback_reason is not None:
            raise ValueError("fallback diagnostics require a v2 source conversion lease")
        executor = UUID(lease.payload["actor_id"])
        delegation = lease.payload.get("delegation_id")
        with Session(bind=connection) as session:
            authority = SyncAuthorityStore(session)
            resources = [ResourceKey(ResourceType.CONTENT_ARTIFACT, lease.artifact_id)]
            if fallback:
                resources.append(ResourceKey(ResourceType.CONTENT_ARTIFACT, key.artifact_id))
            evaluated = decide(
                authority,
                self.policy,
                self.policy.release,
                authenticated_id=executor,
                keys=resources,
                action="ingest",
                requested=RequestedScope(frozenset({key.knowledge_base_id}), (), None, None),
                trace_id=str(UUID(lease.payload["correlation_id"])),
                delegation_id=UUID(delegation) if delegation else None,
                clock=self.clock,
                new_id=uuid4,
                require_record=False,
            )
            for item in evaluated:
                observe_decision(item.decision)
            if any(not item.decision.allowed for item in evaluated):
                raise AuthorizationDenied(
                    next(item.decision for item in evaluated if not item.decision.allowed)
                )
            incoming = verify_bundle(key, manifest_bytes, files)
            manifest = incoming.manifest
            recipe = getattr(manifest, "recipe_sha256", None)
            if key.contract_version == 1:
                recipe = manifest.execution.configuration_hash
            if recipe != lease.payload["recipe_sha256"]:
                raise ArtifactConflict("publication differs from queued parse recipe")
            if manifest.extraction_quality.status == "failed":
                raise ArtifactConflict("failed conversion cannot become ready content")
            if writer_fallback_reason and (
                key.contract_version != 1 or unattributed_item_count < 0
            ):
                raise ValueError("invalid writer fallback metadata")
            if (str(manifest.document_id), str(manifest.version_id), manifest.source_sha256) != (
                lease.payload["document_id"],
                lease.payload["version_id"],
                lease.payload["source_sha256"],
            ):
                raise ArtifactConflict("publication differs from queued source identity")
            lock_content_identity(
                session, key, manifest.document_id, manifest.version_id, manifest.source_sha256
            )
            repository = ContentArtifactRepository(session)
            source = repository.find_source(
                key.tenant_id, key.knowledge_base_id, manifest.source_sha256
            )
            if source and (source[0] != manifest.document_id or any(k != key for k in source[1])):
                raise ArtifactConflict("accepted source requires governed replacement")
            # Full validation and current authority precede the first object write.
            evaluated = [recheck(item, self.policy, self.clock()) for item in evaluated]
            for item in evaluated:
                observe_decision(item.decision)
            if any(not item.decision.allowed for item in evaluated):
                raise AuthorizationDenied(
                    next(item.decision for item in evaluated if not item.decision.allowed)
                )
            if writer_fallback_reason:
                if self.objects is None:
                    raise ValueError("fallback requires the immutable publication intent store")
                unattributed_item_count = retain_fallback_intent(
                    self.objects,
                    incoming,
                    recipe_sha256=recipe,
                    observed_count=unattributed_item_count,
                )
            retained = self.store.publish(key, manifest_bytes, files)
            evaluated = [recheck(item, self.policy, self.clock()) for item in evaluated]
            for item in evaluated:
                observe_decision(item.decision)
            if any(not item.decision.allowed for item in evaluated):
                raise AuthorizationDenied(
                    next(item.decision for item in evaluated if not item.decision.allowed)
                )
            for item in evaluated:
                authority.append_decision(item.decision.with_outcome(OperationOutcome.SUCCEEDED))
            decision = next(item.decision for item in evaluated if item.key.id == key.artifact_id)
            if writer_fallback_reason not in (None, "ORIGIN_UNAVAILABLE"):
                raise ValueError("unknown writer fallback reason")
            repository.register_ready(
                retained,
                actor_id=decision.actor_principal_id,
                authorization_decision_id=decision.decision_id,
                supersedes_artifact_id=None,
                writer_fallback_reason=writer_fallback_reason,
                unattributed_item_count=unattributed_item_count,
            )
            session.flush()
            return retained
