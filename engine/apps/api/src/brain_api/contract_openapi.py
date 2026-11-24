"""Serve the generated source-owned OpenAPI snapshot from the installed bundle."""

from __future__ import annotations

from typing import Any

from brain_contracts.schema_runtime import ContractBundle
from fastapi import FastAPI


def install_contract_openapi(app: FastAPI) -> None:
    # WHY: bundle corruption must refuse startup, even before a route validates
    # its first response. No schema or API source checkout is consulted here.
    bundle = ContractBundle.installed()
    snapshot = bundle.openapi()

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = dict(snapshot)
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
