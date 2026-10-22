"""On-demand F0004 operator jobs; no parser, model or Graph activation."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Literal
from uuid import UUID

from brain_content.config import load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.validation import ArtifactIntegrityError, ArtifactKey
from brain_content.verified_store import VerifiedBundleStore
from brain_persistence.content_operations import ContentIntegrityOperations
from brain_persistence.models import ContentArtifact, ResourceAccessRow
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationUnavailable
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-dir", type=Path, required=True)
    parser.add_argument("--tenant", type=UUID, required=True)
    parser.add_argument("--knowledge-base", type=UUID, required=True)
    parser.add_argument(
        "--action", choices=("sweep", "backfill", "repair", "reconcile"), default="sweep"
    )
    parser.add_argument("--writers-quiesced", action="store_true")
    parser.add_argument("--all-scopes", action="store_true")
    parser.add_argument("--artifact", type=UUID)
    parser.add_argument("--repair-record", type=UUID)
    args = parser.parse_args()
    if args.action == "repair" and (not args.artifact or not args.repair_record):
        parser.error("repair requires --artifact and --repair-record")
    if args.action == "reconcile" and (not args.all_scopes or not args.writers_quiesced):
        parser.error("global reconciliation requires --all-scopes and --writers-quiesced")
    database = os.environ["BRAIN_WORKER_DATABASE_URL"]
    if not database.startswith("postgresql+psycopg://"):
        parser.error("content operations require a postgresql+psycopg database")
    actor = UUID(os.environ["BRAIN_WORKER_PRINCIPAL_ID"])
    config = load_local_object_store_config()
    if not config.immutable:
        parser.error("content operations require immutable local object storage")
    engine = create_engine(database, pool_pre_ping=True)
    policy = CasbinAuthorizationAdapter(
        args.policy_dir / "model.conf", args.policy_dir / "policy.csv"
    )
    service = ContentIntegrityOperations(
        engine,
        VerifiedBundleStore(LocalFilesystemObjectStore(config)),
        policy,
        actor_id=actor,
        tenant_id=args.tenant,
        knowledge_base_id=args.knowledge_base,
    )
    counts: Counter[str] = Counter()
    failed = False

    def perform(operation: Callable[[], str]) -> None:
        nonlocal failed
        try:
            counts[operation()] += 1
        except AuthorizationDenied:
            counts["AUTHORIZATION_DENIED"] += 1
            failed = True
        except AuthorizationUnavailable:
            counts["AUTHORIZATION_UNAVAILABLE"] += 1
            failed = True
        except OSError:
            counts["CONTENT_UNAVAILABLE"] += 1
            failed = True
        except ArtifactIntegrityError:
            counts["ARTIFACT_INTEGRITY"] += 1
            failed = True
        except (ValueError, SQLAlchemyError):
            counts["CONTENT_OPERATION_FAILED"] += 1
            failed = True

    try:
        if args.action == "reconcile":
            perform(partial(service.reconcile_uniqueness, writers_quiesced=args.writers_quiesced))
        elif args.action == "repair":
            perform(lambda: service.repair(args.artifact, repair_record_id=args.repair_record))
        else:
            # Inventory is scoped by trusted ownership/security metadata. Every
            # effect and byte read still passes the unit's current authorization.
            with Session(engine) as session:
                query = select(ContentArtifact.id).where(
                    ContentArtifact.tenant_id == args.tenant,
                    ContentArtifact.knowledge_base_id == args.knowledge_base,
                )
                scopes = select(ResourceAccessRow.resource_id).where(
                    ResourceAccessRow.resource_type == "content_artifact",
                    ResourceAccessRow.tenant_id == args.tenant,
                    ResourceAccessRow.knowledge_base_id == args.knowledge_base,
                )
                if args.artifact:
                    query = query.where(ContentArtifact.id == args.artifact)
                    scopes = scopes.where(ResourceAccessRow.resource_id == args.artifact)
                artifacts, resources = session.scalars(query).all(), session.scalars(scopes).all()
            for artifact_id in artifacts:
                perform(
                    partial(
                        service.inspect_artifact, artifact_id, backfill=args.action == "backfill"
                    )
                )
            for artifact_id in set(resources) - set(artifacts):
                versions: tuple[Literal[1, 2], ...] = (1, 2)
                for version in versions:
                    key = ArtifactKey(artifact_id, args.tenant, args.knowledge_base, version)
                    perform(partial(service.record_orphan, key))
            if args.artifact and args.artifact not in set(resources) | set(artifacts):
                perform(lambda: service.inspect_artifact(args.artifact))
        print(json.dumps({"action": args.action, "counts": dict(sorted(counts.items()))}))
        return 1 if failed else 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Credentials, source text and physical paths never appear in diagnostics.
        raise SystemExit(f"content_operation_failed:{type(exc).__name__}") from None
