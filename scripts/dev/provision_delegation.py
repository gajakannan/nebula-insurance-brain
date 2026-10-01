#!/usr/bin/env python3
"""Trusted local provisioning and revocation of a bounded delegation (F0002-S0005).

Operational authority only (OS/database access is the trusted control) — there is
no web endpoint, no implicit role and no implicit renewal. Issuance is refused when
the ceiling exceeds the acting principal's current authority, when the executor is
not an explicitly provisioned agent/service, or when the window is already expired.

    uv run --project engine python scripts/dev/provision_delegation.py issue \\
        --acting <uuid> --executor <uuid> --operator <uuid> --approval-ref <ref> \\
        --tenant <uuid> --workspace <uuid> --knowledge-base <uuid> \\
        --resource-type content_artifact --resource-id <uuid> --action read \\
        --expires-in-minutes 30
    uv run --project engine python scripts/dev/provision_delegation.py revoke \\
        --delegation <uuid> --operator <uuid> --approval-ref <ref> [--expected-revision N]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from brain_domain.authx import ActionCeiling, Delegation, ResourceKey, ResourceType
from brain_domain.tenancy import OwnedScope
from brain_persistence.grants import issue_delegation, revoke_delegation
from brain_persistence.tenancy import RevisionConflict
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.delegation import DelegationRejected
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_DELEGATION_MINUTES = 24 * 60


def _database_url() -> str:
    url = os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+psycopg://brain:brain@localhost:5432/brain"
    )
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue")
    for name in (
        "acting",
        "executor",
        "operator",
        "tenant",
        "workspace",
        "knowledge-base",
        "resource-id",
    ):
        issue.add_argument(f"--{name}", type=UUID, required=True)
    issue.add_argument(
        "--resource-type", choices=[t.value for t in ResourceType], required=True
    )
    issue.add_argument("--action", action="append", required=True)
    issue.add_argument("--approval-ref", required=True)
    issue.add_argument("--expires-in-minutes", type=int, required=True)
    revoke = sub.add_parser("revoke")
    revoke.add_argument("--delegation", type=UUID, required=True)
    revoke.add_argument("--operator", type=UUID, required=True)
    revoke.add_argument("--approval-ref", required=True)
    revoke.add_argument("--expected-revision", type=int)
    args = parser.parse_args()

    now = datetime.now(UTC)
    engine = create_engine(_database_url())
    try:
        with Session(engine) as session, session.begin():
            if args.command == "issue":
                if not 0 < args.expires_in_minutes <= MAX_DELEGATION_MINUTES:
                    parser.error(
                        f"--expires-in-minutes must be 1..{MAX_DELEGATION_MINUTES}"
                    )
                policies = REPO_ROOT / "planning-mds" / "security" / "policies"
                delegation = Delegation(
                    id=uuid4(),
                    acting_principal_id=args.acting,
                    executor_principal_id=args.executor,
                    issued_by=args.operator,
                    issued_at=now,
                    not_before=now,
                    expires_at=now + timedelta(minutes=args.expires_in_minutes),
                    revoked_at=None,
                    revision=1,
                    ceilings=(
                        ActionCeiling(
                            scope=OwnedScope(
                                args.tenant, args.workspace, args.knowledge_base
                            ),
                            resource=ResourceKey(
                                ResourceType(args.resource_type), args.resource_id
                            ),
                            actions=frozenset(args.action),
                        ),
                    ),
                )
                delegation_id = issue_delegation(
                    session,
                    delegation,
                    operator_id=args.operator,
                    approval_ref=args.approval_ref,
                    policy=CasbinAuthorizationAdapter(
                        policies / "model.conf", policies / "policy.csv"
                    ),
                    at=now,
                )
                print(
                    json.dumps(
                        {
                            "status": "issued",
                            "delegation_id": str(delegation_id),
                            "expires_at": delegation.expires_at.isoformat(),
                        }
                    )
                )
            else:
                revoked = revoke_delegation(
                    session,
                    args.delegation,
                    operator_id=args.operator,
                    approval_ref=args.approval_ref,
                    at=now,
                    expected_revision=args.expected_revision,
                )
                print(
                    json.dumps(
                        {
                            "status": "revoked",
                            "delegation_id": str(revoked.id),
                            "revision": revoked.revision,
                        }
                    )
                )
    except (DelegationRejected, RevisionConflict, ValueError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}), file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
