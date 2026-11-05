"""Container-only deployment probe; prints no credentials or source text."""
import json
import os
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import psycopg
from brain_content.config import load_content_writer_config, load_extraction_config

root = Path("/app/brain")
run = root / "planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff"
with urlopen("http://engine-validation:8000/health", timeout=10) as response:
    health = json.load(response)
with psycopg.connect("postgresql://brain:brain@postgres:5432/brain_f0006_runtime") as connection:
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    version = connection.execute("SHOW server_version").fetchone()[0]
    function = connection.execute(
        "SELECT pg_get_functiondef('brain_assertion_v2_integrity'::regproc)"
    ).fetchone()[0]
assert revision == "0011"
assert "e.page IS NOT DISTINCT FROM" in function and "NULLIF(e.bbox::jsonb" in function
assert os.getuid() != 0
writer = load_content_writer_config()
extraction = load_extraction_config()
assert writer.v2_writer_enabled is False and extraction.pipeline == "direct-baseline"
wheel = next((run / "artifacts/runtime/wheels").glob("*.whl"))
schemas = []
with ZipFile(wheel) as archive:
    for name in archive.namelist():
        if name.endswith(".schema.json"):
            assert archive.read(name) == (root / "planning-mds/schemas" / Path(name).name).read_bytes()
            schemas.append(Path(name).name)
assert len(schemas) == 4
result = {
    "uid": os.getuid(), "health": health, "postgres": version, "migration": revision,
    "page_and_bbox_guard_deployed": True,
    "extraction_pipeline": extraction.pipeline, "v2_content_writer": writer.v2_writer_enabled,
    "packaged_schemas_equal_approved_sources": sorted(schemas),
    "scope": "local synthetic development validation; no production deployment or activation",
}
(run / "artifacts/runtime/deployment-verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
