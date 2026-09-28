#!/usr/bin/env python3
"""Reviewed ownership / identity / restriction reconciliation for F0002 (ADR-0061).

Runs between migration 0005 (expand) and 0006 (constrain). It never infers grants,
never deletes data and never reassigns an owner: every workspace mapping, entity
tenant, membership restriction slice and resource restriction comes from an
explicit, reviewed mapping file. Child ownership is copied down from parents that
the mapping has registered (structural derivation, not inference).

    uv run --project engine python scripts/dev/reconcile_authx.py --mapping m.yaml --dry-run
    uv run --project engine python scripts/dev/reconcile_authx.py --mapping m.yaml --apply \\
        --expected-digest <sha256 printed by --dry-run> --actor-id <uuid> --approval-ref <ref>

`--dry-run` prints counts and orphan/conflict IDs (no content, no tokens) plus the
mapping digest. `--apply` requires that same digest, an operational actor and an
approval reference; it writes one transactional, audited batch and verifies ID and
ownership checksums before/after. Re-applying an already applied digest is a no-op
receipt. `--activate-policy` additionally registers and activates the policy
release computed from the loaded model/policy files.

Mapping (YAML or JSON):

    version: 1
    tenants:
      - id: <uuid>
        workspaces:
          - id: <uuid>
            knowledge_bases: [<uuid>, ...]
    entities:            # fact_slot.entity_id -> owning tenant (+ optional external key)
      - {id: <uuid>, tenant_id: <uuid>, namespace: <str?>, external_key: <str?>}
    memberships:         # complete slice for every existing membership
      - id: <uuid>
        valid_from: <iso8601 with offset>
        expires_at: <iso8601|null>
        selectors: [{kind: broker|account|policy, mode: all|only, ids: [...]}] x3
        classifications: ["..."] | "*"
        source_acl_ids: ["..."] | "*"
    resources:           # security metadata for every protected record
      - {type: content_artifact|review_task|fact_slot, id: <uuid>,
         classifications: [...], source_acl_ids: [...], parent_chain: [{kind, id}],
         dependency_keys: [{type, id}]}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from brain_domain.authx import ResourceKey, ResourceType, ScopedId, Selector
from brain_domain.tenancy import OwnershipConflict
from brain_persistence.grants import activate_policy_release
from brain_persistence.models import (
    AuditEventRow,
    EntityIdentityRow,
    MembershipRow,
)
from brain_persistence.tenancy import (
    provision_knowledge_base,
    provision_resource_access,
    provision_tenant,
    provision_workspace,
    record_operational_event,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from sqlalchemy import TextClause, create_engine, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENT_TYPE = "scope_reconciled"

# Parent-first derivation order for KB-owned children: (child, fk column, parent).
DERIVATIONS = (
    ("document_version", "source_document_id", "source_document"),
    ("content_artifact", "document_version_id", "document_version"),
    ("semantic_interpretation_run", "artifact_id", "content_artifact"),
    ("assertion", "run_id", "semantic_interpretation_run"),
    ("assertion", "original_assertion_id", "assertion"),
    ("assertion_evidence", "assertion_id", "assertion"),
    ("review_batch", None, None),  # from its single-KB review items
    ("review_decision", "review_item_id", "review_item"),
    ("canonical_fact_change", "to_version_id", "canonical_fact_version"),
)
CHECKSUM_TABLES = (
    "principal",
    "membership",
    "source_document",
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "assertion_evidence",
    "review_item",
    "review_batch",
    "review_decision",
    "fact_slot",
    "canonical_fact_version",
    "canonical_fact_change",
    "outbox_event",
    "audit_event",
)
OWNED_TABLES = {
    "source_document",
    "document_version",
    "content_artifact",
    "semantic_interpretation_run",
    "assertion",
    "assertion_evidence",
    "review_item",
    "review_batch",
    "review_decision",
    "fact_slot",
    "canonical_fact_version",
    "canonical_fact_change",
}


_IDENTIFIERS = frozenset(
    {
        *CHECKSUM_TABLES,
        *OWNED_TABLES,
        "membership",
        "content_artifact",
        "review_item",
        "fact_slot",
        *(c for _child, c, _parent in DERIVATIONS if c),
        *(p for _c, _col, p in DERIVATIONS if p),
    }
)


def _sql(statement: str, *identifiers: str) -> TextClause:
    """Build SQL whose *identifiers* come only from this module's constants; every
    operator-supplied value is a bind parameter. Anything else is refused."""
    unknown = [i for i in identifiers if i not in _IDENTIFIERS]
    if unknown:
        raise ValueError(f"refusing unlisted SQL identifier(s): {unknown}")
    return text(
        statement
    )  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text


def _database_url() -> str:
    url = os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+psycopg://brain:brain@localhost:5432/brain"
    )
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


def load_mapping(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    data = yaml.safe_load(raw) if path.suffix in {".yaml", ".yml"} else json.loads(raw)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise SystemExit("mapping must declare version: 1")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return data, hashlib.sha256(canonical.encode()).hexdigest()


def _kb_owners(mapping: dict[str, Any]) -> dict[UUID, tuple[UUID, UUID]]:
    owners: dict[UUID, tuple[UUID, UUID]] = {}
    for tenant in mapping.get("tenants", []):
        for workspace in tenant.get("workspaces", []):
            for kb in workspace.get("knowledge_bases", []):
                kb_id = UUID(str(kb))
                if kb_id in owners:
                    raise SystemExit(f"knowledge base {kb_id} mapped twice")
                owners[kb_id] = (UUID(str(tenant["id"])), UUID(str(workspace["id"])))
    return owners


def _checksums(conn: Connection) -> dict[str, str]:
    """ID (and ownership, where present) digest per table — no content."""
    result: dict[str, str] = {}
    for table in CHECKSUM_TABLES:
        rows = (
            conn.execute(_sql(f"SELECT id::text FROM {table} ORDER BY 1", table))
            .scalars()
            .all()
        )
        result[table] = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    return result


def _ownership_checksums(conn: Connection) -> dict[str, str]:
    """Ownership of rows that already carried it before reconciliation."""
    result: dict[str, str] = {}
    for table in (
        "source_document",
        "review_item",
        "fact_slot",
        "canonical_fact_version",
        "membership",
    ):
        rows = (
            conn.execute(
                _sql(
                    f"SELECT id::text || ':' || tenant_id::text || ':' || knowledge_base_id::text "
                    f"FROM {table} ORDER BY 1",
                    table,
                )
            )
            .scalars()
            .all()
        )
        result[table] = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    return result


def inventory(conn: Connection, mapping: dict[str, Any]) -> dict[str, Any]:
    """Counts, orphan/conflict IDs and proposed changes. Never content or tokens."""
    owners = _kb_owners(mapping)
    mapped_kbs = [str(k) for k in owners]
    report: dict[str, Any] = {
        "counts": {},
        "orphans": {},
        "conflicts": {},
        "proposed": {},
    }

    def ids(sql: str, *identifiers: str, **params: Any) -> list[str]:
        return [
            str(v)
            for v in conn.execute(_sql(sql, *identifiers), params).scalars().all()
        ]

    for table in ("source_document", "review_item", "fact_slot", "membership"):
        report["counts"][table] = conn.execute(
            _sql(f"SELECT count(*) FROM {table}", table)
        ).scalar_one()
        report["orphans"][f"{table}_unmapped_kb"] = ids(
            f"SELECT id FROM {table} WHERE NOT (knowledge_base_id::text = ANY(:kbs))",
            table,
            kbs=mapped_kbs,
        )
        report["conflicts"][f"{table}_tenant_mismatch"] = [
            row
            for row in ids(
                f"SELECT id::text || '|' || tenant_id::text || '|' || knowledge_base_id::text "
                f"FROM {table}",
                table,
            )
            for rid, tenant, kb in [row.split("|")]
            if UUID(kb) in owners and owners[UUID(kb)][0] != UUID(tenant)
        ]
    report["conflicts"]["review_batch_mixed_kb"] = ids(
        """SELECT review_batch_id FROM review_item WHERE review_batch_id IS NOT NULL
           GROUP BY review_batch_id HAVING count(DISTINCT (tenant_id, knowledge_base_id)) > 1"""
    )
    mapped_entities = {str(e["id"]) for e in mapping.get("entities", [])}
    report["orphans"]["fact_slot_entity_unmapped"] = [
        e
        for e in ids("SELECT DISTINCT entity_id FROM fact_slot")
        if e not in mapped_entities
    ]
    mapped_memberships = {str(m["id"]) for m in mapping.get("memberships", [])}
    report["orphans"]["membership_without_slice"] = [
        m
        for m in ids("SELECT id FROM membership WHERE selectors IS NULL")
        if m not in mapped_memberships
    ]
    mapped_resources = {(r["type"], str(r["id"])) for r in mapping.get("resources", [])}
    for resource_type, table in (
        ("content_artifact", "content_artifact"),
        ("review_task", "review_item"),
        ("fact_slot", "fact_slot"),
    ):
        report["orphans"][f"{resource_type}_without_metadata"] = [
            rid
            for rid in ids(
                f"""SELECT t.id FROM {table} t WHERE NOT EXISTS (
                    SELECT 1 FROM resource_access r
                    WHERE r.resource_type = :rt AND r.resource_id = t.id)""",
                table,
                rt=resource_type,
            )
            if (resource_type, rid) not in mapped_resources
        ]
    report["orphans"]["outbox_without_commit_version"] = ids(
        """SELECT o.id FROM outbox_event o WHERE NOT EXISTS (
           SELECT 1 FROM canonical_fact_version v WHERE v.commit_id = o.commit_id)
           AND NOT EXISTS (SELECT 1 FROM canonical_commit c WHERE c.id = o.commit_id)"""
    )
    report["proposed"] = {
        "tenants": len(mapping.get("tenants", [])),
        "knowledge_bases": len(owners),
        "entities": len(mapping.get("entities", [])),
        "membership_slices": len(mapping.get("memberships", [])),
        "resource_metadata": len(mapping.get("resources", [])),
    }
    report["blocking"] = sorted(
        key
        for section in ("orphans", "conflicts")
        for key, value in report[section].items()
        if value
    )
    return report


def _derive_child_ownership(conn: Connection) -> None:
    for child, column, parent in DERIVATIONS:
        if parent is None:
            conn.execute(
                text(
                    """UPDATE review_batch b SET tenant_id = i.tenant_id,
                           knowledge_base_id = i.knowledge_base_id
                       FROM (SELECT DISTINCT review_batch_id, tenant_id, knowledge_base_id
                             FROM review_item WHERE review_batch_id IS NOT NULL) i
                       WHERE i.review_batch_id = b.id AND b.tenant_id IS NULL"""
                )
            )
            continue
        conn.execute(
            _sql(
                f"""UPDATE {child} c SET tenant_id = p.tenant_id,
                        knowledge_base_id = p.knowledge_base_id
                    FROM {parent} p WHERE p.id = c.{column} AND c.tenant_id IS NULL""",
                child,
                parent,
                column,
            )
        )
    # Human-review corrections without a run inherit from their original assertion.
    conn.execute(
        text(
            """UPDATE assertion c SET tenant_id = o.tenant_id, knowledge_base_id = o.knowledge_base_id
               FROM assertion o WHERE o.id = c.original_assertion_id AND c.tenant_id IS NULL"""
        )
    )


def apply(
    conn: Connection,
    mapping: dict[str, Any],
    digest: str,
    actor_id: UUID,
    approval_ref: str,
    activate_policy: bool,
) -> dict[str, Any]:
    at = datetime.now(UTC)
    session = Session(bind=conn)
    already = session.execute(
        select(AuditEventRow.id).where(
            AuditEventRow.event_type == EVENT_TYPE,
            AuditEventRow.payload["input_digest"].as_string() == digest,
        )
    ).first()
    if already is not None:
        return {"status": "no-op", "reason": "digest already applied", "digest": digest}

    report = inventory(conn, mapping)
    if report["blocking"]:
        raise OwnershipConflict(
            "reconciliation blocked: " + ", ".join(report["blocking"])
        )
    before_ids, before_owner = _checksums(conn), _ownership_checksums(conn)

    owners = _kb_owners(mapping)
    for kb_id, (tenant_id, workspace_id) in owners.items():
        provision_tenant(session, tenant_id, actor_id=actor_id, at=at)
        provision_workspace(session, workspace_id, tenant_id, actor_id=actor_id, at=at)
        provision_knowledge_base(
            session, kb_id, workspace_id, tenant_id, actor_id=actor_id, at=at
        )
    for entity in mapping.get("entities", []):
        key = (UUID(str(entity["id"])), UUID(str(entity["tenant_id"])))
        if session.get(EntityIdentityRow, key) is None:
            session.add(
                EntityIdentityRow(
                    id=key[0],
                    tenant_id=key[1],
                    external_namespace=entity.get("namespace"),
                    external_key=entity.get("external_key"),
                    created_at=at,
                    created_by=actor_id,
                )
            )
    session.flush()
    for item in mapping.get("memberships", []):
        row = session.get(MembershipRow, UUID(str(item["id"])))
        if row is None:
            raise OwnershipConflict("mapped membership does not exist")
        selectors = [
            Selector(s["kind"], s["mode"], frozenset(UUID(i) for i in s["ids"]))
            for s in item["selectors"]
        ]
        if sorted(s.kind.value for s in selectors) != ["account", "broker", "policy"]:
            raise OwnershipConflict(
                "membership slice needs exactly one selector per kind"
            )
        row.valid_from = datetime.fromisoformat(item["valid_from"])
        row.expires_at = (
            datetime.fromisoformat(item["expires_at"])
            if item.get("expires_at")
            else None
        )
        row.selectors = [
            s.to_json() for s in sorted(selectors, key=lambda s: s.kind.value)
        ]
        row.classifications = (
            item["classifications"]
            if item["classifications"] == "*"
            else sorted(item["classifications"])
        )
        row.source_acl_ids = (
            item["source_acl_ids"]
            if item["source_acl_ids"] == "*"
            else sorted(item["source_acl_ids"])
        )
    session.flush()
    _derive_child_ownership(conn)
    conn.execute(
        text(
            """INSERT INTO canonical_commit (id, tenant_id, knowledge_base_id, created_at)
               SELECT DISTINCT commit_id, tenant_id, knowledge_base_id, now()
               FROM canonical_fact_version ON CONFLICT (id) DO NOTHING"""
        )
    )
    for resource in mapping.get("resources", []):
        key = ResourceKey(ResourceType(resource["type"]), UUID(str(resource["id"])))
        model_table = {
            "content_artifact": "content_artifact",
            "review_task": "review_item",
            "fact_slot": "fact_slot",
        }[key.type.value]
        owner = conn.execute(
            _sql(
                f"SELECT tenant_id, knowledge_base_id FROM {model_table} WHERE id = :id",
                model_table,
            ),
            {"id": key.id},
        ).first()
        if owner is None:
            raise OwnershipConflict("mapped resource does not exist")
        provision_resource_access(
            session,
            key,
            tenant_id=owner.tenant_id,
            knowledge_base_id=owner.knowledge_base_id,
            classifications=resource["classifications"],
            source_acl_ids=resource.get("source_acl_ids", []),
            parent_chain=[
                ScopedId(p["kind"], UUID(str(p["id"])))
                for p in resource.get("parent_chain", [])
            ],
            dependency_keys=[
                ResourceKey(ResourceType(d["type"]), UUID(str(d["id"])))
                for d in resource.get("dependency_keys", [])
            ],
            actor_id=actor_id,
            at=at,
        )
    if activate_policy:
        policies = REPO_ROOT / "planning-mds" / "security" / "policies"
        release = CasbinAuthorizationAdapter(
            policies / "model.conf", policies / "policy.csv"
        ).release
        activate_policy_release(
            session, release, operator_id=actor_id, approval_ref=approval_ref, at=at
        )

    record_operational_event(
        session,
        event_type=EVENT_TYPE,
        actor_id=actor_id,
        resource_type="reconciliation",
        resource_id=actor_id,
        at=at,
        approval_ref=approval_ref,
        input_digest=digest,
    )
    session.flush()
    after_ids, after_owner = _checksums(conn), _ownership_checksums(conn)
    changed = {
        t
        for t in CHECKSUM_TABLES
        if t != "audit_event" and before_ids[t] != after_ids[t]
    }
    changed_owner = {t for t in before_owner if before_owner[t] != after_owner[t]}
    if changed or changed_owner:
        raise OwnershipConflict(
            f"ID/ownership checksum changed for {sorted(changed | changed_owner)}"
        )
    pending = (
        conn.execute(
            _sql(
                " UNION ALL ".join(
                    f"SELECT count(*) FROM {t} WHERE tenant_id IS NULL"
                    for t in sorted(OWNED_TABLES)
                ),
                *OWNED_TABLES,
            )
        )
        .scalars()
        .all()
    )
    if any(pending):
        raise OwnershipConflict(
            "some KB-owned rows still lack ownership after derivation"
        )
    missing_metadata = conn.execute(
        text(
            """SELECT count(*) FROM (
                 SELECT id FROM content_artifact c WHERE NOT EXISTS (SELECT 1 FROM resource_access r
                   WHERE r.resource_type = 'content_artifact' AND r.resource_id = c.id)
                 UNION ALL SELECT id FROM review_item i WHERE NOT EXISTS (SELECT 1 FROM resource_access r
                   WHERE r.resource_type = 'review_task' AND r.resource_id = i.id)
                 UNION ALL SELECT id FROM fact_slot f WHERE NOT EXISTS (SELECT 1 FROM resource_access r
                   WHERE r.resource_type = 'fact_slot' AND r.resource_id = f.id)) missing"""
        )
    ).scalar_one()
    if missing_metadata:
        raise OwnershipConflict("protected records without security metadata remain")
    return {
        "status": "applied",
        "digest": digest,
        "checksums": after_ids,
        "inventory": report["proposed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--mapping", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-digest")
    parser.add_argument("--actor-id", type=UUID)
    parser.add_argument("--approval-ref")
    parser.add_argument("--activate-policy", action="store_true")
    args = parser.parse_args()

    mapping, digest = load_mapping(args.mapping)
    engine = create_engine(_database_url())
    try:
        if args.dry_run:
            with engine.connect() as conn:
                report = inventory(conn, mapping)
            print(json.dumps({"digest": digest, **report}, indent=2, sort_keys=True))
            return 1 if report["blocking"] else 0
        if args.expected_digest != digest:
            parser.error("--expected-digest must equal the reviewed mapping's digest")
        if args.actor_id is None or not args.approval_ref:
            parser.error("--apply requires --actor-id and --approval-ref")
        try:
            with engine.begin() as conn:
                receipt = apply(
                    conn,
                    mapping,
                    digest,
                    args.actor_id,
                    args.approval_ref,
                    args.activate_policy,
                )
        except OwnershipConflict as exc:
            print(
                json.dumps({"status": "rejected", "reason": str(exc)}), file=sys.stderr
            )
            return 1
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
