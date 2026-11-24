"""Read-only F0011 rollout preflight over every canonical_fact_version row.

The assembly plan uses ``fact_versions`` descriptively; the shipped table is
``canonical_fact_version``. No coordinate or recorded-range filter is applied.
Only safe counts and candidate identities are emitted, never data or row IDs.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import pathlib
import re
import subprocess
from collections.abc import Mapping
from datetime import date
from typing import Any

from brain_api.config import Settings
from brain_api.contract_guards import guard_fact_response
from brain_api.schemas.facts import FactVersionOut
from brain_contracts.schema_runtime import ContractBundle, ContractError
from brain_persistence.models import CanonicalFactVersionRow
from brain_persistence.repositories import _fact_version_from_row
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


class SweepExecutionError(ValueError):
    """Fixed operational code only; no driver/row exception text is exposed."""


def candidate_code_digest() -> str:
    digest = hashlib.sha256(pathlib.Path(__file__).read_bytes())
    for obj in (
        _fact_version_from_row,
        FactVersionOut,
        guard_fact_response,
        ContractBundle,
    ):
        source = inspect.getsourcefile(obj)
        if source is None:
            raise SweepExecutionError("CONTRACT_SWEEP_CODE_IDENTITY_UNAVAILABLE")
        digest.update(pathlib.Path(source).read_bytes())
    return digest.hexdigest()


def environment_target(
    environment: str, configuration: pathlib.Path
) -> tuple[str, str]:
    """Bind the operator's name to the DevOps-inventoried existing database.

    The source-controlled map contains only database/host/port labels. Existing
    application configuration supplies credentials; neither URLs nor credentials
    are returned in a report. Missing inventory is an execution error, not empty.
    """
    try:
        entries = json.loads(configuration.read_bytes())
        target = entries[environment]
        if not isinstance(target, dict) or not isinstance(target.get("database"), str):
            raise TypeError
        if set(target) - {"database", "host", "port"} or not target["database"]:
            raise ValueError
        base = make_url(Settings.from_env().database_url)
        if base.get_backend_name() != "postgresql":
            raise ValueError
        updates: dict[str, Any] = {"database": target["database"]}
        if "host" in target:
            if not isinstance(target["host"], str) or not target["host"]:
                raise ValueError
            updates["host"] = target["host"]
        if "port" in target:
            if type(target["port"]) is not int or not 1 <= target["port"] <= 65535:
                raise ValueError
            updates["port"] = target["port"]
        url = base.set(drivername="postgresql+asyncpg", **updates)
        return url.render_as_string(hide_password=False), target["database"]
    except (OSError, KeyError, TypeError, ValueError):
        raise SweepExecutionError("CONTRACT_SWEEP_ENVIRONMENT_UNAVAILABLE") from None


def zero_row_inventory(path: pathlib.Path | None, environment: str) -> bool:
    if path is None:
        return False
    try:
        inventory = json.loads(path.read_bytes())
        if (
            inventory["environment"] != environment
            or type(inventory["rows"]) is not int
            or inventory["rows"] != 0
        ):
            return False
        for role in ("quality_engineer", "devops"):
            signature = inventory[role]
            if (
                not isinstance(signature["reviewer"], str)
                or not signature["reviewer"].strip()
            ):
                return False
            date.fromisoformat(signature["date"])
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


async def sweep_session(
    session: AsyncSession,
    *,
    environment: str,
    expected_database: str,
    bundle_digest: str,
    code_revision: str,
    empty_inventory_verified: bool = False,
) -> tuple[dict[str, Any], int]:
    """Inspect one fresh session and always roll its transaction back.

    A failed row is counted without recording its identity or exception. A
    database/stream failure or incomplete enumeration exits 2. Data/guard mismatch
    exits 1. Only complete zero-failure coverage can exit 0.
    """
    report: dict[str, Any] = {
        "schema_version": 1,
        "environment": environment,
        "code_revision": code_revision,
        "candidate_code_digest": candidate_code_digest(),
        "bundle_digest": bundle_digest,
        "contract_id": "https://nebula.local/schemas/fact-version-read-v1.schema.json",
        "profile": "native-compat/v1",
        "status": "error",
        "read_only": False,
        "rows_expected": 0,
        "selected": 0,
        "checked": 0,
        "mapping_failures": 0,
        "guard_failures": 0,
        "groups": {"legacy": 0, "temporal": 0, "closed_recorded": 0, "remainders": 0},
        "codes": [],
    }
    try:
        # Must be the first command in a fresh transaction. It applies equally
        # when local development credentials happen to hold elevated privileges.
        await session.execute(
            text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        )
        readonly = await session.scalar(text("SHOW transaction_read_only"))
        isolation = await session.scalar(text("SHOW transaction_isolation"))
        database = await session.scalar(text("SELECT current_database()"))
        if (
            readonly != "on"
            or isolation != "repeatable read"
            or database != expected_database
        ):
            raise SweepExecutionError("CONTRACT_SWEEP_SNAPSHOT_INVALID")
        report["read_only"] = True
        report["isolation"] = isolation
        snapshot = await session.scalar(text("SELECT transaction_timestamp()"))
        report["snapshot_at"] = snapshot.isoformat()
        report["rows_expected"] = int(
            await session.scalar(
                select(func.count()).select_from(CanonicalFactVersionRow)
            )
        )
        stream = await session.stream_scalars(
            select(CanonicalFactVersionRow).execution_options(yield_per=256)
        )
        try:
            async for row in stream:
                report["selected"] += 1
                groups = report["groups"]
                groups["legacy" if row.temporal_contract is None else "temporal"] += 1
                groups["closed_recorded"] += row.recorded.upper is not None
                groups["remainders"] += (
                    row.split_of_version_id is not None or row.change_reason == "split"
                )
                try:
                    version = _fact_version_from_row(row)
                    payload = FactVersionOut.from_domain(version).model_dump(
                        mode="json"
                    )
                except Exception:  # noqa: BLE001 - count failures without driver or row text
                    report["mapping_failures"] += 1
                else:
                    try:
                        guard_fact_response(payload)
                    except ContractError:
                        report["guard_failures"] += 1
                report["checked"] += 1
        finally:
            await stream.close()
        if (
            report["selected"] != report["rows_expected"]
            or report["checked"] != report["selected"]
        ):
            raise SweepExecutionError("CONTRACT_SWEEP_ENUMERATION_INCOMPLETE")
        if report["rows_expected"] == 0 and not empty_inventory_verified:
            raise SweepExecutionError("CONTRACT_SWEEP_EMPTY_REQUIRES_INVENTORY")
        if report["mapping_failures"]:
            report["codes"].append("CONTRACT_SWEEP_ROW_MAPPING_INVALID")
        if report["guard_failures"]:
            report["codes"].append("CONTRACT_INSTANCE_INVALID")
        if report["codes"]:
            report["status"] = "fail"
            return report, 1
        report["status"] = "pass"
        report["zero_row_inventory_verified"] = bool(
            report["rows_expected"] == 0 and empty_inventory_verified
        )
        return report, 0
    except SweepExecutionError as exc:
        report["codes"].append(str(exc))
        return report, 2
    except Exception:  # noqa: BLE001 - report only a fixed operational code
        report["codes"].append("CONTRACT_SWEEP_EXECUTION_FAILED")
        return report, 2
    finally:
        await session.rollback()


async def run(args: argparse.Namespace) -> tuple[Mapping[str, Any], int]:
    bundle = ContractBundle.installed()
    url, database = environment_target(args.environment, args.environments_config)
    revision = await asyncio.to_thread(resolve_code_revision, args.code_revision)
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            return await sweep_session(
                session,
                environment=args.environment,
                expected_database=database,
                bundle_digest=bundle.digest,
                code_revision=revision,
                empty_inventory_verified=zero_row_inventory(
                    args.zero_row_inventory, args.environment
                ),
            )
    finally:
        await engine.dispose()


def resolve_code_revision(explicit: str | None) -> str:
    # Operator containers need no Git executable. The host can pass its exact
    # revision while the candidate digest also binds the executed source bytes.
    value = (
        explicit
        or subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    )
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
        raise SweepExecutionError("CONTRACT_SWEEP_CODE_IDENTITY_UNAVAILABLE")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True, choices=("integration", "dev"))
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument(
        "--environments-config",
        type=pathlib.Path,
        default=pathlib.Path(__file__).with_name("environments.json"),
    )
    parser.add_argument("--zero-row-inventory", type=pathlib.Path)
    parser.add_argument(
        "--code-revision", help="Exact full Git revision from the operator host."
    )
    args = parser.parse_args()
    try:
        report, code = asyncio.run(run(args))
    except Exception:  # noqa: BLE001 - no configuration/driver exception text escapes
        report, code = (
            {
                "schema_version": 1,
                "environment": args.environment,
                "status": "error",
                "codes": ["CONTRACT_SWEEP_CONFIGURATION_FAILED"],
            },
            2,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "environment": args.environment,
                "status": report["status"],
                "exit_code": code,
            }
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
