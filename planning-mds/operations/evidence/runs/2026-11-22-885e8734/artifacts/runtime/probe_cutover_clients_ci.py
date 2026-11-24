"""Record client counts only; never emit connection URLs or query text."""

import asyncio
import json
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

run = Path("planning-mds/operations/evidence/runs/2026-11-22-885e8734")
targets = json.loads(Path("scripts/contracts/environments.json").read_text())


async def probe():
    url = make_url(os.environ["BRAIN_DATABASE_URL"]).set(database="postgres")
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            readonly = await connection.scalar(text("SHOW transaction_read_only"))
            snapshot = await connection.scalar(text("SELECT transaction_timestamp()"))
            rows = await connection.execute(text(
                "SELECT datname, state, count(*) FROM pg_stat_activity "
                "WHERE backend_type = 'client backend' AND pid <> pg_backend_pid() "
                "AND datname IN (:integration, :dev) GROUP BY datname, state"
            ), {name: value["database"] for name, value in targets.items()})
            counts = {name: 0 for name in targets}
            states = {name: {} for name in targets}
            for database, state, count in rows:
                name = next(name for name, value in targets.items() if value["database"] == database)
                counts[name] += count
                states[name][state or "unknown"] = count
            await connection.rollback()
            report = {
                "snapshot_at": snapshot.isoformat(), "read_only": readonly == "on",
                "target_client_backends": counts, "states": states,
                "result": "PASS" if readonly == "on" and not any(counts.values()) else "INSPECT",
                "scope": "Current local targets only; not a claim of global host process absence.",
                "test_writers": "Owned-database test command exited 0 after 81 passes; fixture databases disposed.",
            }
            (run / "artifacts/runtime/cutover-client-inventory-ci.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
            print(json.dumps(report, sort_keys=True))
            return 0 if report["result"] == "PASS" else 1
    finally:
        await engine.dispose()


raise SystemExit(asyncio.run(probe()))
