import json
import urllib.request
from pathlib import Path

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=20) as response:
    document = json.load(response)
    result = {"status": response.status, "openapi": document["openapi"],
              "paths": sorted(document["paths"]), "server": "private candidate validation API",
              "authenticated_test_coverage": "consumer-integration-review-final.xml",
              "scan_scope": "Unauthenticated OpenAPI-driven DAST; protected authorization/atomicity proved separately by PostgreSQL integration tests."}
Path(__file__).with_name("http-preflight.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "openapi": result["openapi"], "path_count": len(result["paths"])}))
