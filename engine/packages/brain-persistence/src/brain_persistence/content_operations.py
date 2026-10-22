"""Operator-only backfill, integrity sweep and explicitly authorized repair.

Each unit reevaluates ingest authority and commits its decision with every effect.
Normal reads never call this service. It neither deletes nor reparses content.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Literal, TypeVar
from uuid import UUID, uuid4

from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.object_store import ObjectNotFoundError
from brain_content.service import ArtifactMetadata, VerifiedContentStore
from brain_content.validation import ArtifactIntegrityError, ArtifactKey, VerifiedBundle
from brain_domain.authx import (
    NO_FILTER,
    AuthorizationDecision,
    OperationOutcome,
    RequestedScope,
    ResourceKey,
    ResourceType,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationUnavailable, decide, recheck
from sqlalchemy import (
    Column,
    MetaData,
    Table,
    UniqueConstraint,
    Uuid,
    inspect,
    select,
    text,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.schema import DropConstraint

from brain_persistence import content_models as tables
from brain_persistence.authx import SyncAuthorityStore
from brain_persistence.content_repository import (
    ContentArtifactRepository,
    lock_artifact,
    lock_content_identity,
)
from brain_persistence.models import ContentArtifact

T = TypeVar("T")
Trigger = Literal["LEGACY_BACKFILL", "INTEGRITY_SWEEP", "AUTHORIZED_REPAIR"]


class ContentIntegrityOperations:
    def __init__(
        self,
        engine: Engine,
        store: VerifiedContentStore,
        policy: CasbinAuthorizationAdapter,
        *,
        actor_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.engine, self.store, self.policy = engine, store, policy
        self.actor_id, self.tenant_id, self.knowledge_base_id = (
            actor_id,
            tenant_id,
            knowledge_base_id,
        )
        self.clock = clock or (lambda: datetime.now(UTC))

    def _unit(
        self,
        artifact_id: UUID,
        operation: Callable[[Session, AuthorizationDecision], T],
        *,
        require_record: bool = True,
    ) -> T:
        def scoped(session: Session, decisions: Sequence[AuthorizationDecision]) -> T:
            decision = decisions[0]
            if decision.scope is None or decision.scope.tenant_id != self.tenant_id:
                raise PermissionError("operator scope does not match trusted owner")
            return operation(session, decision)

        return self._batch(
            [artifact_id],
            scoped,
            require_record=require_record,
            requested=RequestedScope(frozenset({self.knowledge_base_id}), (), None, None),
        )

    def _batch(
        self,
        artifact_ids: Sequence[UUID],
        operation: Callable[[Session, Sequence[AuthorizationDecision]], T],
        *,
        require_record: bool = True,
        requested: RequestedScope = NO_FILTER,
    ) -> T:
        decisions: list[AuthorizationDecision] = []
        try:
            with Session(self.engine) as session, session.begin():
                authority = SyncAuthorityStore(session)
                evaluated = decide(
                    authority,
                    self.policy,
                    self.policy.release,
                    authenticated_id=self.actor_id,
                    keys=[
                        ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)
                        for artifact_id in artifact_ids
                    ],
                    action="ingest",
                    requested=requested,
                    trace_id=str(uuid4()),
                    delegation_id=None,
                    clock=self.clock,
                    new_id=uuid4,
                    require_record=require_record,
                )
                evaluated = [recheck(item, self.policy, self.clock()) for item in evaluated]
                decisions = [item.decision for item in evaluated]
                if any(not decision.allowed for decision in decisions):
                    raise AuthorizationDenied(
                        next(decision for decision in decisions if not decision.allowed)
                    )
                for decision in decisions:
                    authority.append_decision(decision.with_outcome(OperationOutcome.SUCCEEDED))
                result = operation(session, decisions)
                evaluated = [recheck(item, self.policy, self.clock()) for item in evaluated]
                decisions = [item.decision for item in evaluated]
                if any(not decision.allowed for decision in decisions):
                    raise AuthorizationDenied(
                        next(decision for decision in decisions if not decision.allowed)
                    )
                session.flush()
                return result
        except Exception:
            # Session context rolled back all effects before this fresh audit.
            if decisions:
                try:
                    with Session(self.engine) as session, session.begin():
                        for decision in decisions:
                            SyncAuthorityStore(session).append_decision(
                                decision.with_outcome(OperationOutcome.FAILED)
                                if decision.allowed
                                else decision
                            )
                except Exception as exc:
                    raise AuthorizationUnavailable("content operation audit unavailable") from exc
            raise

    def reconcile_uniqueness(self, *, writers_quiesced: bool) -> str:
        """Global DDL: current ingest authority for every artifact, or no DDL.

        Only the catalog-discovered single-column version uniqueness is removed.
        The table lock follows authority and no artifact advisory locks follow it.
        Operators must quiesce ingestion/date/operator writes for this window.
        """
        if not writers_quiesced:
            raise ValueError("uniqueness reconciliation requires quiesced writers")
        if self.engine.dialect.name != "postgresql":
            raise ValueError("uniqueness reconciliation requires PostgreSQL")
        with Session(self.engine) as session:
            ids = tuple(session.scalars(select(ContentArtifact.id)).all())
        if not ids:
            return "DEFERRED_EMPTY"

        def operation(session: Session, decisions: Sequence[AuthorizationDecision]) -> str:
            session.execute(text("LOCK TABLE public.content_artifact IN ACCESS EXCLUSIVE MODE"))
            current = set(session.scalars(select(ContentArtifact.id)).all())
            if current != set(ids):
                raise ValueError("content inventory changed during reconciliation")
            repository = ContentArtifactRepository(session)
            for artifact_id in ids:
                metadata = repository.get_metadata(artifact_id)
                if metadata.publication_state != "ready":
                    raise ValueError("all content must be reconciled and ready")
                self._verify(session, metadata)
            constraints = inspect(session.connection()).get_unique_constraints(
                "content_artifact", schema="public"
            )
            names: list[str] = []
            for row in constraints:
                if row["column_names"] == ["document_version_id"] and isinstance(row["name"], str):
                    names.append(row["name"])
            for name in names:
                constraint = UniqueConstraint("document_version_id", name=name)
                Table(
                    "content_artifact",
                    MetaData(),
                    Column("document_version_id", Uuid),
                    constraint,
                    schema="public",
                )
                session.execute(DropConstraint(constraint))
            for decision in decisions:
                metadata = repository.get_metadata(decision.resource.id)
                audit = repository.authorization_audit(
                    decision.decision_id, decision.actor_principal_id, metadata.key
                )
                repository.mutation_event(
                    audit,
                    "content_uniqueness_reconciled",
                    {
                        "artifact_id": str(metadata.key.artifact_id),
                        "dropped_constraints": names,
                        "authorization_decision_id": str(decision.decision_id),
                    },
                )
            return "RECONCILED"

        return self._batch(ids, operation)

    def _locked(self, session: Session, artifact_id: UUID) -> ArtifactMetadata:
        repository = ContentArtifactRepository(session)
        if not repository.expanded():
            raise RuntimeError("content schema expansion is required")
        metadata = repository.get_metadata(artifact_id)
        if (metadata.key.tenant_id, metadata.key.knowledge_base_id) != (
            self.tenant_id,
            self.knowledge_base_id,
        ):
            raise PermissionError("content operation belongs to another scope")
        lock_content_identity(
            session, metadata.key, metadata.document_id, metadata.version_id, metadata.source_sha256
        )
        session.execute(
            select(ContentArtifact.id).where(ContentArtifact.id == artifact_id).with_for_update()
        ).one()
        return repository.get_metadata(artifact_id)

    def _verify(self, session: Session, metadata: ArtifactMetadata) -> VerifiedBundle:
        try:
            bundle = self.store.load_verified(metadata.key)
        except ObjectNotFoundError:
            raise ArtifactIntegrityError("accepted marker is missing") from None
        except PermissionError:
            raise ArtifactIntegrityError("retained content has another owner") from None
        # Repair verifies immutable identities while expressly leaving quarantine.
        replace(metadata, publication_state="ready").verify_identity(bundle)
        ContentArtifactRepository(session).verify_indexes(bundle)
        return bundle

    def _repair_record(
        self,
        session: Session,
        key: ArtifactKey,
        decision: AuthorizationDecision,
        *,
        kind: str,
        detail: dict,
        storage_key: str | None = None,
        resolves_id: UUID | None = None,
    ) -> UUID:
        record_id = uuid4()
        session.execute(
            tables.content_repair_record.insert().values(
                id=record_id,
                tenant_id=key.tenant_id,
                knowledge_base_id=key.knowledge_base_id,
                artifact_id=key.artifact_id if storage_key is None else None,
                storage_key=storage_key,
                kind=kind,
                detail={**detail, "authorization_decision_id": str(decision.decision_id)},
                resolves_id=resolves_id,
                resolution="REPAIRED" if resolves_id else None,
                recorded_by=decision.actor_principal_id,
            )
        )
        return record_id

    def _transition(
        self,
        session: Session,
        metadata: ArtifactMetadata,
        decision: AuthorizationDecision,
        *,
        target: Literal["ready", "quarantined"],
        trigger: Trigger,
        reason: str,
        repair_id: UUID | None = None,
        values: dict | None = None,
    ) -> None:
        repository = ContentArtifactRepository(session)
        audit = repository.authorization_audit(
            decision.decision_id, decision.actor_principal_id, metadata.key
        )
        audit_id = repository.mutation_event(
            audit,
            "content_artifact_quarantined"
            if target == "quarantined"
            else (
                "content_artifact_repaired"
                if trigger == "AUTHORIZED_REPAIR"
                else "content_artifact_verified"
            ),
            {
                "artifact_id": str(metadata.key.artifact_id),
                "from_state": metadata.publication_state,
                "to_state": target,
                "trigger": trigger,
                "reason_code": reason,
                "authorization_decision_id": str(decision.decision_id),
            },
        )
        session.execute(
            tables.content_artifact_state_event.insert().values(
                id=uuid4(),
                artifact_id=metadata.key.artifact_id,
                tenant_id=metadata.key.tenant_id,
                knowledge_base_id=metadata.key.knowledge_base_id,
                from_state=metadata.publication_state,
                to_state=target,
                trigger=trigger,
                reason_code=reason,
                actor_principal_id=decision.actor_principal_id,
                authorization_decision_id=decision.decision_id,
                audit_event_id=audit_id,
                repair_record_id=repair_id,
            )
        )
        session.execute(
            update(ContentArtifact)
            .where(ContentArtifact.id == metadata.key.artifact_id)
            .values(publication_state=target, **(values or {}))
        )

    def inspect_artifact(self, artifact_id: UUID, *, backfill: bool = False) -> str:
        def operation(session: Session, decision: AuthorizationDecision) -> str:
            metadata = self._locked(session, artifact_id)
            if metadata.publication_state == "quarantined":
                return "QUARANTINED"
            try:
                bundle = self._verify(session, metadata)
            except (ArtifactIntegrityError, ArtifactVersionUnsupported) as exc:
                reason = (
                    "MISSING_FILE"
                    if "missing" in str(exc)
                    else "HASH_MISMATCH"
                    if "hash" in str(exc)
                    else "MANIFEST_INVALID"
                )
                repair = self._repair_record(
                    session,
                    metadata.key,
                    decision,
                    kind="INTEGRITY_FAILURE",
                    detail={"reason_code": reason},
                )
                self._transition(
                    session,
                    metadata,
                    decision,
                    target="quarantined",
                    trigger="LEGACY_BACKFILL" if backfill else "INTEGRITY_SWEEP",
                    reason=reason,
                    repair_id=repair,
                )
                return "QUARANTINED"
            if not backfill or metadata.publication_state == "ready":
                return "VERIFIED"
            observed = {
                "artifact_contract_version": bundle.key.contract_version,
                "recipe_sha256": (
                    bundle.manifest.execution.configuration_hash
                    if bundle.key.contract_version == 1
                    else getattr(bundle.manifest, "recipe_sha256", None)
                ),
                "manifest_sha256": bundle.manifest_sha256,
            }
            row = ContentArtifactRepository(session)._row(artifact_id)
            ambiguous = [
                name
                for name, value in observed.items()
                if row[name] is not None and row[name] != value
            ]
            if ambiguous:
                self._repair_record(
                    session,
                    metadata.key,
                    decision,
                    kind="LEGACY_BACKFILL_BLOCKED",
                    detail={"ambiguous_fields": ambiguous},
                )
                return "BLOCKED"
            self._transition(
                session,
                metadata,
                decision,
                target="ready",
                trigger="LEGACY_BACKFILL",
                reason="VERIFIED",
                values={name: value for name, value in observed.items() if row[name] is None},
            )
            return "READY"

        return self._unit(artifact_id, operation)

    def repair(self, artifact_id: UUID, *, repair_record_id: UUID) -> str:
        def operation(session: Session, decision: AuthorizationDecision) -> str:
            metadata = self._locked(session, artifact_id)
            if metadata.publication_state != "quarantined":
                raise ValueError("authorized repair requires a quarantined artifact")
            records = tables.content_repair_record
            prior = (
                session.execute(
                    select(records).where(
                        records.c.id == repair_record_id,
                        records.c.artifact_id == artifact_id,
                        records.c.tenant_id == metadata.key.tenant_id,
                        records.c.knowledge_base_id == metadata.key.knowledge_base_id,
                        records.c.resolves_id.is_(None),
                    )
                )
                .mappings()
                .one_or_none()
            )
            resolved = session.execute(
                select(records.c.id).where(records.c.resolves_id == repair_record_id)
            ).first()
            if prior is None or resolved:
                raise ValueError("repair record is absent, foreign or already resolved")
            self._verify(session, metadata)
            resolving = self._repair_record(
                session,
                metadata.key,
                decision,
                kind=prior["kind"],
                detail={"reason_code": "REPAIRED"},
                resolves_id=repair_record_id,
            )
            self._transition(
                session,
                metadata,
                decision,
                target="ready",
                trigger="AUTHORIZED_REPAIR",
                reason="REPAIRED",
                repair_id=resolving,
            )
            return "READY"

        return self._unit(artifact_id, operation)

    def record_orphan(self, key: ArtifactKey) -> str:
        if (key.tenant_id, key.knowledge_base_id) != (self.tenant_id, self.knowledge_base_id):
            raise PermissionError("orphan marker has another scope")

        def operation(session: Session, decision: AuthorizationDecision) -> str:
            # Pre-record security metadata, not a source hash, authorizes this unit.
            lock_artifact(session, key.artifact_id)
            if session.get(ContentArtifact, key.artifact_id) is not None:
                return "REGISTERED"
            try:
                self.store.load_verified(key)
                verification = "VERIFIED"
            except ObjectNotFoundError:
                return "ABSENT"
            except (ArtifactIntegrityError, ArtifactVersionUnsupported, PermissionError):
                verification = "INVALID"
            marker = f"{key.prefix}/manifest.json"
            records = tables.content_repair_record
            prior = session.execute(
                select(records.c.id).where(
                    records.c.storage_key == marker,
                    records.c.tenant_id == key.tenant_id,
                    records.c.knowledge_base_id == key.knowledge_base_id,
                    records.c.kind == "ORPHAN_MARKER",
                )
            ).first()
            if prior is None:
                record_id = self._repair_record(
                    session,
                    key,
                    decision,
                    kind="ORPHAN_MARKER",
                    storage_key=marker,
                    detail={
                        "artifact_id": str(key.artifact_id),
                        "contract_version": key.contract_version,
                        "verification": verification,
                    },
                )
                repository = ContentArtifactRepository(session)
                audit = repository.authorization_audit(
                    decision.decision_id, decision.actor_principal_id, key
                )
                repository.mutation_event(
                    audit,
                    "content_repair_recorded",
                    {
                        "repair_record_id": str(record_id),
                        "kind": "ORPHAN_MARKER",
                        "authorization_decision_id": str(decision.decision_id),
                    },
                )
            return "ORPHAN_MARKER"

        return self._unit(key.artifact_id, operation, require_record=False)
