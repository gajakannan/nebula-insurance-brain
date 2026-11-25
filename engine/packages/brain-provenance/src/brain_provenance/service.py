"""Internal provenance reader (F0009 S0001/S0003/S0004, assembly plan Step 4).

Order inside one authorization unit of work:

1. the anchor is authorized and locked (non-disclosing denial);
2. `prepare_reads` runs metadata-only discovery and returns the READ requirement
   of every linked source, review task and fact slot;
3. all of them are authorized and locked before `load`; any denial refuses the
   whole explanation;
4. `load` materializes exactly the planned rows, refusing a changed topology;
5. authority is rechecked after the load, the output is validated against the
   installed F0011 contract, and the facade commits the read audit once.

There is no cache, no parse, no model call and no canonical or learning write.
"""

from __future__ import annotations

from brain_contracts.schema_runtime import ContractBundle, ContractError, ContractRef
from brain_domain.authx import NO_FILTER, Action, AuthorizationDecision, RequestedScope
from brain_domain.principal import Principal
from brain_domain.provenance import (
    LineageUnavailable,
    ProvenanceContractError,
    ProvenanceQuery,
    ProvenanceResult,
)
from brain_security.execution import AuthorizationExecution

from brain_provenance.ports import ProvenancePlan, ProvenanceRepository

RESULT_CONTRACT = ContractRef("provenance-result-v1", "1")
QUERY_CONTRACT = ContractRef("provenance-query-v1", "1")


class ProvenanceReader:
    def __init__(self, repository: ProvenanceRepository, execution: AuthorizationExecution) -> None:
        self._repository = repository
        self._execution = execution

    async def read(
        self,
        principal: Principal,
        query: ProvenanceQuery,
        *,
        trace_id: str,
        requested: RequestedScope = NO_FILTER,
    ) -> ProvenanceResult:
        # Shape only: this authorizes nothing (Step 4.1).
        try:
            ContractBundle.installed().validate(
                QUERY_CONTRACT, query.to_json(), profile="portable-json/v1"
            )
        except ContractError as exc:
            raise ProvenanceContractError("invalid provenance query") from exc
        planned: list[ProvenancePlan] = []

        async def prepare() -> list:
            plan = await self._repository.discover(query)
            if plan.root != query.root or plan.anchor != query.anchor:
                raise LineageUnavailable()
            planned.append(plan)
            # The anchor was decided first; every other requirement is decided here.
            return [key for key in plan.source_keys if key != query.anchor]

        async def load(_decision: AuthorizationDecision) -> ProvenanceResult:
            (plan,) = planned
            result = await self._repository.materialize(plan)
            if (
                result.root != plan.root
                or (result.tenant_id, result.knowledge_base_id)
                != (plan.tenant_id, plan.knowledge_base_id)
                or {r.ref for r in result.records} != set(plan.record_refs)
            ):
                raise LineageUnavailable()
            try:
                ContractBundle.installed().validate(
                    RESULT_CONTRACT, result.to_json(), profile="native-compat/v1"
                )
            except ContractError as exc:
                # No partial graph leaves: an output invariant failure is unavailable.
                raise LineageUnavailable() from exc
            return result

        return await self._execution.read(
            principal,
            query.anchor,
            Action.READ,
            trace_id=trace_id,
            load=load,
            requested=requested,
            prepare_reads=prepare,
        )
