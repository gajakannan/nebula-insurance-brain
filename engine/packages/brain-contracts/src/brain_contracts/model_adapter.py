"""Source validation surrounds generated Pydantic parsing and serialization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .schema_runtime import ContractBundle, ContractError, ContractRef, WireProfile


def model_for(ref: ContractRef) -> type[BaseModel]:
    from .generated import contracts_v1

    name = ref.name.removesuffix(".schema.json")
    try:
        return getattr(contracts_v1, contracts_v1.MODEL_INDEX[(name, ref.pointer)])
    except (KeyError, AttributeError):
        raise ContractError("CONTRACT_MODEL_MISMATCH") from None


def to_wire(ref: ContractRef, model: BaseModel, *, profile: WireProfile) -> Any:
    try:
        wire = model.model_dump(mode="json", by_alias=True, exclude_unset=True)
        ContractBundle.installed().validate(ref, wire, profile=profile)
        return wire
    except Exception:
        raise ContractError("CONTRACT_MODEL_MISMATCH") from None


def parse_model[ModelT: BaseModel](
    ref: ContractRef, raw: bytes | str, model: type[ModelT], *, profile: WireProfile
) -> ModelT:
    bundle = ContractBundle.installed()
    value = bundle.decode(raw, profile=profile)
    bundle.validate(ref, value, profile=profile)
    try:
        parsed = model.model_validate(value)
        wire = to_wire(ref, parsed, profile=profile)
        # WHY: source guards catch lost constraints, while this comparison catches
        # accepted extras/nulls/strings lost by a generator approximation.
        if wire != value:
            raise ContractError("CONTRACT_MODEL_MISMATCH")
        return parsed
    except Exception:
        raise ContractError("CONTRACT_MODEL_MISMATCH") from None
