#!/usr/bin/env python3
"""Revoke a principal's membership(s) in one tenant/KB (F0001-S0006 proof, F0002-S0003).

F0002: revocation goes through `brain_persistence.grants.revoke_membership`, which
takes the principal's authority row FOR UPDATE, sets `revoked_at`, advances the
monotonic authority revision and records an audited `membership_revoked` event with
the operational actor and approval reference — all in one transaction. Protected
operations hold FOR SHARE on the same row, so the next operation after this commit
always observes it. There is no grant cache.

The F0001 arguments are unchanged; `--operator-id` and `--approval-ref` default to
`BRAIN_OPERATOR_PRINCIPAL_ID` / `BRAIN_APPROVAL_REF` and are required one way or the other.

Usage:
    python3 scripts/dev/revoke_membership.py --issuer <issuer> --subject <subject> \\
        --tenant-id <uuid> --knowledge-base-id <uuid> [--database-url <url>] \\
        [--operator-id <uuid>] [--approval-ref <ref>]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from uuid import UUID

from brain_persistence.grants import revoke_membership
from brain_persistence.models import ExternalIdentityRow, MembershipRow
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def revoke(
    *,
    database_url: str,
    issuer: str,
    subject: str,
    tenant_id: str,
    knowledge_base_id: str,
    operator_id: UUID,
    approval_ref: str,
) -> int:
    engine = create_engine(database_url)
    try:
        with Session(engine) as session, session.begin():
            membership_ids = (
                session.execute(
                    select(MembershipRow.id)
                    .join(
                        ExternalIdentityRow,
                        ExternalIdentityRow.principal_id == MembershipRow.principal_id,
                    )
                    .where(
                        ExternalIdentityRow.issuer == issuer,
                        ExternalIdentityRow.subject == subject,
                        MembershipRow.tenant_id == UUID(tenant_id),
                        MembershipRow.knowledge_base_id == UUID(knowledge_base_id),
                        MembershipRow.revoked_at.is_(None),
                    )
                    .order_by(MembershipRow.id)
                )
                .scalars()
                .all()
            )
            now = datetime.now(UTC)
            for membership_id in membership_ids:
                revoke_membership(
                    session,
                    membership_id,
                    operator_id=operator_id,
                    approval_ref=approval_ref,
                    at=now,
                )
            return len(membership_ids)
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--knowledge-base-id", required=True)
    parser.add_argument(
        "--database-url",
        default=os.environ.get(
            "BRAIN_DATABASE_URL",
            "postgresql+psycopg://brain:brain@localhost:5432/brain",
        ).replace("postgresql+asyncpg://", "postgresql+psycopg://"),
    )
    parser.add_argument(
        "--operator-id",
        type=UUID,
        default=os.environ.get("BRAIN_OPERATOR_PRINCIPAL_ID"),
    )
    parser.add_argument("--approval-ref", default=os.environ.get("BRAIN_APPROVAL_REF"))
    args = parser.parse_args()
    if args.operator_id is None or not args.approval_ref:
        parser.error(
            "an operational actor (--operator-id) and --approval-ref are required"
        )

    updated = revoke(
        database_url=args.database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        if args.database_url.startswith("postgresql://")
        else args.database_url,
        issuer=args.issuer,
        subject=args.subject,
        tenant_id=args.tenant_id,
        knowledge_base_id=args.knowledge_base_id,
        operator_id=UUID(str(args.operator_id)),
        approval_ref=args.approval_ref,
    )
    if updated == 0:
        print("No active membership matched — nothing revoked.", file=sys.stderr)
        return 1
    print(f"Revoked {updated} membership row(s) for {args.issuer} / {args.subject}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
