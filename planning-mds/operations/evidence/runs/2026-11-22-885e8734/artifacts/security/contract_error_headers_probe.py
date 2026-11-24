"""G3 Security probe: does the ContractError 500 carry the baseline security headers?"""
import json

from brain_api.app import create_app
from brain_api.errors import SECURITY_HEADERS
from brain_contracts.schema_runtime import ContractError
from fastapi.testclient import TestClient

app = create_app()


@app.get("/__probe_contract_error")
async def _probe() -> None:
    raise ContractError("CONTRACT_MODEL_MISMATCH")


response = TestClient(app, raise_server_exceptions=False).get("/__probe_contract_error")
missing = {k: v for k, v in SECURITY_HEADERS.items() if response.headers.get(k) != v}
body = response.json()
result = {"status_code": response.status_code, "code": body.get("code"), "body_keys": sorted(body),
          "detail": body.get("detail"), "missing_security_headers": sorted(missing),
          "verdict": "pass" if response.status_code == 500 and not missing and body.get("detail") is None else "fail"}
print(json.dumps(result))
raise SystemExit(0 if result["verdict"] == "pass" else 1)
