import json
import urllib.request
from pathlib import Path

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=20) as response:
    document = json.load(response)
    result = {"status": response.status, "openapi": document["openapi"],
              "paths": sorted(document["paths"]), "server": "private F0009 candidate API",
              "scan_scope": "Unauthenticated OpenAPI-driven DAST; protected authorization, refusal "
              "attribution and lineage reads are proved by the PostgreSQL integration suites."}
Path(__file__).with_name("http-preflight.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "openapi": result["openapi"], "path_count": len(result["paths"])}))
