#!/usr/bin/env python3
"""Revoke one membership row directly in Postgres (F0001-S0006 revocation proof).

Sets `revoked_at = now()` and bumps `grant_revision` on the matching row. There is
no separate revocation API in this feature — membership rows are written straight
by an operator/admin flow that lands later (F0002); this script stands in for that
flow so the propagation-timing proof (`engine/tests/security/test_revocation_propagation.py`)
has something real to measure against. `PrincipalResolver.memberships()` excludes
any row with `revoked_at IS NOT NULL` on every read (no cache), so propagation is
bounded only by transaction visibility, not by `BRAIN_GRANT_CACHE_SECONDS`.

Usage:
    python3 scripts/dev/revoke_membership.py --issuer <issuer> --subject <subject> \\
        --tenant-id <uuid> --knowledge-base-id <uuid> [--database-url <url>]
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg


def revoke(
    *, database_url: str, issuer: str, subject: str, tenant_id: str, knowledge_base_id: str
) -> int:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE membership
            SET revoked_at = now(), grant_revision = grant_revision + 1
            WHERE principal_id = (
                SELECT id FROM principal WHERE issuer = %s AND subject = %s
            )
            AND tenant_id = %s
            AND knowledge_base_id = %s
            AND revoked_at IS NULL
            """,
            (issuer, subject, tenant_id, knowledge_base_id),
        )
        updated = cursor.rowcount
        connection.commit()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--knowledge-base-id", required=True)
    parser.add_argument(
        "--database-url",
        default=os.environ.get(
            "BRAIN_DATABASE_URL", "postgresql://brain:brain@localhost:5432/brain"
        ).replace("postgresql+asyncpg://", "postgresql://"),
    )
    args = parser.parse_args()

    updated = revoke(
        database_url=args.database_url,
        issuer=args.issuer,
        subject=args.subject,
        tenant_id=args.tenant_id,
        knowledge_base_id=args.knowledge_base_id,
    )
    if updated == 0:
        print("No active membership matched — nothing revoked.", file=sys.stderr)
        return 1
    print(f"Revoked {updated} membership row(s) for {args.issuer} / {args.subject}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
