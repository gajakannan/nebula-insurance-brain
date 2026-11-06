"""Authorized assertion writes; no canonical or interpretation-run completion effects."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from brain_contracts.assertions import AdmissionBatch, AdmissionOutcome, AdmittedAssertion
from brain_domain.assertions import EntityReference, ProducerContext
from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.principal import Principal
from brain_security.execution import AuthorizationExecution

from brain_assertions.admission import AssertionAdmissionService
from brain_assertions.ports import NameClaimConflict


class AssertionRepository(Protocol):
    async def lock_context(self, context: ProducerContext) -> None: ...

    async def persist(
        self,
        context: ProducerContext,
        item: AdmittedAssertion,
        *,
        delivery_key: str,
    ) -> AdmittedAssertion: ...

    async def source_keys(self, assertion_id: UUID) -> tuple[ResourceKey, ...]: ...

    async def project(self, assertion_id: UUID) -> dict: ...


class AssertionWriteService:
    def __init__(
        self,
        repository: AssertionRepository,
        admission: AssertionAdmissionService,
        execution: AuthorizationExecution,
    ) -> None:
        self._repository = repository
        self._admission = admission
        self._execution = execution

    async def admit(
        self,
        principal: Principal,
        context: ProducerContext,
        entities: Sequence[EntityReference],
        items: Sequence[bytes],
        *,
        delivery_key: str,
        truncated: bool = False,
        uninterpreted_blocks: Sequence[str] = (),
    ) -> AdmissionBatch:
        if not delivery_key:
            raise ValueError("delivery identity required")
        source = ResourceKey(ResourceType.CONTENT_ARTIFACT, context.artifact_id)

        async def operation(decisions: Sequence[AuthorizationDecision]) -> AdmissionBatch:
            decision = next(
                d for d in decisions if d.resource == source and d.action == Action.INTERPRET
            )
            if decision.scope is None or (
                decision.scope.tenant_id,
                decision.scope.knowledge_base_id,
                decision.actor_principal_id,
            ) != (context.tenant_id, context.knowledge_base_id, context.actor_id):
                raise PermissionError("assertion producer scope mismatch")
            await self._repository.lock_context(context)
            checked = await self._admission.check_items(
                context,
                entities,
                items,
                truncated=truncated,
                uninterpreted_blocks=uninterpreted_blocks,
            )
            retained: list[AdmittedAssertion] = []
            outcomes = list(checked.outcomes)
            for item in checked.accepted:
                try:
                    retained.append(
                        await self._repository.persist(context, item, delivery_key=delivery_key)
                    )
                except NameClaimConflict:
                    metadata = item.metadata
                    outcomes.append(
                        AdmissionOutcome(
                            item_index=metadata.item_index,
                            item_path=f"/assertions/{metadata.item_index}",
                            candidate_id=item.record.id,
                            block_id=item.record.evidence[0].block_id,
                            disposition="REJECTED",
                            reason="NAME_CLAIMED_BY_ANOTHER",
                            raw_item_sha256=metadata.raw_item_sha256,
                            excerpt=items[metadata.item_index].decode("utf-8", errors="replace")[
                                :256
                            ],
                            model_id=context.model_id,
                            prompt_hash=context.prompt_hash,
                        )
                    )
            return AdmissionBatch(
                schema_version=1,
                run_id=context.run_id,
                artifact_id=context.artifact_id,
                accepted=tuple(retained),
                outcomes=tuple(outcomes),
                requires_partial=checked.requires_partial,
            )

        return await self._execution.mutate(
            principal,
            [source],
            Action.INTERPRET,
            trace_id=context.trace_id,
            operation=operation,
        )

    async def read(self, principal: Principal, assertion_id: UUID) -> dict:
        # This discovery loads IDs/owners only, never source text or the projection.
        keys = await self._repository.source_keys(assertion_id)
        if not keys:
            raise LookupError("assertion source unavailable")

        async def load(_decision: AuthorizationDecision) -> dict:
            return await self._repository.project(assertion_id)

        if len(keys) == 1:
            return await self._execution.read(
                principal,
                keys[0],
                Action.READ,
                trace_id="assertion-read",
                load=load,
            )

        async def load_all(_decisions: Sequence[AuthorizationDecision]) -> dict:
            return await self._repository.project(assertion_id)

        return await self._execution.mutate(
            principal,
            keys,
            Action.READ,
            trace_id="assertion-read",
            operation=load_all,
        )
