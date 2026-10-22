"""Authorized append-only document dates; no production authoring endpoint."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from brain_content.dates import (
    ContentDateBasis,
    DateBasis,
    DateBasisInput,
    DateBasisInvalid,
    DateSelectionStale,
    DocumentDateCandidate,
    DocumentDateSelection,
    DocumentDateValue,
    DocumentDateView,
    HumanDateBasis,
    HumanDateDecisionVerifier,
    HumanDateInput,
    HumanDateSelectionVerifier,
    HumanDecisionReceipt,
    IdempotencyConflict,
    SourceMetadataDateBasis,
    SourceMetadataDateInput,
    SourceMetadataDateVerifier,
    UnavailableHumanDateVerifier,
    UnavailableSourceMetadataVerifier,
    command_hash,
    reject_processing_date,
    verify_content_date_basis,
)
from brain_content.service import ArtifactMetadata
from brain_content.validation import ArtifactKey, VerifiedBundle
from brain_domain.authx import AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.principal import Principal
from brain_security.execution import AuthorizationExecution
from pydantic import TypeAdapter
from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from brain_persistence import content_models as tables
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.models import DocumentVersion


class AsyncVerifiedContentStore(Protocol):
    async def load_verified(self, key: ArtifactKey) -> VerifiedBundle: ...


def candidate_record(row: Mapping[Any, Any]) -> DocumentDateCandidate:
    return DocumentDateCandidate(
        **{
            name: row[name]
            for name in (
                "id",
                "document_version_id",
                "tenant_id",
                "knowledge_base_id",
                "created_at",
                "actor_principal_id",
                "authorization_decision_id",
                "authorization_audit_event_id",
                "idempotency_key",
                "supersedes_id",
            )
        },
        contract_version=1,
        record_type="candidate",
        date=DocumentDateValue(value=row["date_value"], precision=row["date_precision"]),
        basis=TypeAdapter(DateBasis).validate_json(json.dumps(row["basis"])),
    )


def selection_record(row: Mapping[Any, Any]) -> DocumentDateSelection:
    return DocumentDateSelection(
        **{
            name: row[name]
            for name in (
                "id",
                "document_version_id",
                "tenant_id",
                "knowledge_base_id",
                "created_at",
                "actor_principal_id",
                "authorization_decision_id",
                "authorization_audit_event_id",
                "idempotency_key",
                "candidate_id",
                "previous_selection_id",
                "sequence",
                "reason",
            )
        },
        contract_version=1,
        record_type="selection",
        human_decision=HumanDecisionReceipt(
            decision_id=row["human_decision_id"],
            actor_principal_id=row["human_actor_principal_id"],
            authorization_decision_id=row["human_authorization_decision_id"],
            decided_at=row["human_decided_at"],
            receipt_sha256=row["human_receipt_sha256"],
        ),
    )


def _owned(table: Table, metadata: ArtifactMetadata) -> tuple[ColumnElement[bool], ...]:
    return (
        table.c.document_version_id == metadata.version_id,
        table.c.tenant_id == metadata.key.tenant_id,
        table.c.knowledge_base_id == metadata.key.knowledge_base_id,
    )


class DocumentDateService:
    def __init__(
        self,
        session: AsyncSession,
        execution: AuthorizationExecution,
        content: AsyncVerifiedContentStore,
        *,
        human_dates: HumanDateDecisionVerifier | None = None,
        human_selections: HumanDateSelectionVerifier | None = None,
        source_metadata: SourceMetadataDateVerifier | None = None,
    ) -> None:
        self.session, self.execution, self.content = session, execution, content
        self.human_dates = human_dates or UnavailableHumanDateVerifier()
        self.human_selections = human_selections or UnavailableHumanDateVerifier()
        self.source_metadata = source_metadata or UnavailableSourceMetadataVerifier()

    async def _metadata(
        self, artifact_id: UUID, *, lock: bool, shared: bool = False
    ) -> ArtifactMetadata:
        def load(session: Session) -> ArtifactMetadata:
            metadata = ContentArtifactRepository(session).get_metadata(artifact_id)
            if lock:
                session.execute(
                    select(DocumentVersion.id)
                    .where(
                        DocumentVersion.id == metadata.version_id,
                        DocumentVersion.tenant_id == metadata.key.tenant_id,
                        DocumentVersion.knowledge_base_id == metadata.key.knowledge_base_id,
                    )
                    .with_for_update(read=shared)
                ).one()
            return metadata

        return await self.session.run_sync(load)

    async def _verified(self, metadata: ArtifactMetadata) -> VerifiedBundle:
        bundle = await self.content.load_verified(metadata.key)
        metadata.verify_identity(bundle)
        await self.session.run_sync(lambda s: ContentArtifactRepository(s).verify_indexes(bundle))
        return bundle

    def _human_basis(
        self, decision_id: UUID, version_id: UUID, date: DocumentDateValue
    ) -> HumanDateBasis:
        verified = self.human_dates.verify(
            decision_id,
            document_version_id=version_id,
            date_value=date.value,
            precision=date.precision,
        )
        if (
            verified.decision_id,
            verified.document_version_id,
            verified.date_value,
            verified.precision,
        ) != (decision_id, version_id, date.value, date.precision):
            raise DateBasisInvalid("human date receipt does not match the command")
        if verified.decided_at > datetime.now(UTC):
            raise DateBasisInvalid("human decision is in the future")
        return HumanDateBasis(
            kind="HUMAN",
            **verified.model_dump(exclude={"document_version_id", "date_value", "precision"}),
        )

    async def append_candidate(
        self,
        principal: Principal,
        *,
        artifact_id: UUID,
        date: DocumentDateValue,
        basis: DateBasisInput,
        supersedes_id: UUID | None,
        idempotency_key: str,
        trace_id: str,
    ) -> DocumentDateCandidate:
        keys = [ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)]
        if isinstance(basis, ContentDateBasis) and basis.artifact_id != artifact_id:
            keys.append(ResourceKey(ResourceType.CONTENT_ARTIFACT, basis.artifact_id))

        async def operation(decisions: Sequence[AuthorizationDecision]) -> DocumentDateCandidate:
            metadata = await self._metadata(artifact_id, lock=True)
            await self._verified(metadata)
            if not idempotency_key:
                raise DateBasisInvalid("idempotency key is required")
            request = command_hash(
                {
                    "artifact_id": artifact_id,
                    "date": date,
                    "basis": basis,
                    "supersedes_id": supersedes_id,
                    "actor_id": principal.id,
                }
            )
            if isinstance(basis, ContentDateBasis):
                referenced = await self._metadata(basis.artifact_id, lock=False)
                if (
                    referenced.version_id,
                    referenced.key.tenant_id,
                    referenced.key.knowledge_base_id,
                ) != (metadata.version_id, metadata.key.tenant_id, metadata.key.knowledge_base_id):
                    raise DateBasisInvalid("content basis belongs to another version")
                verify_content_date_basis(await self._verified(referenced), basis)
                retained: DateBasis = basis
            elif isinstance(basis, SourceMetadataDateInput):
                reject_processing_date(basis.field)
                retained = self.source_metadata.verify(
                    document_version_id=metadata.version_id,
                    system=basis.system,
                    record_id=basis.record_id,
                    field=basis.field,
                    date=date,
                )
                if (retained.system, retained.record_id, retained.field) != (
                    basis.system,
                    basis.record_id,
                    basis.field,
                ):
                    raise DateBasisInvalid("source metadata receipt does not match the command")
                # Revalidate returned trusted objects too, including its snapshot hash.
                retained = SourceMetadataDateBasis.model_validate(retained.model_dump())
            elif isinstance(basis, HumanDateInput):
                retained = self._human_basis(basis.decision_id, metadata.version_id, date)
            else:
                raise DateBasisInvalid("unsupported date basis")

            def append(session: Session) -> DocumentDateCandidate:
                table = tables.document_date_candidate
                existing = (
                    session.execute(
                        select(table).where(
                            *_owned(table, metadata),
                            table.c.idempotency_key == idempotency_key,
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if existing:
                    if existing["request_sha256"] != request:
                        raise IdempotencyConflict("date request key changed")
                    return candidate_record(existing)
                if supersedes_id:
                    seen: set[UUID] = set()
                    predecessor: UUID | None = supersedes_id
                    while predecessor:
                        if predecessor in seen:
                            raise DateBasisInvalid("candidate correction cycle")
                        seen.add(predecessor)
                        row = (
                            session.execute(
                                select(table).where(
                                    *_owned(table, metadata),
                                    table.c.id == predecessor,
                                )
                            )
                            .mappings()
                            .one_or_none()
                        )
                        if row is None:
                            raise DateBasisInvalid(
                                "candidate predecessor belongs to another version"
                            )
                        predecessor = row["supersedes_id"]
                repository = ContentArtifactRepository(session)
                decision = next(d for d in decisions if d.resource.id == artifact_id)
                audit = repository.authorization_audit(
                    decision.decision_id, decision.actor_principal_id, metadata.key
                )
                row = (
                    session.execute(
                        table.insert()
                        .values(
                            id=uuid4(),
                            document_version_id=metadata.version_id,
                            tenant_id=metadata.key.tenant_id,
                            knowledge_base_id=metadata.key.knowledge_base_id,
                            date_value=date.value,
                            date_precision=date.precision,
                            basis_kind=retained.kind,
                            basis=retained.model_dump(mode="json"),
                            content_artifact_id=retained.artifact_id
                            if isinstance(retained, ContentDateBasis)
                            else None,
                            content_block_id=retained.block_id
                            if isinstance(retained, ContentDateBasis)
                            else None,
                            supersedes_id=supersedes_id,
                            idempotency_key=idempotency_key,
                            request_sha256=request,
                            actor_principal_id=decision.actor_principal_id,
                            authorization_decision_id=decision.decision_id,
                            authorization_audit_event_id=audit.id,
                        )
                        .returning(table)
                    )
                    .mappings()
                    .one()
                )
                repository.mutation_event(
                    audit,
                    "document_date_candidate_recorded",
                    {
                        "candidate_id": str(row["id"]),
                        "version_id": str(metadata.version_id),
                        "supersedes_id": str(supersedes_id) if supersedes_id else None,
                        "authorization_decision_id": str(decision.decision_id),
                    },
                )
                return candidate_record(row)

            return await self.session.run_sync(append)

        return await self.execution.mutate(
            principal, keys, "ingest", trace_id=trace_id, operation=operation
        )

    async def select(
        self,
        principal: Principal,
        *,
        artifact_id: UUID,
        candidate_id: UUID | None,
        expected_selection_id: UUID | None,
        human_decision_id: UUID,
        reason: str,
        idempotency_key: str,
        trace_id: str,
    ) -> DocumentDateSelection:
        async def operation(decisions: Sequence[AuthorizationDecision]) -> DocumentDateSelection:
            metadata = await self._metadata(artifact_id, lock=True)
            await self._verified(metadata)
            if not idempotency_key or not reason:
                raise DateBasisInvalid("selection requires reason and idempotency key")
            verified = self.human_selections.verify_selection(
                human_decision_id,
                document_version_id=metadata.version_id,
                candidate_id=candidate_id,
                expected_selection_id=expected_selection_id,
            )
            if (
                verified.decision_id,
                verified.document_version_id,
                verified.candidate_id,
                verified.expected_selection_id,
            ) != (human_decision_id, metadata.version_id, candidate_id, expected_selection_id):
                raise DateBasisInvalid("human selection receipt does not match the command")
            if verified.decided_at > datetime.now(UTC):
                raise DateBasisInvalid("human decision is in the future")
            receipt = HumanDecisionReceipt.model_validate(
                verified.model_dump(
                    exclude={"document_version_id", "candidate_id", "expected_selection_id"}
                )
            )
            request = command_hash(
                {
                    "artifact_id": artifact_id,
                    "candidate_id": candidate_id,
                    "expected_selection_id": expected_selection_id,
                    "human_decision_id": human_decision_id,
                    "reason": reason,
                    "actor_id": principal.id,
                }
            )

            def append(session: Session) -> DocumentDateSelection:
                table = tables.document_date_selection
                existing = (
                    session.execute(
                        select(table).where(
                            *_owned(table, metadata),
                            table.c.idempotency_key == idempotency_key,
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if existing:
                    if existing["request_sha256"] != request:
                        raise IdempotencyConflict("date selection request key changed")
                    return selection_record(existing)
                latest = (
                    session.execute(
                        select(table)
                        .where(*_owned(table, metadata))
                        .order_by(table.c.sequence.desc())
                        .limit(1)
                    )
                    .mappings()
                    .one_or_none()
                )
                if (latest["id"] if latest else None) != expected_selection_id:
                    raise DateSelectionStale("date selection changed")
                if candidate_id:
                    candidates = tables.document_date_candidate
                    row = (
                        session.execute(
                            select(candidates).where(
                                *_owned(candidates, metadata),
                                candidates.c.id == candidate_id,
                            )
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if row is None:
                        raise DateBasisInvalid("selected candidate belongs to another version")
                    candidate = candidate_record(row)
                    if isinstance(candidate.basis, HumanDateBasis):
                        current = self._human_basis(
                            candidate.basis.decision_id, metadata.version_id, candidate.date
                        )
                        if current != candidate.basis:
                            raise DateBasisInvalid("human candidate receipt changed")
                repository = ContentArtifactRepository(session)
                decision = next(d for d in decisions if d.resource.id == artifact_id)
                audit = repository.authorization_audit(
                    decision.decision_id, decision.actor_principal_id, metadata.key
                )
                row = (
                    session.execute(
                        table.insert()
                        .values(
                            id=uuid4(),
                            document_version_id=metadata.version_id,
                            tenant_id=metadata.key.tenant_id,
                            knowledge_base_id=metadata.key.knowledge_base_id,
                            candidate_id=candidate_id,
                            previous_selection_id=expected_selection_id,
                            human_decision_id=receipt.decision_id,
                            human_actor_principal_id=receipt.actor_principal_id,
                            human_authorization_decision_id=receipt.authorization_decision_id,
                            human_decided_at=receipt.decided_at,
                            human_receipt_sha256=receipt.receipt_sha256,
                            sequence=latest["sequence"] + 1 if latest else 1,
                            reason=reason,
                            idempotency_key=idempotency_key,
                            request_sha256=request,
                            actor_principal_id=decision.actor_principal_id,
                            authorization_decision_id=decision.decision_id,
                            authorization_audit_event_id=audit.id,
                        )
                        .returning(table)
                    )
                    .mappings()
                    .one()
                )
                repository.mutation_event(
                    audit,
                    "document_date_selected",
                    {
                        "selection_id": str(row["id"]),
                        "version_id": str(metadata.version_id),
                        "candidate_id": str(candidate_id) if candidate_id else None,
                        "previous_selection_id": str(expected_selection_id)
                        if expected_selection_id
                        else None,
                        "authorization_decision_id": str(decision.decision_id),
                        "human_decision_id": str(human_decision_id),
                    },
                )
                return selection_record(row)

            return await self.session.run_sync(append)

        return await self.execution.mutate(
            principal,
            [ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)],
            "ingest",
            trace_id=trace_id,
            operation=operation,
        )

    async def read(
        self, principal: Principal, *, artifact_id: UUID, selection_id: UUID | None, trace_id: str
    ) -> DocumentDateView:
        async def load(_decision: AuthorizationDecision) -> DocumentDateView:
            # WHY: READ COMMITTED candidate/selection queries need one stable
            # view. Writers lock this version FOR UPDATE; hold FOR SHARE until
            # the read audit commits so a selected candidate cannot be omitted.
            metadata = await self._metadata(artifact_id, lock=True, shared=True)
            await self._verified(metadata)

            def view(session: Session) -> DocumentDateView:
                candidates, selections = (
                    tables.document_date_candidate,
                    tables.document_date_selection,
                )
                rows = (
                    session.execute(
                        select(candidates)
                        .where(*_owned(candidates, metadata))
                        .order_by(candidates.c.created_at, candidates.c.id)
                    )
                    .mappings()
                    .all()
                )
                query = select(selections).where(*_owned(selections, metadata))
                if selection_id:
                    query = query.where(selections.c.id == selection_id)
                selected = (
                    session.execute(query.order_by(selections.c.sequence.desc()).limit(1))
                    .mappings()
                    .one_or_none()
                )
                if selection_id and selected is None:
                    raise DateBasisInvalid("historical selection belongs to another version")
                records = tuple(candidate_record(row) for row in rows)
                selection = selection_record(selected) if selected else None
                date = next(
                    (row.date for row in records if selection and row.id == selection.candidate_id),
                    None,
                )
                return DocumentDateView(
                    document_version_id=metadata.version_id,
                    candidates=records,
                    selection=selection,
                    selected_date=date,
                )

            return await self.session.run_sync(view)

        return await self.execution.read(
            principal,
            ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id),
            "read",
            trace_id=trace_id,
            load=load,
        )
